import time

from loguru import logger

a = 0
while True:
    print(f'内部 print 输出 {a}')
    logger.info(f'内部 logger 输出 {a}')
    a += 1
    time.sleep(1)

    if a % 2 == 0:
        print('内部 print 输出 模拟报错 Exception XXX')
        logger.error('内部 logger 输出 模拟报错 Exception XXX')

    if a % 3 == 0:
        print('内部 print 输出 模拟低速状态 11.11 KB/s')
        logger.error('内部 logger 输出 模拟低速状态 11.11 KB/s')
