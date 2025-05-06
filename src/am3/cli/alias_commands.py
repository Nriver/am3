#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
别名命令处理模块
为命令行界面提供别名支持
"""
import sys
import click
from functools import update_wrapper

from am3.alias import alias_dict, get_aliases


def create_alias_command(command_name, aliases):
    """
    创建一个别名命令
    
    Args:
        command_name: 原始命令名称
        aliases: 别名列表
    
    Returns:
        装饰器函数
    """
    def decorator(f):
        # 创建一个新的命令，但不添加到命令组
        cmd = click.Command(
            name=command_name,
            callback=f,
            params=f.params,
            help=f.help,
            epilog=f.epilog,
            short_help=f.short_help,
            add_help_option=f.add_help_option,
            hidden=f.hidden,
        )
        
        # 保存原始命令
        cmd.original_callback = f
        
        # 返回命令
        return cmd
    
    return decorator


def process_args():
    """
    处理命令行参数，将别名转换为原始命令
    
    Returns:
        处理后的参数列表
    """
    args = sys.argv[1:]
    if not args:
        return args
    
    # 检查第一个参数是否是别名
    first_arg = args[0]
    
    # 遍历所有命令的别名
    for cmd, aliases in alias_dict.items():
        if first_arg in aliases:
            # 替换为原始命令
            args[0] = cmd
            break
    
    return args


def setup_aliases(cli_group):
    """
    设置命令别名
    
    Args:
        cli_group: Click 命令组
    """
    # 获取所有命令
    commands = cli_group.commands
    
    # 为每个命令添加别名
    for cmd_name, cmd in list(commands.items()):
        if cmd_name in alias_dict:
            aliases = alias_dict[cmd_name]
            for alias in aliases:
                if alias != cmd_name:  # 避免添加与原始命令相同的别名
                    # 创建别名命令
                    alias_cmd = click.Command(
                        name=alias,
                        callback=cmd.callback,
                        params=cmd.params,
                        help=cmd.help,
                        epilog=cmd.epilog,
                        short_help=f"Alias for '{cmd_name}'",
                        add_help_option=cmd.add_help_option,
                        hidden=True,  # 隐藏别名，不在帮助中显示
                    )
                    # 添加到命令组
                    cli_group.add_command(alias_cmd, alias)
    
    # 处理 API 子命令组
    if 'api' in commands and hasattr(commands['api'], 'commands'):
        api_commands = commands['api'].commands
        for cmd_name, cmd in list(api_commands.items()):
            if cmd_name in alias_dict:
                aliases = alias_dict[cmd_name]
                for alias in aliases:
                    if alias != cmd_name:
                        # 创建别名命令
                        alias_cmd = click.Command(
                            name=alias,
                            callback=cmd.callback,
                            params=cmd.params,
                            help=cmd.help,
                            epilog=cmd.epilog,
                            short_help=f"Alias for 'api {cmd_name}'",
                            add_help_option=cmd.add_help_option,
                            hidden=True,
                        )
                        # 添加到 API 命令组
                        commands['api'].add_command(alias_cmd, alias)
