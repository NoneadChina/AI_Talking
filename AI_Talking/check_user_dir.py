# -*- coding: utf-8 -*-
"""
检查用户目录是否正确创建
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.config_manager import get_app_data_dir

# 获取应用程序数据目录
app_data_dir = get_app_data_dir()
print(f"应用程序数据目录: {app_data_dir}")

# 检查目录是否存在
if os.path.exists(app_data_dir):
    print(f"目录已存在")
    # 列出目录下的文件
    files = os.listdir(app_data_dir)
    print(f"目录下的文件: {files}")
    
    # 检查logs子目录
    logs_dir = os.path.join(app_data_dir, 'logs')
    if os.path.exists(logs_dir):
        print(f"logs目录已存在")
        log_files = os.listdir(logs_dir)
        print(f"logs目录下的文件: {log_files}")
    else:
        print(f"logs目录不存在")
else:
    print(f"目录不存在")

# 检查salt.txt文件
from utils.secure_storage import _salt_file_path
print(f"salt.txt文件路径: {_salt_file_path}")
if os.path.exists(_salt_file_path):
    print(f"salt.txt文件已存在")
else:
    print(f"salt.txt文件不存在")

# 检查配置文件
from utils.config_manager import config_manager
print(f"配置文件路径: {config_manager.config_file_path}")
if os.path.exists(config_manager.config_file_path):
    print(f"配置文件已存在")
else:
    print(f"配置文件不存在")
