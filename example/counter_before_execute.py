import time

from loguru import logger


def check(switch=10):
    if switch == 10:
        return check_time()
    elif switch == 20:
        return check_web()
    elif switch == 21:
        return check_web_with_proxy()
    elif switch == 30:
        return check_redis()
    elif switch == 40:
        return complex_check()
    elif switch == 50:
        return check_port()
    elif switch == 60:
        return check_cmd_output()


def check_time():
    from datetime import datetime
    # 检测函数 简单模拟每x秒满足一次条件
    s = datetime.now().second
    if s % 3 == 0:
        logger.info('时间检测 通过')
        return True
    logger.warning('时间检测 未通过')
    return False


def check_web():
    # 检测函数 web服务连通性
    import requests
    res = requests.get('http://127.0.0.1:8080')
    if res.status_code == 200:
        logger.info('Web检测 通过')
        return True
    logger.warning('Web检测 未通过')
    return False


def check_web_with_proxy():
    # 检测函数 使用代理检测web服务连通性
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    # 禁用安全请求警告
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    proxies = {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809"
    }

    url = 'https://www.google.com'

    try:
        res = requests.get(url, proxies=proxies, verify=False)
        logger.info('Web代理检测 通过')
        return True
    except Exception as e:
        logger.warning('Web代理检测 未通过')
        return False


def check_redis():
    # 检测函数 redis连通性
    from redis import Redis
    redis_host = '127.0.0.1'
    r = Redis(redis_host, socket_connect_timeout=1)  # short timeout for the test
    try:
        # redis 的 ping 命令可以检测是否可用
        r.ping()
        logger.info('Redis检测 通过')
        return True
    except:
        logger.warning('Redis检测 未通过')
        return False


def complex_check():
    # 检测函数 复杂条件
    # 其实就是把多个条件一个一个检测
    funcs = [check_time, check_web, check_redis]
    for x in funcs:
        if not x():
            logger.warning('复杂条件检测 未通过')
            return False
    logger.info('复杂条件检测 通过')
    return True


def check_port():
    # 检测函数 tcp端口连通性
    import socket
    ip = '127.0.0.1'
    port = 3306
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        logger.info('端口检测 通过')
        return True
    except:
        logger.warning('端口检测 未通过')
        return False


def check_cmd_output():
    # 检测函数 命令行输出结果检测
    # 比如检测硬盘剩余空间
    import subprocess
    cmd = 'df -h | grep /dev/sda'
    res = subprocess.check_output(cmd, shell=True, encoding='utf-8')
    if res:
        usage = int(res.split()[-2].replace('%', ''))
        if usage <= 95:
            logger.info('磁盘剩余空间检测 通过')
            return True
    logger.info('磁盘剩余空间检测 未通过')
    return False


if __name__ == '__main__':
    while True:
        time.sleep(1)
        logger.info(f'检测结果 {check(60)}')
