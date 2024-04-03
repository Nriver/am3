import os
import shutil

import click


@click.command()
@click.option('-c', '--conf', required=False, help='json配置文件路径')
@click.option('-s', '--start', required=False, help='目标路径', default='')
@click.option('-i', '--interpreter', required=False, help='解释器路径', default='')
@click.option('-g', '--generate', required=False, help='生成配置json文件, 不启动应用', default='')
@click.option('--restart_control', required=False, help='是否控制程序的重启', default=True)
@click.option('--restart_check_delay', required=False, help='重启关键字检测延迟', type=int, default=0)
@click.option('--restart_keyword', required=False, help='如 出现关键字 则 自动重启, 多个关键字用空格隔开',
              multiple=True, default=[])
@click.option('--restart_keyword_regex', required=False,
              help='如 出现正则关键字 则 自动重启 多个关键字用空格隔开', multiple=True, default=[])
@click.option('-t', '--restart_wait_time', required=False, help='自动重启等待时间(秒)', default=1, type=int)
@click.option('-d', '--working_directory', required=False, help='工作目录', default='')
@click.option('-b', '--before_execute', required=False, help='运行前环境检查', default='')
@click.option('--name', required=False, help='应用名称', default='')
@click.option('--app_log_path', required=False, help='日志路径', default='')
@click.option('--app_pid_file', required=False, help='pid文件路径', default='')
@click.option('--params', required=False, help='命令参数', default='')
@click.option('--update_script', required=False, help='更新脚本', default='')
def parse_args(**args):
    """
    解析启动的命令行参数
    注意!!! 调用这个函数必须加上 standalone_mode=False 才能获得返回值
    :param args:
    :return:
    """
    return args


def guess_interpreter(target):
    """根据文件后缀猜测对应的执行工具/编译器"""
    # 获取文件类型
    file_name = os.path.basename(target)
    if '.' not in file_name:
        return '', '可执行文件'
    if file_name.endswith('.sh'):
        return '/bin/bash', 'bash脚本'
    if file_name.endswith('.exe'):
        return '', 'exe程序'
    if file_name.endswith('.py'):
        # 优先使用python3
        if shutil.which('python3'):
            return 'python3', 'Python 程序'
        return 'python', 'Python 程序'


if __name__ == '__main__':
    print(parse_args(standalone_mode=False))
