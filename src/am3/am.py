#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys

from am3 import cmdline
from am3.alias import alias_list, alias_log, alias_startup, alias_load, alias_start, alias_stop, alias_delete, \
    alias_restart, alias_help, alias_api
from am3.settings import am3_log_path


def main():
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    print(sys.argv)
    # print(sys.executable)
    # exit()
    # 这里要解析一下参数

    # 获取模块对应文件路径
    cmdline_file = os.path.abspath(cmdline.__file__)

    if len(sys.argv) == 1:
        print('empty')
        os.system(sys.executable + ' ' + cmdline_file)
        exit()

    if len(sys.argv) == 2 and sys.argv[1] in alias_help:
        os.system(sys.executable + ' ' + cmdline_file + ' -h')
        exit()

    action = sys.argv[1]
    if action in alias_list:
        print('应用列表')
        cmdline.list_apps()
        exit()
    elif action in alias_log:
        print('输出日志')
        am3_status = cmdline.read_am3_status()
        apps = am3_status['apps']
        if len(sys.argv) == 2:
            print('没有传入 app_id 输出am3的日志')
            print(am3_log_path)
            if not os.path.exists(am3_log_path):
                os.system(f'touch {am3_log_path}')
            os.system(f'tail -f {am3_log_path}')
        else:
            app_id = sys.argv[2]
            if app_id in apps:
                log_output_path = apps[app_id]['app_conf']['app_log_path']
                print(log_output_path)
                if not os.path.exists(log_output_path):
                    os.system(f'touch {log_output_path}')
                os.system(f'tail -f {log_output_path}')
            else:
                print('app id 不存在')
        exit()
    elif action in alias_startup:
        print('自启动')
        cmdline.startup(am3_executable_path=os.path.abspath(__file__))
        exit()

    elif action in alias_load:
        app_list = cmdline.load_apps()
        for app in app_list:
            app_id = app['app_id']
            if app['app_is_running']:
                cmd = [sys.executable, cmdline_file, 'start', app_id]
                print(cmd)
                subprocess.Popen(cmd,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.STDOUT
                                 )
        exit()

    elif action in alias_api:
        print('api')
        cmdline.handle_api()
        exit()

    if sys.argv[1] in (alias_start + alias_stop + alias_restart + alias_delete):
        if sys.argv[2] == 'all':
            # 特殊情况 传入的参数是 all 则遍历所有的 app_id
            app_ids = cmdline.get_all_app_ids()
            for app_id in app_ids:
                cmd = [sys.executable, cmdline_file, sys.argv[1], app_id]
                print(cmd)
                subprocess.Popen(cmd,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.STDOUT
                                 )
            exit()

    # 正常的 --start 等参数
    # 特殊命令
    # start 命令
    # restart 命令
    # delete 命令
    # 都通过子进程方式运行
    print('运行命令')
    # switch = 10
    switch = 20
    if switch == 10:
        # sys.exit(cmdline.execute())
        sys.exit(cmdline.main())
    elif switch == 20:
        # print(cmdline_file)
        cmd = [sys.executable, cmdline_file, *sys.argv[1:]]
        # print(cmd)
        subprocess.Popen(cmd,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.STDOUT
                         )
        exit()


if __name__ == '__main__':
    main()
