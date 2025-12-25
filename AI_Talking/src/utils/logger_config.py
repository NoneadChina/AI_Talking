# -*- coding: utf-8 -*-
"""
日志配置模块
提供统一的日志配置，避免重复配置，便于维护
"""

import logging.config
import os

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
            "filename": "ai_talking.log",
            "encoding": "utf-8",
            "maxBytes": 5 * 1024 * 1024,  # 5MB，减少单个日志文件大小
            "backupCount": 3,  # 保留3个备份，减少总日志占用空间
            "formatter": "detailed",
            "level": "INFO",  # 降低文件日志级别，减少日志量
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "INFO",  # 降低根日志级别，减少日志量
    },
    # 单独配置urllib3的日志级别，减少HTTP请求日志
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
