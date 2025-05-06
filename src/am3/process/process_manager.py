#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理模块
负责处理进程的启动、监控和停止
"""
import os
import re
import sys
import time
import subprocess
import importlib.util
from datetime import datetime

import click
import psutil
from loguru import logger

from am3.utils.process_util import kill_process_and_all_child


class ProcessManager:
    """进程管理器类，处理进程的生命周期"""

    def __init__(self, config_manager):
        """初始化进程管理器"""
        self.config_manager = config_manager

    def start_process(self, app_config):
        """启动进程"""
        logger.info(f"启动进程: {app_config['name']}")

        # 检查前置条件
        if self._check_before_execute(app_config):
            # 启动进程
            return self._execute_process(app_config)
        else:
            logger.error(f"启动前检查失败: {app_config['name']}")
            return False

    def stop_process(self, app_config):
        """停止进程"""
        logger.info(f"停止进程: {app_config['name']}")

        app_pid_file = app_config.get('app_pid_file')
        if not app_pid_file or not os.path.exists(app_pid_file):
            logger.info(f"PID文件不存在: {app_pid_file}")
            return True  # 如果PID文件不存在，认为进程已经停止

        try:
            with open(app_pid_file) as f:
                app_pid = int(f.read().strip())

            # 杀死进程及其子进程
            kill_process_and_all_child(app_pid)
            logger.info(f"已停止进程 PID: {app_pid}")

            # 删除PID文件
            os.remove(app_pid_file)
            return True
        except Exception as e:
            logger.exception(f"停止进程时出错: {e}")
            return False

    def _check_before_execute(self, app_config):
        """执行前检查"""
        before_execute = app_config.get('before_execute')
        if not before_execute:
            return True  # 没有前置检查，直接返回成功

        try:
            # 加载检查脚本
            logger.info(f"执行前置检查脚本: {before_execute}")
            spec = importlib.util.spec_from_file_location("", before_execute)
            check_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(check_module)

            # 执行检查函数
            while True:
                time.sleep(1)
                if check_module.check():
                    logger.info("环境检查通过")
                    return True
                else:
                    logger.warning("环境检查未通过，等待重试")
        except Exception as e:
            logger.exception(f"执行前置检查时出错: {e}")
            return False

    def _execute_process(self, app_config):
        """执行进程"""
        # 提取配置
        interpreter = app_config.get('interpreter', '')
        start = app_config.get('start', '')
        params = app_config.get('params', '')
        working_directory = app_config.get('working_directory', '')
        restart_control = app_config.get('restart_control', True)
        restart_check_delay = app_config.get('restart_check_delay', 0)
        restart_keyword = app_config.get('restart_keyword', [])
        restart_keyword_regex = app_config.get('restart_keyword_regex', [])
        restart_wait_time = app_config.get('restart_wait_time', 1)
        app_log_path = app_config.get('app_log_path', '')
        app_pid_file = app_config.get('app_pid_file', '')

        # 构建命令
        if interpreter:
            cmd = [interpreter, start]
        else:
            cmd = [start]

        if params:
            cmd.append(params)

        cmd_str = ' '.join(cmd)
        logger.info(f"执行命令: {cmd_str}")

        # 创建监控进程
        monitor_script = self._create_monitor_script(
            app_config, cmd_str, restart_control, restart_check_delay,
            restart_keyword, restart_keyword_regex, restart_wait_time
        )

        # 启动监控进程
        try:
            # 启动一个后台进程来运行监控脚本
            monitor_process = subprocess.Popen(
                [sys.executable, '-c', monitor_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=working_directory
            )
            logger.info(f"监控进程已启动 PID: {monitor_process.pid}")

            # 记录监控进程的PID
            with open(app_pid_file, 'w') as f:
                f.write(str(monitor_process.pid))

            return True
        except Exception as e:
            logger.exception(f"启动监控进程时出错: {e}")
            return False

    def _create_monitor_script(self, app_config, cmd_str, restart_control,
                              restart_check_delay, restart_keyword,
                              restart_keyword_regex, restart_wait_time):
        """创建监控脚本"""
        # 获取应用配置
        app_log_path = app_config.get('app_log_path', '')
        working_directory = app_config.get('working_directory', '')

        # 创建Python脚本内容
        script = f"""
import os
import re
import sys
import time
import subprocess
from datetime import datetime

# 设置工作目录
os.chdir('{working_directory}')

# 启动目标进程
process = subprocess.Popen(
    '{cmd_str}',
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    encoding='utf-8',
    universal_newlines=True
)

# 记录启动时间
begin_time = datetime.now()

# 打开日志文件
log_file = open('{app_log_path}', 'a')
log_file.write(f"\\n\\n--- 进程启动于 {{datetime.now()}} ---\\n")
log_file.flush()

# 监控进程输出
restart_needed = False
try:
    for line in iter(process.stdout.readline, ""):
        # 写入日志
        log_file.write(line)
        log_file.flush()

        # 检查是否需要重启
        if {restart_control} and int((datetime.now() - begin_time).seconds) > {restart_check_delay}:
            # 检查关键字
            restart_keywords = {restart_keyword}
            for keyword in restart_keywords:
                if keyword in line:
                    log_file.write(f"输出匹配关键字 '{{keyword}}'，需要重启\\n")
                    log_file.flush()
                    process.kill()
                    restart_needed = True
                    break

            # 检查正则表达式
            if not restart_needed:
                restart_regex = {restart_keyword_regex}
                for pattern in restart_regex:
                    if re.search(pattern, line):
                        log_file.write(f"输出匹配正则 '{{pattern}}'，需要重启\\n")
                        log_file.flush()
                        process.kill()
                        restart_needed = True
                        break

            if restart_needed:
                break
except Exception as e:
    log_file.write(f"监控进程出错: {{e}}\\n")
    log_file.flush()

# 关闭文件句柄
process.stdout.close()
return_code = process.wait()
log_file.write(f"进程退出，返回码: {{return_code}}\\n")

# 如果需要重启
if restart_needed and {restart_control}:
    log_file.write(f"等待 {restart_wait_time} 秒后自动重启应用\\n")
    log_file.flush()
    time.sleep({restart_wait_time})

    # 重新启动进程
    os.execv(sys.executable, [sys.executable, '-c', __file__])

log_file.close()
"""
        return script


