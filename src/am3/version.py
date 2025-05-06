#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本信息模块
包含项目的版本号和其他版本相关信息
"""

# 版本号 (遵循语义化版本规范: https://semver.org/)
__version__ = '1.1.0'

# 版本名称
__version_name__ = 'Stable'

# 构建日期 (可以在发布时更新)
__build_date__ = '2023-11-15'

# 版本信息字典，可以在需要时扩展
VERSION_INFO = {
    'version': __version__,
    'version_name': __version_name__,
    'build_date': __build_date__
}

# 获取版本号的函数
def get_version():
    """获取当前版本号"""
    return __version__

# 获取完整版本信息的函数
def get_version_info():
    """获取完整版本信息"""
    return VERSION_INFO
