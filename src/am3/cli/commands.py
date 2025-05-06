#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行命令定义模块
使用 Click 库实现命令行界面
"""
import os
import sys
import click
from loguru import logger

from am3.config.manager import ConfigManager
from am3.core.app_manager import AppManager
from am3.process.process_manager import ProcessManager
from am3.cli.alias_commands import setup_aliases
from am3.version import __version__


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """AM3 - 应用管理工具

    用于管理和监控应用程序的运行。
    """
    # 确保 context 对象存在
    ctx.ensure_object(dict)
    # 初始化配置管理器
    ctx.obj['config_manager'] = ConfigManager()
    # 初始化应用管理器
    ctx.obj['app_manager'] = AppManager(ctx.obj['config_manager'])
    # 初始化进程管理器
    ctx.obj['process_manager'] = ProcessManager(ctx.obj['config_manager'])


@cli.command('list', short_help='列出所有应用')
@click.option('-a', '--all', is_flag=True, help='显示所有详细信息')
@click.pass_context
def list_apps(ctx, all):
    """列出所有已注册的应用"""
    app_manager = ctx.obj['app_manager']
    app_manager.list_apps(show_details=all)


@cli.command('start', short_help='启动应用')
@click.argument('app_id', required=False)
@click.option('-s', '--start', help='目标路径')
@click.option('-i', '--interpreter', help='解释器路径')
@click.option('-c', '--conf', help='配置文件路径')
@click.option('-d', '--working-directory', help='工作目录')
@click.option('-p', '--params', help='命令参数')
@click.option('-n', '--name', help='应用名称')
@click.option('-g', '--generate', help='生成配置JSON文件，不启动应用')
@click.option('-b', '--before-execute', help='运行前环境检查脚本路径')
@click.option('--restart-control/--no-restart-control', default=True, help='是否控制程序的重启')
@click.option('--restart-check-delay', type=int, default=0, help='重启关键字检测延迟(秒)')
@click.option('--restart-keyword', multiple=True, help='如出现关键字则自动重启，多个关键字可重复使用此选项')
@click.option('--restart-keyword-regex', multiple=True, help='如出现正则关键字则自动重启，多个正则可重复使用此选项')
@click.option('-t', '--restart-wait-time', type=int, default=1, help='自动重启等待时间(秒)')
@click.option('--update-script', help='更新脚本路径')
@click.pass_context
def start_app(ctx, app_id, start, interpreter, conf, working_directory, params, name, generate,
              before_execute, restart_control, restart_check_delay, restart_keyword,
              restart_keyword_regex, restart_wait_time, update_script):
    """启动应用

    可以通过APP_ID启动已注册的应用，或者通过提供参数启动新应用
    """
    app_manager = ctx.obj['app_manager']

    # 如果指定了生成配置文件选项
    if generate and (start or conf):
        app_config = {}

        if conf:
            # 从配置文件加载基础配置
            loaded_config = app_manager.config_manager.load_app_config_from_file(conf)
            if loaded_config:
                app_config.update(loaded_config)

        # 使用命令行参数覆盖或补充配置
        if start:
            app_config['start'] = start
        if interpreter:
            app_config['interpreter'] = interpreter
        if working_directory:
            app_config['working_directory'] = working_directory
        if params:
            app_config['params'] = params
        if name:
            app_config['name'] = name
        if before_execute:
            app_config['before_execute'] = before_execute

        # 添加重启相关配置
        app_config['restart_control'] = restart_control
        app_config['restart_check_delay'] = restart_check_delay
        app_config['restart_keyword'] = list(restart_keyword) if restart_keyword else []
        app_config['restart_keyword_regex'] = list(restart_keyword_regex) if restart_keyword_regex else []
        app_config['restart_wait_time'] = restart_wait_time

        # 添加更新脚本配置
        if update_script:
            app_config['update_script'] = update_script

        # 生成配置文件
        app_manager.generate_app_config(app_config, generate)
        return

    # 正常启动应用流程
    if app_id:
        # 启动已存在的应用
        if app_id.lower() == 'all':
            # 启动所有应用
            app_manager.start_all_apps()
        else:
            try:
                app_id = int(app_id)
                app_manager.start_app_by_id(app_id)
            except ValueError:
                click.echo(f"错误: 应用ID必须是数字，收到的是 '{app_id}'")
                sys.exit(1)
    elif start or conf:
        # 启动新应用
        app_config = {
            'start': start,
            'interpreter': interpreter,
            'working_directory': working_directory,
            'params': params,
            'name': name,
            'before_execute': before_execute,
            'restart_control': restart_control,
            'restart_check_delay': restart_check_delay,
            'restart_keyword': list(restart_keyword) if restart_keyword else [],
            'restart_keyword_regex': list(restart_keyword_regex) if restart_keyword_regex else [],
            'restart_wait_time': restart_wait_time
        }

        # 添加更新脚本配置
        if update_script:
            app_config['update_script'] = update_script

        if conf:
            # 从配置文件加载
            app_manager.start_app_from_config(conf)
        else:
            # 使用命令行参数
            app_manager.start_app(app_config)
    else:
        click.echo("错误: 必须提供应用ID或启动路径")
        sys.exit(1)


@cli.command('stop', short_help='停止应用')
@click.argument('app_id')
@click.pass_context
def stop_app(ctx, app_id):
    """停止运行中的应用"""
    app_manager = ctx.obj['app_manager']

    if app_id.lower() == 'all':
        # 停止所有应用
        app_manager.stop_all_apps()
    else:
        try:
            app_id = int(app_id)
            app_manager.stop_app_by_id(app_id)
        except ValueError:
            click.echo(f"错误: 应用ID必须是数字，收到的是 '{app_id}'")
            sys.exit(1)


@cli.command('restart', short_help='重启应用')
@click.argument('app_id')
@click.pass_context
def restart_app(ctx, app_id):
    """重启应用"""
    app_manager = ctx.obj['app_manager']

    if app_id.lower() == 'all':
        # 重启所有应用
        app_manager.restart_all_apps()
    else:
        try:
            app_id = int(app_id)
            app_manager.restart_app_by_id(app_id)
        except ValueError:
            click.echo(f"错误: 应用ID必须是数字，收到的是 '{app_id}'")
            sys.exit(1)


@cli.command('delete', short_help='删除应用')
@click.argument('app_id')
@click.pass_context
def delete_app(ctx, app_id):
    """从管理列表中删除应用"""
    app_manager = ctx.obj['app_manager']

    if app_id.lower() == 'all':
        # 删除所有应用
        if click.confirm('确定要删除所有应用吗?'):
            app_manager.delete_all_apps()
    else:
        try:
            app_id = int(app_id)
            app_manager.delete_app_by_id(app_id)
        except ValueError:
            click.echo(f"错误: 应用ID必须是数字，收到的是 '{app_id}'")
            sys.exit(1)


@cli.command('log', short_help='查看应用日志')
@click.argument('app_id', required=False)
@click.option('-f', '--follow', is_flag=True, help='持续查看日志')
@click.option('-n', '--lines', type=int, default=10, help='显示的行数')
@click.pass_context
def view_log(ctx, app_id, follow, lines):
    """查看应用日志"""
    app_manager = ctx.obj['app_manager']

    if app_id:
        try:
            app_id = int(app_id)
            app_manager.view_app_log(app_id, follow, lines)
        except ValueError:
            click.echo(f"错误: 应用ID必须是数字，收到的是 '{app_id}'")
            sys.exit(1)
    else:
        # 查看AM3自身的日志
        app_manager.view_am3_log(follow, lines)


@cli.command('save', short_help='保存应用列表')
@click.pass_context
def save_apps(ctx):
    """保存当前应用列表配置"""
    app_manager = ctx.obj['app_manager']
    app_manager.save_apps()


@cli.command('load', short_help='加载应用列表')
@click.pass_context
def load_apps(ctx):
    """从保存的配置加载应用列表"""
    app_manager = ctx.obj['app_manager']
    app_manager.load_apps()


@cli.command('startup', short_help='设置开机自启动')
@click.pass_context
def setup_startup(ctx):
    """设置AM3开机自启动"""
    config_manager = ctx.obj['config_manager']
    config_manager.setup_startup()


@cli.group('api', short_help='API服务管理')
def api():
    """管理API服务"""
    pass


@api.command('init', short_help='初始化API服务')
@click.pass_context
def init_api(ctx):
    """初始化API服务配置"""
    config_manager = ctx.obj['config_manager']
    config_manager.init_api()


@api.command('start', short_help='启动API服务')
@click.pass_context
def start_api(ctx):
    """启动API服务"""
    app_manager = ctx.obj['app_manager']
    app_manager.start_api_service()


@api.command('stop', short_help='停止API服务')
@click.pass_context
def stop_api(ctx):
    """停止API服务"""
    app_manager = ctx.obj['app_manager']
    app_manager.stop_api_service()


# 设置命令别名
setup_aliases(cli)

if __name__ == '__main__':
    cli(obj={})
