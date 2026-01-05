# -*- coding: utf-8 -*-
"""
查看配置文件内容
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.config_manager import config_manager

print(f"配置文件路径: {config_manager.config_file_path}")
if os.path.exists(config_manager.config_file_path):
    print("配置文件内容:")
    with open(config_manager.config_file_path, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("配置文件不存在")
    print(f"使用默认配置")
    print(f"日志文件路径: {config_manager.get('logging.file_path')}")
