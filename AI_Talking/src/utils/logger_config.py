# -*- coding: utf-8 -*-
"""
日志配置模块
提供统一的日志配置，避免重复配置，便于维护
"""

import logging.config
import os
from .config_manager import config_manager

# 获取日志配置
log_level = config_manager.get('logging.level', 'INFO')
log_file_path = config_manager.get('logging.file_path', 'logs/app.log')
max_bytes = config_manager.get('logging.max_bytes', 10485760)  # 10MB
backup_count = config_manager.get('logging.backup_count', 5)

# 确保日志目录存在
log_dir = os.path.dirname(log_file_path)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# 详细的日志配置
dict_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file_path,
            "encoding": "utf-8",
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "formatter": "detailed",
            "level": log_level,
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": log_level,
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": log_level,
    },
    # 单独配置各模块的日志级别，减少冗余日志
    "loggers": {
        "urllib3": {"level": "WARNING", "handlers": ["file"], "propagate": False},
        "requests": {"level": "WARNING", "handlers": ["file"], "propagate": False},
        "PyQt5": {"level": "WARNING", "handlers": ["file"], "propagate": False},
    },
}

# 配置日志
logging.config.dictConfig(dict_config)


# 创建并返回logger实例
def get_logger(name=None):
    """
    获取日志记录器实例

    Args:
        name (str, optional): 日志记录器名称. Defaults to None.

    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)