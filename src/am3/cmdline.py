import fcntl
import getpass
import importlib
import json
import os.path
import os.path
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime

import psutil
from am3.alias import alias_start, alias_restart, alias_delete, alias_stop, alias_save, alias_load, alias_init
from am3.settings import am3_pids_path, am3_status_path, am3_log_path, am3_logs_path, am3_dump_path, am3_dump_bak_path, \
    am3_data_path, am3_init_path
from am3.utils.cmd_util import parse_args, guess_interpreter
from am3.utils.color_util import bright_cyan, bool_color, green
from am3.utils.linux_util import detect_init_system
from am3.utils.path_util import format_path, format_name
from am3.utils.process_util import kill_process_and_all_child
from loguru import logger
from prettytable import PrettyTable

logger.add(am3_log_path, rotation="10 MB")


def get_system_boot_time():
    return str(datetime.fromtimestamp(psutil.boot_time()))


def init_config():
    # 初始化配置
    with open(am3_status_path, 'r') as f:
        content = f.read()
        if not content:
            return
        am3_status = json.loads(content)
        if am3_status['system_boot_time'] != get_system_boot_time():
            logger.info('系统重启过，进程pid都要设置为失效')
            shutil.rmtree(am3_pids_path)
            os.makedirs(am3_pids_path)

            am3_status['system_boot_time'] = get_system_boot_time()
            # 初始化同时要更新启动时间，避免pid无限被删除
            with open(f'{am3_status_path}', 'w') as f2:
                logger.info('写入 am3 status')
                f2.write(json.dumps(am3_status, ensure_ascii=False, indent=4))


def execute(app_conf={}, param_fix=True):
    logger.info('执行execute()')
    # 参数修正
    if len(sys.argv) > 1 and param_fix:
        if not sys.argv[1].startswith(('-', '--')):
            sys.argv[1] = '--' + sys.argv[1]

    if app_conf:
        logger.info('使用已有配置')
        # 默认配置，兼容旧版本数据更新
        default_conf = {
            'start': '',
            'interpreter': '',
            'restart_control': '',
            'restart_check_delay': 0,
            'restart_keyword': '',
            'restart_keyword_regex': '',
            'working_directory': '',
            'restart_wait_time': 1,
            'before_execute': '',
            'name': '',
            'app_log_path': '',
            'params': '',
            'update_script': '',
        }
        default_conf.update(app_conf)
        app_conf = default_conf.copy()
    else:
        init_config()
        # ap = argparse.ArgumentParser()
        # ap.add_argument('-c', '--conf', required=False, help='json配置文件路径')
        # ap.add_argument('-s', '--start', required=False, help='目标路径', default='')
        # ap.add_argument('-i', '--interpreter', required=False, help='解释器路径', default='')
        # ap.add_argument('-g', '--generate', required=False, help='生成配置json文件, 不启动应用', default='')
        # ap.add_argument('--restart_control', required=False, help='是否控制程序的重启', default=True)
        # ap.add_argument('--restart_check_delay', required=False, help='重启关键字检测延迟', type=int, default=0)
        # ap.add_argument('--restart_keyword', required=False, help='如 出现关键字 则 自动重启, 多个关键字用空格隔开',
        #                 nargs='+', default=[])
        # ap.add_argument('--restart_keyword_regex', required=False,
        #                 help='如 出现正则关键字 则 自动重启 多个关键字用空格隔开', nargs='+',
        #                 default=[])
        # ap.add_argument('-t', '--restart_wait_time', required=False, help='自动重启等待时间(秒)', default=1, type=int)
        # ap.add_argument('-d', '--working_directory', required=False, help='工作目录', default='')
        # ap.add_argument('-b', '--before_execute', required=False, help='运行前环境检查', default='')
        # ap.add_argument('--name', required=False, help='应用名称', default='')
        # ap.add_argument('--app_log_path', required=False, help='日志路径', default='')
        # ap.add_argument('--app_pid_file', required=False, help='pid文件路径', default='')
        # ap.add_argument('--params', required=False, help='命令参数', default='')
        # ap.add_argument('--update_script', required=False, help='更新脚本', default='')
        #
        # args = vars(ap.parse_args())
        args = parse_args(standalone_mode=False)
        logger.info(f'click 解析 {args}')

        conf_path = args['conf']
        if conf_path:
            logger.info('读取配置文件')
            with open(conf_path, 'r', encoding='utf-8') as f:
                conf = json.loads(f.read())
                start = conf.get('start', '')
                interpreter = conf.get('interpreter', '')
                restart_control = conf.get('restart_control', True)
                restart_check_delay = conf.get('restart_check_delay', 0)
                restart_keyword = conf.get('restart_keyword', [])
                restart_keyword_regex = conf.get('restart_keyword_regex', [])
                working_directory = conf.get('working_directory', './')
                restart_wait_time = conf.get('restart_wait_time', 1)
                before_execute = conf.get('before_execute', '')
                name = conf.get('name', '')
                app_log_path = conf.get('app_log_path', '')
                app_pid_file = conf.get('app_pid_file', '')
                params = conf.get('params', '')
                update_script = conf.get('update_script', '')
        else:
            start = args['start']
            interpreter = args['interpreter']
            restart_control = args['restart_control']
            restart_check_delay = args['restart_check_delay']
            restart_keyword = args['restart_keyword']
            restart_keyword_regex = args['restart_keyword_regex']
            working_directory = args['working_directory']
            restart_wait_time = args['restart_wait_time']
            before_execute = args['before_execute']
            name = args['name']
            app_log_path = args['app_log_path']
            app_pid_file = args['app_pid_file']
            params = args['params']
            update_script = args['update_script']

        if not start:
            logger.error(f"缺少必要参数, 请使用 {green('am -h')} 查看参数")
            return

        # 参数处理
        # 格式化路径
        start = format_path(start)
        if before_execute:
            before_execute = format_path(before_execute)
        # 默认参数设置
        interpreter_guess, file_type = guess_interpreter(start)
        if not interpreter:
            interpreter = interpreter_guess
        logger.info(f'解释器 {interpreter}')
        logger.info(f'文件类型 {file_type}')

        if not name:
            name = os.path.basename(start)
            if '.' in name:
                name = name.rsplit('.', 1)[0]

        if not working_directory:
            working_directory = os.getcwd()
        working_directory = format_path(working_directory)
        logger.info(f'working_directory {working_directory}')

        if not app_log_path:
            app_log_path = f'{am3_logs_path}/{format_name(name)}.log'

            # 检查是否有重名的应用，如果有，那么日志文件就要加序号，防止多个应用写到同一个日志里
            # 当然，要排除掉自己
            am3_status = read_am3_status()
            log_list_set = set([am3_status['apps'][x]['app_conf']['app_log_path'] for x in am3_status['apps'] if
                                am3_status['apps'][x]['app_conf']['start'] != start])
            tmp = 0
            while True:
                if app_log_path in log_list_set:
                    tmp += 1
                    app_log_path = f'{am3_logs_path}/{format_name(name)}-{tmp}.log'
                else:
                    break

        app_conf = {
            'start': start,
            'interpreter': interpreter,
            'restart_control': restart_control,
            'restart_check_delay': restart_check_delay,
            'restart_keyword': restart_keyword,
            'restart_keyword_regex': restart_keyword_regex,
            'working_directory': working_directory,
            'restart_wait_time': restart_wait_time,
            'before_execute': before_execute,
            'name': name,
            'app_log_path': app_log_path,
            'params': params,
            'uuid': str(uuid.uuid4()),
            'update_script': update_script,
        }

        logger.info(f'应用配置 {app_conf}')

        generate = args['generate']
        if generate:
            logger.info('生成配置文件')
            with open(generate, 'w', encoding='utf-8') as f:
                f.write(json.dumps(app_conf, ensure_ascii=False, indent=4))
                exit()

        # 记录配置
        with open(f'{am3_status_path}', 'r') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            status_data = json.loads(f.read())

            app_exist = False
            max_id = -1
            app_id = 0
            for x in status_data['apps']:
                max_id = max(max_id, int(x))
                if status_data['apps'][str(x)]['app_conf']['start'] == start:
                    app_exist = True
                    app_id = max_id
                    logger.info(f'已存在app, 更新应用配置数据')
                    status_data['apps'][str(x)]['app_conf'].update(app_conf)

            if not app_exist:
                logger.info('新进程 添加应用配置')
                app_id = max_id + 1
                status_data['apps'][str(app_id)] = {
                    'app_conf': app_conf,
                }

            # 默认值处理
            if not app_pid_file:
                app_pid_file = f'{am3_pids_path}/{format_name(name)}-{app_id}.pid'
            app_conf['app_pid_file'] = app_pid_file
            status_data['apps'][str(app_id)]['app_conf']['app_pid_file'] = app_pid_file

            with open(f'{am3_status_path}', 'w') as f2:
                logger.info('写入 am3 status')
                f2.write(json.dumps(status_data, ensure_ascii=False, indent=4))

    if app_conf['before_execute']:
        logger.info('运行前检查')
        # 根据路径加载脚本
        # https://stackoverflow.com/questions/67631/how-do-i-import-a-module-given-the-full-path
        spec = importlib.util.spec_from_file_location("", app_conf['before_execute'])
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)

        # 执行脚本里的 check函数
        while True:
            time.sleep(1)
            if foo.check():
                logger.info('环境检查 通过')
                break
            else:
                logger.warning('环境检查 未通过')

    auto_restart = True
    while True:
        logger.info('启动进程')
        if auto_restart:
            # 配置日志输出到文件
            log_handler_id = logger.add(app_conf['app_log_path'], rotation="1 MB", retention="10 days", colorize=True)
            auto_restart = watch_application(app_conf)
            logger.remove(log_handler_id)
            if auto_restart:
                if app_conf['app_log_path']:
                    logger.info(f"等待 {app_conf['restart_wait_time']} 秒后自动重启应用")
                    time.sleep(app_conf['restart_wait_time'])
                else:
                    logger.info(f'已禁用自动重启')


def watch_application(app_conf):
    interpreter = app_conf['interpreter']
    start = app_conf['start']
    restart_keyword = app_conf['restart_keyword']
    restart_keyword_regex = app_conf['restart_keyword_regex']
    working_directory = app_conf['working_directory']
    restart_control = app_conf['restart_control']
    restart_check_delay = app_conf['restart_check_delay']
    name = app_conf['name']
    app_pid_file = app_conf['app_pid_file']
    params = app_conf['params']

    # DONE: 解决丢失高亮
    begin_time = datetime.now()
    if interpreter:
        cmd = [interpreter, start, params]
    else:
        cmd = [start, params]
    logger.info(cmd)
    cmd_str = ' '.join(cmd)
    p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         encoding='utf-8', universal_newlines=True, cwd=working_directory)
    logger.info(f'应用 {name} 进程id {p.pid}')

    # 记录pid
    with open(app_pid_file, 'w') as f:
        f.write(str(os.getpid()))

    res = execute_subprocess(p)
    for line in res:
        # 这里的字符串是带ansi颜色的
        print(f'{line}', end="")
        logger.info(line)
        if int((datetime.now() - begin_time).seconds) > restart_check_delay:
            # print(f'am3监控输出 {line}', end="")
            # logger.info(f'am3监控输出 {line}')
            for k in restart_keyword:
                # print(k)
                if k in line:
                    logger.info(f'输出 {line.strip()} 满足 关键字匹配条件 {k} 需要重启: pid {p.pid}')
                    if restart_control:
                        p.kill()
                        logger.info(f'已停止: pid {p.pid}')
                        return True
                    else:
                        logger.info(f'已禁用自动重启，不进行杀进程操作')
            for k in restart_keyword_regex:
                res = re.search(k, line)
                if res:
                    logger.info(f'输出 {line.strip()} 满足 正则匹配条件 {k} 需要重启: pid {p.pid}')
                    if restart_control:
                        p.kill()
                        logger.info(f'已停止: pid {p.pid}')
                        return True
                    else:
                        logger.info(f'已禁用自动重启，不进行杀进程操作')
    return True


def execute_subprocess(p):
    for stdout_line in iter(p.stdout.readline, ""):
        # print(stdout_line, end="")
        yield stdout_line
    p.stdout.close()
    return_code = p.wait()
    logger.info('进程退出了')
    # 这里会拿到进程退出码 异常退出可以在这里记录
    # logger.info(f'return_code {return_code}')
    # if return_code:
    #     raise subprocess.CalledProcessError(return_code, p.pid)


def read_am3_status():
    """读取am3状态信息"""
    with open(am3_status_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if not content:
            logger.info('暂无应用')
        am3_status = json.loads(content)
    return am3_status


def get_app_list():
    """获取应用列表"""
    am3_status = read_am3_status()
    data_list = []
    for app_id in am3_status['apps']:
        app = am3_status['apps'][app_id]
        # 获取进程状态
        app_is_running = check_app_running(app)

        data_list.append({
            'app_id': app_id,
            'app_name': app['app_conf']['name'],
            'app_is_running': app_is_running,
            'uuid': app['app_conf']['uuid'],
        })
    return data_list


def get_app_id_by_uuid(app_uuid):
    am3_status = read_am3_status()
    for app_id in am3_status['apps']:
        app = am3_status['apps'][app_id]['app_conf']
        if app['uuid'] == app_uuid:
            return app_id


def list_apps():
    """输出应用列表"""
    app_list = get_app_list()
    # pprint(app_list)
    t = PrettyTable()

    field_names = ['ID', '名称', '运行中']
    # 设置标题颜色
    for x in range(len(field_names)):
        field_names[x] = bright_cyan(field_names[x])
    t.field_names = field_names

    for x in app_list:
        t.add_row([bright_cyan(x['app_id']), x['app_name'], bool_color(x['app_is_running'])])
    print(t)

    # 检测应用列表是否已保存
    if not os.path.exists(am3_dump_path):
        if app_list:
            print(f"应用列表未保存，请使用{green('am save')}来保存应用列表")
        exit()

    with open(am3_dump_path, 'r', encoding='utf-8') as f:
        dump_data = json.loads(f.read())
        dump_status_data = dump_data['status_data']
        dump_app_list = dump_data['app_list']
    status_data = get_status_data()

    status_data.pop('system_boot_time')
    dump_status_data.pop('system_boot_time')
    # 提示保存结果
    print('应用配置一致', status_data == dump_status_data)
    print('应用状态列表一致', app_list == dump_app_list)
    if (status_data == dump_status_data) and (app_list == dump_app_list):
        pass
    else:
        print(f"应用配置和状态可能有修改, 请使用 {green('am save')} 进行保存")


def stop_app_by_app_id(app_id):
    # 停止应用
    app_id = str(app_id)
    logger.info(f'停止应用 {app_id}')
    am3_status = read_am3_status()
    apps = am3_status['apps']
    result = True
    if app_id in apps:
        app_pid_file = apps[app_id]['app_conf']['app_pid_file']
        try:
            if not os.path.exists(app_pid_file):
                logger.info(f'app_pid_file {app_pid_file} 不存在')
                return True
            with open(app_pid_file) as f:
                app_pid = int(f.read().strip())
                # psutil.Process(app_pid).terminate()
                # FIXED: sh文件启动另一个可执行文件，stop只会关掉sh的进程，而可执行文件进程还在，也就是 am的子进程的子进程没有被杀掉
                kill_process_and_all_child(app_pid)
            # 正常停止后 删除对应pid文件
            os.remove(app_pid_file)

        except Exception as e:
            logger.exception("报错了")
    else:
        logger.info('app id 不存在')
        result = False
    logger.info('停止应用 执行完毕')
    return result


def start_app_by_app_id(app_id):
    logger.info(f'运行 start_app_by_app_id({app_id})')
    app_id = str(app_id)
    # 运行前先检查应用是否已经在运行，防止出现重复运行的问题
    if check_running_by_app_id(app_id):
        stop_app_by_app_id(app_id)
    am3_status = read_am3_status()
    apps = am3_status['apps']
    if app_id in apps:
        execute(apps[str(app_id)]['app_conf'], param_fix=False)
        return True
    else:
        logger.info('app id 不存在')
    return False


def restart_app_by_app_id(app_id):
    app_id = str(app_id)
    logger.info(f'重启应用 {app_id}')
    stop_app_by_app_id(app_id)
    result = start_app_by_app_id(app_id)
    return result


def delete_app_by_app_id(app_id):
    app_id = str(app_id)
    logger.info(f'删除应用 {app_id}')
    result = stop_app_by_app_id(app_id)
    if not result:
        return True
    logger.info(f'删除 status 数据')
    with open(f'{am3_status_path}', 'r') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        status_data = json.loads(f.read())
        # logger.info(status_data['apps'])
        if app_id in status_data['apps']:
            status_data['apps'].pop(app_id)
            with open(f'{am3_status_path}', 'w') as f2:
                logger.info('写入 am3 status')
                f2.write(json.dumps(status_data, ensure_ascii=False, indent=4))
    return True


def get_status_data():
    with open(f'{am3_status_path}', 'r') as f:
        status_data = json.loads(f.read())
    return status_data


def get_all_app_ids():
    status_data = get_status_data()
    app_ids = []
    for x in status_data['apps']:
        app_ids.append(x)
    return app_ids


def save_apps(dump_file=am3_dump_path):
    logger.info('保存应用列表')
    status_data = get_status_data()
    app_list = get_app_list()

    # 修复旧版本缺少uuid的问题, 以后可以删掉
    for x in status_data['apps']:
        if 'uuid' not in status_data['apps'][x]['app_conf']:
            status_data['apps'][x]['app_conf']['uuid'] = str(uuid.uuid4())

    dump_data = {
        'status_data': status_data,
        'app_list': app_list,
    }

    with open(dump_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(dump_data, ensure_ascii=False, indent=4))


def load_apps(dump_file=am3_dump_path):
    logger.info('读取应用列表')
    init_config()

    if not os.path.exists(dump_file):
        logger.warning('应用列表不存在')
        return

    # 先备份
    save_apps(am3_dump_bak_path)
    # 删除所有的应用
    app_ids = get_all_app_ids()
    for app_id in app_ids:
        logger.info(app_id)
        delete_app_by_app_id(app_id)

    # 再加载应用列表
    with open(dump_file, 'r', encoding='utf-8') as f:
        dump_data = json.loads(f.read())
        status_data = dump_data['status_data']
        # 更新boot time
        status_data['system_boot_time'] = str(datetime.fromtimestamp(psutil.boot_time()))
        app_list = dump_data['app_list']

        with open(f'{am3_status_path}', 'w') as f2:
            logger.info('写入 am3 status')
            f2.write(json.dumps(status_data, ensure_ascii=False, indent=4))
    return app_list


def startup(am3_executable_path):
    # 参考 https://github.com/Unitech/pm2/blob/master/lib/API/Startup.js
    logger.info('添加自启动')
    logger.info(f'主程序路径 {am3_executable_path}')
    init_system = detect_init_system()
    user = getpass.getuser()
    service_name = f'am3-{user}'
    logger.info(f'系统启动类型 {init_system}')
    logger.info(f'用户名 {user}')
    cmdline_path = os.path.abspath(__file__)
    package_path = os.path.dirname(cmdline_path)
    logger.info(f'当前cmdline脚本路径 {cmdline_path}')
    logger.info(f'am3模块路径 {package_path}')
    logger.info(f'am3 数据路径 {am3_data_path}')

    # just for template render
    template_vars = {
        'am3_data_path': am3_data_path,
        'user': user,
        'am3_executable_path': am3_executable_path,
    }

    def get_template(tpl_name):
        # 获取模板，渲染参数
        template_file = f'{package_path}/templates/init-scripts/{tpl_name}.tpl'
        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read().format(**template_vars)
            return template

    if init_system == 'systemd':
        # manjaro arch ubuntu 等系统
        template = get_template('systemd')
        destination = f'/etc/systemd/system/{service_name}.service'
        # 以防万一不生效 执行两次
        cmds = [
            f'sudo systemctl enable {service_name}',
            f'sudo systemctl enable {service_name}.service',
        ]

    elif init_system == 'launchd':
        # macos
        template = get_template('launchd')
        destination = f"{os.path.expanduser('~/Library/LaunchAgents')}/{service_name}.plist"
        cmds = [
            f"mkdir -p {os.path.expanduser('~/Library/LaunchAgents')}",
            f'launchctl load -w {destination}',
        ]
    else:
        logger.error('暂不支持')
        return

    logger.info('尝试写入启动文件')
    try:
        tmp_init_file = os.path.join(am3_init_path, 'init.txt')
        with open(tmp_init_file, 'w', encoding='utf-8') as f:
            f.write(template)
        os.system(f'sudo cp {tmp_init_file} {destination}')
        logger.info(f'成功写入 {destination}')

        for cmd in cmds:
            os.system(cmd)
        logger.info(f'成功添加启动项')
    except PermissionError as e:
        logger.error('文件写入失败，可能是权限不够，请尝试执行 `sudo am startup`')
        exit()


def check_app_running(app):
    # 获取进程状态
    app_pid_file = app['app_conf']['app_pid_file']
    if not os.path.exists(app_pid_file):
        app_is_running = False
    else:
        with open(app_pid_file) as f:
            app_pid = int(f.read().strip())
        if psutil.pid_exists(app_pid):
            app_is_running = True
        else:
            app_is_running = False
    return app_is_running


def check_running_by_app_id(app_id):
    app_id = str(app_id)
    am3_status = get_status_data()
    app = am3_status['apps'][app_id]
    return check_app_running(app)


def handle_api():
    # api命令解析
    logger.info('handle_api()')

    if len(sys.argv) == 2:
        logger.info('缺少参数')
        logger.info('可用命令参数 init start stop restart')
        exit()

    cmd = sys.argv[2]
    if cmd in alias_init:
        logger.info('api服务 初始化')
        # 交互式设置初始化参数

        default_node_name = socket.gethostname()
        node_name = input(f'api 节点名称(回车默认计使用算机名称 {default_node_name})\n')
        if not node_name:
            node_name = default_node_name
            # print(node_name)

        api_token = input('api 身份校验 token(默认 自动生成随机uuid)\n')
        if not api_token:
            api_token = str(uuid.uuid4())
            # print(api_token)

        server_address = input('am 控制中心服务地址(默认 http://127.0.0.1:8000)\n')
        if not server_address:
            server_address = 'http://127.0.0.1:8000'
            # print(server_address)

        namespace = input('am 控制中心服务 socketio 的 namespace(默认 /am3_control)\n')
        if not namespace:
            namespace = '/am3_control'
            # print(namespace)

        socketio_path = input('am 控制中心服务 socketio 路径(默认 /socket.io)\n')
        if not socketio_path:
            socketio_path = '/socket.io'
            # print(socketio_path)

        with open(f'{am3_status_path}', 'r') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            status_data = json.loads(f.read())
            # logger.info(status_data['api'])
            if 'api' not in status_data:
                status_data['api'] = {}
            status_data['api'].update({
                'node_name': node_name,
                'api_token': api_token,
                'server_address': server_address,
                'namespace': namespace,
                'socketio_path': socketio_path,
            })
            with open(f'{am3_status_path}', 'w') as f2:
                logger.info('写入 am3 status')
                f2.write(json.dumps(status_data, ensure_ascii=False, indent=4))

    elif cmd in alias_start:
        logger.info('api服务 启动')

    elif cmd in alias_stop:
        logger.info('api服务 停止')

    elif cmd in alias_restart:
        logger.info('api服务 重启')

    logger.info('finished')


def main():
    logger.info('执行main()')

    func_rel = [
        [alias_start, start_app_by_app_id],
        [alias_restart, restart_app_by_app_id],
        [alias_delete, delete_app_by_app_id],
        # [alias_list, list_apps],
        [alias_stop, stop_app_by_app_id],
        [alias_save, save_apps],
        # [alias_load, load_apps],
        # [alias_startup, startup],
    ]

    func_dict = {}
    for keywords, func in func_rel:
        for keyword in keywords:
            func_dict[keyword] = func

    if sys.argv[1] in func_dict.keys():
        # start 命令后面如果是数字 则认为是 app_id 尝试当做int 处理
        # 如果报错，就回落到默认的 --start 参数，认为后面是应用启动路径
        logger.info('特殊命令')

        if sys.argv[1] in (alias_save + alias_load):
            func_dict[sys.argv[1]]()
        else:
            try:
                app_id = int(sys.argv[2])
            except:
                execute()
                exit()
            func_dict[sys.argv[1]](app_id)
        exit()

    logger.info('main() 调用 execute()')
    execute()


if __name__ == '__main__':
    # debug测试
    DEBUG = False
    # DEBUG = True
    if DEBUG:
        # sys.argv = ['/home/nate/.local/bin/am', '-c', 'example/counter_config.json']
        # sys.argv = ['/home/nate/gitRepo/am3/cmdline.py', 'u']

        # os.chdir('/home/nate/soft/frp3/')
        # sys.argv = ['/home/nate/gitRepo/am3/cmdline.py', '-s', './frpc']

        sys.argv = ['/home/nate/gitRepo/am3/cmdline.py', '--start', 'ping', '--params', '127.0.0.1']
        logger.info(sys.argv)
        logger.info(sys.argv[1])

    logger.info(f'cmdline 接收到的参数 {sys.argv}')

    if len(sys.argv) == 1:
        execute()
    else:
        main()
