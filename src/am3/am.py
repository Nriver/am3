#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AM3 - 应用管理工具
主入口文件
"""
import os
import re
import sys
from loguru import logger

from am3.cli.commands import cli
from am3.cli.alias_commands import process_args
from am3.config.manager import ConfigManager


def main():
    """主函数入口"""
    # 清理命令行参数
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    # 处理别名
    new_args = process_args()
    if new_args:
        sys.argv[1:] = new_args

    # 初始化配置
    config_manager = ConfigManager()

    # 设置日志
    logger.add(config_manager.am3_log_path, rotation="10 MB")

    # 执行命令行接口
    cli(obj={})


if __name__ == '__main__':
    main()
