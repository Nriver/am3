import asyncio
import os
import time

import socketio
import urllib3
from am3.cmdline import get_status_data, get_app_list, get_app_id_by_uuid
from am3.settings import am3_data_path, am3_pids_path
from loguru import logger
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def push_app_list():
    print('主动推送app列表')
    app_list = get_app_list()
    data = {
        'api_token': api_token,
        'app_list': app_list,
    }
    sio.emit('recieve_app_list', {'data': data}, namespace=namespace)


def on_file_modified(event):
    print(f"{event.src_path} 被修改")
    push_app_list()


def on_file_deleted(event):
    print(f"{event.src_path} 被删除")
    push_app_list()


def init_event_handler(watch_patterns, on_modified, on_deleted):
    ignore_patterns = None  # 设置忽略的文件模式
    ignore_directories = True  # 是否忽略文件夹变化
    case_sensitive = True  # 是否对大小写敏感
    event_handler = PatternMatchingEventHandler(watch_patterns, ignore_patterns, ignore_directories, case_sensitive)
    event_handler.on_modified = on_modified
    event_handler.on_deleted = on_deleted
    return event_handler


def init_observer(event_handler, watch_path):
    # 文件监控
    # http://www.coolpython.net/python_senior/third_module/watchdog.html

    # 监控目录
    go_recursively = False  # 是否监控子文件夹
    my_observer = Observer()
    my_observer.schedule(event_handler, watch_path, recursive=go_recursively)
    my_observer.start()


def observer_status_json():
    event_handler = init_event_handler(["status.json", ], on_file_modified, on_file_deleted)
    init_observer(event_handler, am3_data_path)


def observer_pids():
    event_handler = init_event_handler(["*.pid", ], on_file_modified, on_file_deleted)
    init_observer(event_handler, am3_pids_path)


class AmConnect(socketio.ClientNamespace):

    def __init__(self, namespace):
        super(AmConnect, self).__init__(namespace)

    def on_connect(self):
        print('connect()')
        print('connected to server')

    def on_answer(self, data):
        print('answer()')
        print(data)

    def on_require_app_list(self):
        print('服务端要求获取app列表')
        push_app_list()

    def on_start_node_app(self, message):
        print('接收到启动app的命令')
        app_uuid = message['data']['uuid']
        app_id = get_app_id_by_uuid(app_uuid)
        os.system(f'am start {app_id}')

    def on_stop_node_app(self, message):
        print('接收到停止app的命令')
        app_uuid = message['data']['uuid']
        app_id = get_app_id_by_uuid(app_uuid)
        os.system(f'am stop {app_id}')


def keep_run():
    # https://stackoverflow.com/questions/20170251/how-to-run-a-script-forever
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    finally:
        loop.close()


def start_server():
    sio.register_namespace(AmConnect(namespace))
    # 重连间隔
    reconnect_interval = 5
    while True:
        try:
            print('socketio连接')
            sio.connect(server_address, namespaces=namespace, socketio_path=socketio_path,
                        headers={'client_type': 'am3', 'token': api_token})

            # 保持一直运行
            keep_run()

        except Exception as e:
            print(e)
        logger.info(f'等待{reconnect_interval}秒后重连')
        time.sleep(reconnect_interval)


if __name__ == '__main__':
    # 如果连接有问题就用这个参数调试
    # sio = socketio.Client(logger=True, engineio_logger=True)
    sio = socketio.Client(ssl_verify=False)
    # sio = socketio.Client()

    status_data = get_status_data()
    api_status_data = status_data['api']
    api_token = api_status_data['api_token']
    namespace = api_status_data['namespace']
    server_address = api_status_data['server_address']
    socketio_path = api_status_data['socketio_path']

    # 启动文件监控
    observer_status_json()
    observer_pids()

    start_server()
