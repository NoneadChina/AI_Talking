# -*- coding: utf-8 -*-
"""
内存使用监控模块
用于定期监控应用程序的内存使用情况
"""

import os
import time
import threading
from typing import Optional

# 尝试导入psutil，如果不可用则使用模拟数据
psutil_available = False
try:
    import psutil
    psutil_available = True
except ImportError:
    pass

from .logger_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class MemoryMonitor:
    """
    内存使用监控类，定期记录应用程序的内存使用情况
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """
        单例模式，确保只创建一个MemoryMonitor实例
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MemoryMonitor, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """
        初始化内存监控器
        """
        self._running = False
        self._interval = 60  # 默认监控间隔为60秒
        self._thread = None
        self._process = None
        
        # 如果psutil可用，获取当前进程
        if psutil_available:
            self._process = psutil.Process(os.getpid())
        
        logger.info("内存监控器已初始化")
    
    def start(self, interval: int = 60):
        """
        启动内存监控
        
        Args:
            interval: 监控间隔，单位为秒，默认为60秒
        """
        if not self._running:
            self._interval = interval
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            logger.info(f"内存监控已启动，监控间隔: {interval}秒")
    
    def stop(self):
        """
        停止内存监控
        """
        if self._running:
            self._running = False
            if self._thread:
                self._thread.join(2.0)  # 等待线程结束，最多等待2秒
            logger.info("内存监控已停止")
    
    def _monitor_loop(self):
        """
        监控循环，定期检查内存使用情况
        """
        while self._running:
            try:
                self._log_memory_usage()
                time.sleep(self._interval)
            except Exception as e:
                logger.error(f"内存监控循环出错: {str(e)}")
                time.sleep(1.0)
    
    def _log_memory_usage(self):
        """
        记录当前内存使用情况
        """
        if psutil_available and self._process:
            try:
                # 获取内存使用情况
                mem_info = self._process.memory_info()
                mem_rss = mem_info.rss / 1024 / 1024  # 转换为MB
                mem_vms = mem_info.vms / 1024 / 1024  # 转换为MB
                
                # 获取CPU使用率
                cpu_percent = self._process.cpu_percent(interval=0.1)
                
                # 记录内存使用情况
                logger.info(
                    f"内存使用情况: 物理内存={mem_rss:.2f} MB, 虚拟内存={mem_vms:.2f} MB, CPU使用率={cpu_percent:.1f}%"
                )
            except Exception as e:
                logger.error(f"获取内存使用情况出错: {str(e)}")
        else:
            # psutil不可用，使用模拟数据
            logger.info("内存监控: psutil不可用，无法获取实际内存使用情况")
    
    def get_current_memory_usage(self) -> Optional[dict]:
        """
        获取当前内存使用情况
        
        Returns:
            dict: 内存使用情况，包含rss, vms, cpu_percent等字段；如果psutil不可用则返回None
        """
        if psutil_available and self._process:
            try:
                mem_info = self._process.memory_info()
                cpu_percent = self._process.cpu_percent(interval=0.1)
                
                return {
                    'rss': mem_info.rss / 1024 / 1024,  # MB
                    'vms': mem_info.vms / 1024 / 1024,  # MB
                    'cpu_percent': cpu_percent
                }
            except Exception as e:
                logger.error(f"获取当前内存使用情况出错: {str(e)}")
                return None
        return None


# 创建全局内存监控实例
memory_monitor = MemoryMonitor()
