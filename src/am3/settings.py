import json
import os
from datetime import datetime

import psutil
from am3.utils.path_util import format_path
from loguru import logger

am3_data_path = format_path('~/.am3')
if not os.path.exists(am3_data_path):
    os.makedirs(am3_data_path)

# pid 文件夹
am3_pids_path = os.path.join(am3_data_path, 'pids')
if not os.path.exists(am3_pids_path):
    os.makedirs(am3_pids_path)

# # am3.pid 文件
# am3_pids_path = os.path.join(am3_data_path, 'am3.pid')
# if not os.path.exists(am3_pids_path):
#     with open(am3_pids_path, 'w') as f:
#         pass

# logs 文件夹
am3_logs_path = os.path.join(am3_data_path, 'logs')
if not os.path.exists(am3_logs_path):
    os.makedirs(am3_logs_path)

# init 文件夹
am3_init_path = os.path.join(am3_data_path, 'init')
if not os.path.exists(am3_init_path):
    os.makedirs(am3_init_path)

# status.json 文件
am3_status_path = os.path.join(am3_data_path, 'status.json')
# 初始化
if not os.path.exists(am3_status_path):
    with open(am3_status_path, 'w') as f:
        logger.info('写入 am3 status')
        f.write(json.dumps({
            'version': '0.0.1',
            'apps': {},
            'system_boot_time': str(datetime.fromtimestamp(psutil.boot_time())),
            'api': {
                'api_token': '',
                'am_control_center': '',
            }
        }, ensure_ascii=False, indent=4))

# am3 自身的日志路径
am3_log_path = os.path.join(am3_data_path, 'am3.log')

# am3 保存app状态列表的dump路径
am3_dump_path = os.path.join(am3_data_path, 'dump.json')
# 恢复时先备份之前的app状态列表，方便恢复
am3_dump_bak_path = os.path.join(am3_data_path, 'dump_bak.json')
