import psutil
from loguru import logger


def kill_process_and_all_child(parent_pid):
    parent_pid = int(parent_pid)
    # 杀掉进程以及所有子进程
    child_pids = []
    # 检查进程是否存在
    if psutil.pid_exists(parent_pid):
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            child_pids.append(int(child.pid))
        all_pids = [parent_pid, ] + child_pids
        logger.info(f'杀死pid {all_pids}')
        for pid in all_pids:
            try:
                logger.info(f'进程 {pid} 存在 {psutil.pid_exists(pid)}')
                psutil.Process(pid).terminate()
            except Exception as e:
                logger.info(f'报错 {e}')
    else:
        logger.info(f'父级进程 {parent_pid} 不存在')
