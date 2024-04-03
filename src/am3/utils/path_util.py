import os
import platform

system = platform.system()


def format_path(file_path):
    """
    格式化路径
    install.py会用到这个函数，所以logger要用try包住
    """
    file_path = os.path.expanduser(file_path)
    # 修正路径斜杠
    if system == 'Windows':
        file_path = file_path.replace('//', '/').replace('/', '\\')
    else:
        file_path = file_path.replace('\\', '/').replace('//', '/')

    if ('\\') in file_path or ('/') in file_path:
        # 使用绝对路径找文件
        file_path = os.path.abspath(file_path)
    else:
        # 使用PATH找文件
        pass
    return file_path


def format_name(file_name):
    return file_name.replace('  ', ' ').replace(' ', '-')


if __name__ == '__main__':
    print(format_path('date'))
    print(format_path('./run.sh'))
