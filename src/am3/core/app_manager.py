#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用管理模块
负责管理应用的生命周期
"""
import os
import sys
import json
import subprocess
from datetime import datetime

import click
import psutil
from loguru import logger
from prettytable import PrettyTable

from am3.utils.color_util import bright_cyan, bool_color, green
from am3.utils.path_util import format_path, format_name
from am3.process.process_manager import ProcessManager


class AppManager:
    """应用管理器类，处理应用的生命周期管理"""

    def __init__(self, config_manager):
        """初始化应用管理器"""
        self.config_manager = config_manager
        self.process_manager = ProcessManager(config_manager)

    def get_app_list(self):
        """获取应用列表"""
        status_data = self.config_manager.get_status_data()
        app_list = []

        for app_id in status_data['apps']:
            app = status_data['apps'][app_id]
            # 检查应用是否在运行
            app_is_running = self.check_app_running(app)

            app_list.append({
                'app_id': app_id,
                'app_name': app['app_conf']['name'],
                'app_is_running': app_is_running,
                'uuid': app['app_conf']['uuid'],
            })

        return app_list

    def list_apps(self, show_details=False):
        """列出所有应用"""
        app_list = self.get_app_list()

        if not app_list:
            click.echo("没有注册的应用")
            return

        # 创建表格
        table = PrettyTable()

        # 设置表头
        field_names = ['ID', '名称', '运行中']
        if show_details:
            field_names.extend(['启动路径', '工作目录', 'PID文件'])

        # 设置标题颜色
        colored_field_names = [bright_cyan(name) for name in field_names]
        table.field_names = colored_field_names

        # 添加数据行
        status_data = self.config_manager.get_status_data()
        for app in app_list:
            app_id = app['app_id']
            row = [
                bright_cyan(app_id),
                app['app_name'],
                bool_color(app['app_is_running'])
            ]

            if show_details:
                app_conf = status_data['apps'][app_id]['app_conf']
                row.extend([
                    app_conf['start'],
                    app_conf['working_directory'],
                    app_conf['app_pid_file']
                ])

            table.add_row(row)

        # 输出表格
        click.echo(table)

        # 检查应用列表是否已保存
        if not os.path.exists(self.config_manager.am3_dump_path):
            if app_list:
                click.echo(f"应用列表未保存，请使用 {green('am save')} 来保存应用列表")
            return

        # 检查配置一致性
        try:
            with open(self.config_manager.am3_dump_path, 'r', encoding='utf-8') as f:
                dump_data = json.loads(f.read())
                dump_status_data = dump_data['status_data']
                dump_app_list = dump_data['app_list']

            status_data = self.config_manager.get_status_data()

            # 移除启动时间再比较
            status_data_copy = status_data.copy()
            dump_status_data_copy = dump_status_data.copy()

            if 'system_boot_time' in status_data_copy:
                status_data_copy.pop('system_boot_time')
            if 'system_boot_time' in dump_status_data_copy:
                dump_status_data_copy.pop('system_boot_time')

            configs_match = status_data_copy == dump_status_data_copy
            lists_match = app_list == dump_app_list

            click.echo(f"应用配置一致: {configs_match}")
            click.echo(f"应用状态列表一致: {lists_match}")

            if not (configs_match and lists_match):
                click.echo(f"应用配置和状态可能有修改, 请使用 {green('am save')} 进行保存")
        except Exception as e:
            logger.exception(f"检查配置一致性时出错: {e}")

    def check_app_running(self, app):
        """检查应用是否在运行"""
        app_pid_file = app['app_conf']['app_pid_file']

        if not os.path.exists(app_pid_file):
            return False

        try:
            with open(app_pid_file) as f:
                app_pid = int(f.read().strip())

            return psutil.pid_exists(app_pid)
        except Exception as e:
            logger.exception(f"检查应用运行状态时出错: {e}")
            return False

    def start_app_by_id(self, app_id):
        """通过ID启动应用"""
        app_id = str(app_id)
        logger.info(f"启动应用 ID: {app_id}")

        # 检查应用是否已在运行
        status_data = self.config_manager.get_status_data()
        if app_id not in status_data['apps']:
            click.echo(f"错误: 应用ID {app_id} 不存在")
            return False

        app = status_data['apps'][app_id]
        if self.check_app_running(app):
            click.echo(f"应用 {app['app_conf']['name']} 已在运行中，先停止它")
            self.stop_app_by_id(app_id)

        # 启动应用
        return self.process_manager.start_process(app['app_conf'])

    def start_app(self, app_config):
        """启动新应用"""
        # 处理应用配置
        if not app_config.get('start'):
            click.echo("错误: 必须提供启动路径")
            return False

        # 格式化路径
        app_config['start'] = format_path(app_config['start'])

        # 设置工作目录
        if not app_config.get('working_directory'):
            app_config['working_directory'] = os.getcwd()
        app_config['working_directory'] = format_path(app_config['working_directory'])

        # 猜测解释器
        if not app_config.get('interpreter'):
            from am3.utils.cmd_util import guess_interpreter
            interpreter, file_type = guess_interpreter(app_config['start'])
            app_config['interpreter'] = interpreter
            logger.info(f"猜测解释器: {interpreter}, 文件类型: {file_type}")

        # 设置应用名称
        if not app_config.get('name'):
            name = os.path.basename(app_config['start'])
            if '.' in name:
                name = name.rsplit('.', 1)[0]
            app_config['name'] = name

        # 设置日志路径
        if not app_config.get('app_log_path'):
            app_log_path = f"{self.config_manager.am3_logs_path}/{format_name(app_config['name'])}.log"

            # 检查是否有重名的应用日志
            status_data = self.config_manager.get_status_data()
            log_paths = set()

            for app_id in status_data['apps']:
                other_app = status_data['apps'][app_id]['app_conf']
                if other_app['start'] != app_config['start']:
                    log_paths.add(other_app.get('app_log_path', ''))

            # 如果日志路径冲突，添加序号
            counter = 0
            while app_log_path in log_paths:
                counter += 1
                app_log_path = f"{self.config_manager.am3_logs_path}/{format_name(app_config['name'])}-{counter}.log"

            app_config['app_log_path'] = app_log_path

        # 添加UUID
        if not app_config.get('uuid'):
            import uuid
            app_config['uuid'] = str(uuid.uuid4())

        # 保存应用配置
        success, app_id = self.config_manager.save_app_config(app_config)

        if not success:
            click.echo("保存应用配置失败")
            return False

        # 启动应用
        return self.process_manager.start_process(app_config)

    def generate_app_config(self, app_config, output_file):
        """生成应用配置文件

        Args:
            app_config: 应用配置字典
            output_file: 输出文件路径

        Returns:
            bool: 是否成功生成配置文件
        """
        logger.info(f"生成配置文件: {output_file}")

        # 确保必要的字段存在
        if not app_config.get('start'):
            click.echo("错误: 必须提供启动路径")
            return False

        # 格式化路径
        app_config['start'] = format_path(app_config['start'])

        # 设置工作目录
        if not app_config.get('working_directory'):
            app_config['working_directory'] = os.getcwd()
        app_config['working_directory'] = format_path(app_config['working_directory'])

        # 猜测解释器
        if not app_config.get('interpreter'):
            from am3.utils.cmd_util import guess_interpreter
            interpreter, file_type = guess_interpreter(app_config['start'])
            app_config['interpreter'] = interpreter
            logger.info(f"猜测解释器: {interpreter}, 文件类型: {file_type}")

        # 设置应用名称
        if not app_config.get('name'):
            name = os.path.basename(app_config['start'])
            if '.' in name:
                name = name.rsplit('.', 1)[0]
            app_config['name'] = name

        # 添加UUID
        if not app_config.get('uuid'):
            import uuid
            app_config['uuid'] = str(uuid.uuid4())

        # 保存配置文件
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(app_config, ensure_ascii=False, indent=4))
            click.echo(f"配置文件已生成: {output_file}")
            return True
        except Exception as e:
            logger.exception(f"生成配置文件时出错: {e}")
            click.echo(f"生成配置文件失败: {e}")
            return False

    def start_app_from_config(self, config_file):
        """从配置文件启动应用"""
        app_config = self.config_manager.load_app_config_from_file(config_file)

        if not app_config:
            click.echo(f"错误: 无法加载配置文件 {config_file}")
            return False

        return self.start_app(app_config)

    def stop_app_by_id(self, app_id):
        """停止应用"""
        app_id = str(app_id)
        logger.info(f"停止应用 ID: {app_id}")

        status_data = self.config_manager.get_status_data()
        if app_id not in status_data['apps']:
            click.echo(f"错误: 应用ID {app_id} 不存在")
            return False

        app = status_data['apps'][app_id]
        return self.process_manager.stop_process(app['app_conf'])

    def restart_app_by_id(self, app_id):
        """重启应用"""
        app_id = str(app_id)
        logger.info(f"重启应用 ID: {app_id}")

        # 先停止再启动
        if self.stop_app_by_id(app_id):
            return self.start_app_by_id(app_id)
        return False

    def delete_app_by_id(self, app_id):
        """删除应用"""
        app_id = str(app_id)
        logger.info(f"删除应用 ID: {app_id}")

        # 先停止应用
        self.stop_app_by_id(app_id)

        # 删除配置
        if self.config_manager.delete_app_config(app_id):
            click.echo(f"应用 ID: {app_id} 已删除")
            return True
        else:
            click.echo(f"删除应用 ID: {app_id} 失败")
            return False

    def start_all_apps(self):
        """启动所有应用"""
        app_ids = self.config_manager.get_all_app_ids()

        if not app_ids:
            click.echo("没有注册的应用")
            return

        success_count = 0
        for app_id in app_ids:
            if self.start_app_by_id(app_id):
                success_count += 1

        click.echo(f"已启动 {success_count}/{len(app_ids)} 个应用")

    def stop_all_apps(self):
        """停止所有应用"""
        app_ids = self.config_manager.get_all_app_ids()

        if not app_ids:
            click.echo("没有注册的应用")
            return

        success_count = 0
        for app_id in app_ids:
            if self.stop_app_by_id(app_id):
                success_count += 1

        click.echo(f"已停止 {success_count}/{len(app_ids)} 个应用")

    def restart_all_apps(self):
        """重启所有应用"""
        app_ids = self.config_manager.get_all_app_ids()

        if not app_ids:
            click.echo("没有注册的应用")
            return

        success_count = 0
        for app_id in app_ids:
            if self.restart_app_by_id(app_id):
                success_count += 1

        click.echo(f"已重启 {success_count}/{len(app_ids)} 个应用")

    def delete_all_apps(self):
        """删除所有应用"""
        app_ids = self.config_manager.get_all_app_ids()

        if not app_ids:
            click.echo("没有注册的应用")
            return

        success_count = 0
        for app_id in app_ids:
            if self.delete_app_by_id(app_id):
                success_count += 1

        click.echo(f"已删除 {success_count}/{len(app_ids)} 个应用")

    def save_apps(self):
        """保存应用列表"""
        if self.config_manager.save_apps_dump():
            click.echo("应用列表已保存")
            return True
        else:
            click.echo("保存应用列表失败")
            return False

    def load_apps(self):
        """加载应用列表"""
        if self.config_manager.load_apps_dump():
            click.echo("应用列表已加载")
            return True
        else:
            click.echo("加载应用列表失败")
            return False

    def view_app_log(self, app_id, follow=False, lines=10):
        """查看应用日志"""
        app_id = str(app_id)
        app_config = self.config_manager.get_app_config(app_id)

        if not app_config:
            click.echo(f"错误: 应用ID {app_id} 不存在")
            return False

        log_path = app_config.get('app_log_path')
        if not log_path or not os.path.exists(log_path):
            click.echo(f"错误: 日志文件 {log_path} 不存在")
            return False

        # 查看日志
        if follow:
            cmd = f"tail -f {log_path}"
        else:
            cmd = f"tail -n {lines} {log_path}"

        os.system(cmd)
        return True

    def view_am3_log(self, follow=False, lines=10):
        """查看AM3自身的日志"""
        log_path = self.config_manager.am3_log_path

        if not os.path.exists(log_path):
            with open(log_path, 'w') as f:
                pass
            click.echo(f"创建日志文件: {log_path}")

        # 查看日志
        if follow:
            cmd = f"tail -f {log_path}"
        else:
            cmd = f"tail -n {lines} {log_path}"

        os.system(cmd)
        return True

    def start_api_service(self):
        """启动API服务"""
        # 这里需要实现API服务启动逻辑
        # 使用原始的api.py文件
        try:
            import am3
            package_path = os.path.dirname(os.path.abspath(am3.__file__))
            api_script_path = os.path.join(package_path, 'api.py')

            # 启动API服务进程
            cmd = [sys.executable, api_script_path]
            api_log_path = os.path.join(self.config_manager.am3_logs_path, 'api.log')

            with open(api_log_path, 'a') as log_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=os.path.dirname(api_script_path)
                )

            # 记录API服务PID
            api_pid_file = os.path.join(self.config_manager.am3_pids_path, 'api.pid')
            with open(api_pid_file, 'w') as f:
                f.write(str(process.pid))

            click.echo(f"API服务已启动，PID: {process.pid}")
            click.echo(f"API服务日志: {api_log_path}")
            return True
        except Exception as e:
            logger.exception(f"启动API服务时出错: {e}")
            click.echo(f"启动API服务失败: {e}")
            return False

    def stop_api_service(self):
        """停止API服务"""
        # 这里需要实现API服务停止逻辑
        try:
            # 检查API服务是否在运行
            api_pid_file = os.path.join(self.config_manager.am3_pids_path, 'api.pid')
            if not os.path.exists(api_pid_file):
                click.echo("API服务未运行")
                return True

            # 读取PID
            with open(api_pid_file, 'r') as f:
                api_pid = int(f.read().strip())

            # 检查进程是否存在
            if not psutil.pid_exists(api_pid):
                click.echo("API服务未运行")
                os.remove(api_pid_file)
                return True

            # 停止进程
            from am3.utils.process_util import kill_process_and_all_child
            kill_process_and_all_child(api_pid)

            # 删除PID文件
            os.remove(api_pid_file)

            click.echo("API服务已停止")
            return True
        except Exception as e:
            logger.exception(f"停止API服务时出错: {e}")
            click.echo(f"停止API服务失败: {e}")
            return False
