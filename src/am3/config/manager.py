#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责处理所有配置相关的操作
"""
import os
import json
import fcntl
import getpass
import uuid
import socket
from datetime import datetime

import psutil
import click
from loguru import logger

from am3.utils.path_util import format_path
from am3.utils.linux_util import detect_init_system
from am3.version import __version__


class ConfigManager:
    """配置管理器类，处理所有配置相关操作"""

    def __init__(self):
        """初始化配置管理器"""
        # 基础路径
        self.am3_data_path = format_path('~/.am3')
        self._ensure_directory(self.am3_data_path)

        # 子目录
        self.am3_pids_path = os.path.join(self.am3_data_path, 'pids')
        self._ensure_directory(self.am3_pids_path)

        self.am3_logs_path = os.path.join(self.am3_data_path, 'logs')
        self._ensure_directory(self.am3_logs_path)

        self.am3_init_path = os.path.join(self.am3_data_path, 'init')
        self._ensure_directory(self.am3_init_path)

        # 文件路径
        self.am3_status_path = os.path.join(self.am3_data_path, 'status.json')
        self.am3_log_path = os.path.join(self.am3_data_path, 'am3.log')
        self.am3_dump_path = os.path.join(self.am3_data_path, 'dump.json')
        self.am3_dump_bak_path = os.path.join(self.am3_data_path, 'dump_bak.json')

        # 初始化状态文件
        self._init_status_file()

        # 检查系统启动时间
        self._check_system_boot_time()

    def _ensure_directory(self, directory):
        """确保目录存在"""
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _init_status_file(self):
        """初始化状态文件"""
        if not os.path.exists(self.am3_status_path):
            with open(self.am3_status_path, 'w') as f:
                logger.info('初始化 am3 status 文件')
                f.write(json.dumps({
                    'version': __version__,
                    'apps': {},
                    'system_boot_time': str(datetime.fromtimestamp(psutil.boot_time())),
                    'api': {
                        'api_token': '',
                        'node_name': '',
                        'server_address': '',
                        'namespace': '',
                        'socketio_path': '',
                    }
                }, ensure_ascii=False, indent=4))

    def _check_system_boot_time(self):
        """检查系统启动时间，如果系统重启过，清理PID文件"""
        try:
            with open(self.am3_status_path, 'r') as f:
                content = f.read()
                if not content:
                    return

                am3_status = json.loads(content)
                current_boot_time = str(datetime.fromtimestamp(psutil.boot_time()))

                if am3_status.get('system_boot_time') != current_boot_time:
                    logger.info('系统重启过，进程pid都要设置为失效')
                    # 清理PID目录
                    for file in os.listdir(self.am3_pids_path):
                        os.remove(os.path.join(self.am3_pids_path, file))

                    # 更新启动时间
                    am3_status['system_boot_time'] = current_boot_time
                    with open(self.am3_status_path, 'w') as f2:
                        logger.info('更新系统启动时间')
                        f2.write(json.dumps(am3_status, ensure_ascii=False, indent=4))
        except Exception as e:
            logger.exception(f"检查系统启动时间时出错: {e}")

    def get_status_data(self):
        """获取状态数据"""
        try:
            with open(self.am3_status_path, 'r') as f:
                return json.loads(f.read())
        except Exception as e:
            logger.exception(f"读取状态数据时出错: {e}")
            return {'version': __version__, 'apps': {}, 'system_boot_time': '', 'api': {}}

    def update_status_data(self, status_data):
        """更新状态数据"""
        try:
            with open(self.am3_status_path, 'r+') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.seek(0)
                f.truncate()
                f.write(json.dumps(status_data, ensure_ascii=False, indent=4))
                fcntl.flock(f, fcntl.LOCK_UN)
            return True
        except Exception as e:
            logger.exception(f"更新状态数据时出错: {e}")
            return False

    def get_app_config(self, app_id):
        """获取应用配置"""
        status_data = self.get_status_data()
        app_id = str(app_id)

        if app_id in status_data['apps']:
            return status_data['apps'][app_id]['app_conf']
        return None

    def save_app_config(self, app_config, app_id=None):
        """保存应用配置"""
        status_data = self.get_status_data()

        # 如果没有提供app_id，查找是否已存在相同启动路径的应用
        if app_id is None:
            app_exists = False
            max_id = -1

            for id_str in status_data['apps']:
                max_id = max(max_id, int(id_str))
                if status_data['apps'][id_str]['app_conf']['start'] == app_config['start']:
                    app_exists = True
                    app_id = id_str
                    break

            if not app_exists:
                app_id = str(max_id + 1)
        else:
            app_id = str(app_id)

        # 确保UUID存在
        if 'uuid' not in app_config:
            app_config['uuid'] = str(uuid.uuid4())

        # 更新或创建应用配置
        if app_id in status_data['apps']:
            status_data['apps'][app_id]['app_conf'].update(app_config)
        else:
            status_data['apps'][app_id] = {'app_conf': app_config}

        # 保存状态数据
        return self.update_status_data(status_data), app_id

    def delete_app_config(self, app_id):
        """删除应用配置"""
        status_data = self.get_status_data()
        app_id = str(app_id)

        if app_id in status_data['apps']:
            del status_data['apps'][app_id]
            return self.update_status_data(status_data)
        return False

    def get_all_app_ids(self):
        """获取所有应用ID"""
        status_data = self.get_status_data()
        return list(status_data['apps'].keys())

    def load_app_config_from_file(self, config_file):
        """从配置文件加载应用配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.loads(f.read())
        except Exception as e:
            logger.exception(f"从文件加载配置时出错: {e}")
            return None

    def save_app_config_to_file(self, app_config, output_file):
        """保存应用配置到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(app_config, ensure_ascii=False, indent=4))
            return True
        except Exception as e:
            logger.exception(f"保存配置到文件时出错: {e}")
            return False

    def save_apps_dump(self):
        """保存应用列表到dump文件"""
        from am3.core.app_manager import AppManager

        status_data = self.get_status_data()
        app_manager = AppManager(self)
        app_list = app_manager.get_app_list()

        # 修复旧版本缺少uuid的问题
        for app_id in status_data['apps']:
            if 'uuid' not in status_data['apps'][app_id]['app_conf']:
                status_data['apps'][app_id]['app_conf']['uuid'] = str(uuid.uuid4())

        dump_data = {
            'status_data': status_data,
            'app_list': app_list,
        }

        try:
            with open(self.am3_dump_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(dump_data, ensure_ascii=False, indent=4))
            return True
        except Exception as e:
            logger.exception(f"保存应用列表到dump文件时出错: {e}")
            return False

    def load_apps_dump(self):
        """从dump文件加载应用列表"""
        if not os.path.exists(self.am3_dump_path):
            logger.warning('应用列表dump文件不存在')
            return False

        # 先备份当前状态
        self.save_apps_dump_to_file(self.am3_dump_bak_path)

        try:
            with open(self.am3_dump_path, 'r', encoding='utf-8') as f:
                dump_data = json.loads(f.read())
                status_data = dump_data['status_data']

                # 更新系统启动时间
                status_data['system_boot_time'] = str(datetime.fromtimestamp(psutil.boot_time()))

                # 更新状态数据
                self.update_status_data(status_data)
                return True
        except Exception as e:
            logger.exception(f"从dump文件加载应用列表时出错: {e}")
            return False

    def save_apps_dump_to_file(self, file_path):
        """保存应用列表到指定文件"""
        try:
            with open(self.am3_status_path, 'r') as f:
                status_data = json.loads(f.read())

            from am3.core.app_manager import AppManager
            app_manager = AppManager(self)
            app_list = app_manager.get_app_list()

            dump_data = {
                'status_data': status_data,
                'app_list': app_list,
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(dump_data, ensure_ascii=False, indent=4))
            return True
        except Exception as e:
            logger.exception(f"保存应用列表到指定文件时出错: {e}")
            return False

    def init_api(self):
        """初始化API服务配置"""
        # 获取当前配置
        status_data = self.get_status_data()

        # 交互式设置
        default_node_name = socket.gethostname()
        node_name = click.prompt(f'API节点名称', default=default_node_name)

        api_token = click.prompt('API身份校验token', default=str(uuid.uuid4()))

        server_address = click.prompt('AM控制中心服务地址', default='http://127.0.0.1:8000')

        namespace = click.prompt('AM控制中心服务socketio的namespace', default='/am3_control')

        socketio_path = click.prompt('AM控制中心服务socketio路径', default='/socket.io')

        # 更新配置
        if 'api' not in status_data:
            status_data['api'] = {}

        status_data['api'].update({
            'node_name': node_name,
            'api_token': api_token,
            'server_address': server_address,
            'namespace': namespace,
            'socketio_path': socketio_path,
        })

        # 保存配置
        return self.update_status_data(status_data)

    def setup_startup(self):
        """设置开机自启动"""
        # 获取系统信息
        init_system = detect_init_system()
        user = getpass.getuser()
        service_name = f'am3-{user}'

        # 获取可执行文件路径
        import sys
        am3_executable_path = os.path.abspath(sys.argv[0])

        # 模板变量
        template_vars = {
            'am3_data_path': self.am3_data_path,
            'user': user,
            'am3_executable_path': am3_executable_path,
        }

        # 获取模板目录
        import am3
        import pkg_resources

        def get_template(tpl_name):
            """获取并渲染模板"""
            try:
                # 尝试从包资源中获取模板
                template_path = pkg_resources.resource_filename('am3', f'startup_scripts/{tpl_name}.tpl')
                logger.info(f"尝试从路径加载模板: {template_path}")

                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template = f.read().format(**template_vars)
                        return template
                else:
                    # 如果找不到模板文件，尝试从源代码目录加载
                    package_path = os.path.dirname(os.path.abspath(am3.__file__))
                    template_file = f'{package_path}/startup_scripts/{tpl_name}.tpl'
                    logger.info(f"尝试从源码目录加载模板: {template_file}")

                    if os.path.exists(template_file):
                        with open(template_file, 'r', encoding='utf-8') as f:
                            template = f.read().format(**template_vars)
                            return template
                    else:
                        raise FileNotFoundError(f"找不到模板文件: {tpl_name}.tpl")
            except Exception as e:
                logger.exception(f"加载模板时出错: {e}")
                raise

        # 根据不同的初始化系统处理
        if init_system == 'systemd':
            # systemd系统 (如Ubuntu, Arch等)
            template = get_template('systemd')
            destination = f'/etc/systemd/system/{service_name}.service'
            cmds = [
                f'sudo systemctl enable {service_name}',
                f'sudo systemctl enable {service_name}.service',
            ]
        elif init_system == 'launchd':
            # macOS
            template = get_template('launchd')
            destination = f"{os.path.expanduser('~/Library/LaunchAgents')}/{service_name}.plist"
            cmds = [
                f"mkdir -p {os.path.expanduser('~/Library/LaunchAgents')}",
                f'launchctl load -w {destination}',
            ]
        else:
            logger.error(f'不支持的初始化系统: {init_system}')
            return False

        # 写入启动文件
        try:
            tmp_init_file = os.path.join(self.am3_init_path, 'init.txt')
            with open(tmp_init_file, 'w', encoding='utf-8') as f:
                f.write(template)

            os.system(f'sudo cp {tmp_init_file} {destination}')
            logger.info(f'成功写入启动文件: {destination}')

            # 执行启用命令
            for cmd in cmds:
                os.system(cmd)

            logger.info('成功添加启动项')
            return True
        except Exception as e:
            logger.exception(f"设置开机自启动时出错: {e}")
            return False
