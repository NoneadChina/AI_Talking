# -*- coding: utf-8 -*-
"""
日志配置模块，用于配置和获取日志记录器
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# 日志文件路径
LOG_FILE = "ai_talking.log"

# 日志级别配置
LOG_LEVEL = logging.INFO

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 日志文件最大大小（字节）
MAX_LOG_SIZE = 10 * 1024 * 1024

# 日志文件备份数量
BACKUP_COUNT = 5

def get_logger(name):
    """
    获取日志记录器
    
    Args:
        name: 记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # 检查logger是否已经添加了handler
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        
        # 创建文件处理器
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger
