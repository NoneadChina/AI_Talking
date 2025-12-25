# -*- coding: utf-8 -*-
"""
错误监控模块，用于记录和统计错误信息
"""

import time
import threading
from collections import defaultdict, deque
from .logger_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class ErrorMonitor:
    """
    错误监控类，用于记录和统计错误信息
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        单例模式，确保只创建一个ErrorMonitor实例
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ErrorMonitor, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        """
        初始化错误监控器
        """
        # 错误统计字典：{error_type: count}
        self.error_counts = defaultdict(int)

        # 最近的错误记录，最多保存100条
        self.recent_errors = deque(maxlen=100)

        # 时间窗口内的错误数，用于限流
        self.error_window = deque(maxlen=60)  # 1分钟窗口

        # 互斥锁，确保线程安全
        self._lock = threading.Lock()

        logger.info("错误监控器已初始化")

    def record_error(
        self, error_type: str, error_message: str, module: str = "unknown"
    ):
        """
        记录错误信息

        Args:
            error_type: 错误类型（如ConnectionError, TimeoutError等）
            error_message: 错误消息
            module: 发生错误的模块
        """
        with self._lock:
            # 增加错误计数
            self.error_counts[error_type] += 1

            # 记录最近的错误
            error_record = {
                "timestamp": time.time(),
                "type": error_type,
                "message": error_message,
                "module": module,
            }
            self.recent_errors.append(error_record)

            # 添加到时间窗口
            self.error_window.append(time.time())

            # 记录日志
            logger.error(f"[{module}] {error_type}: {error_message}")

            # 检查是否超过错误阈值
            self._check_error_threshold()

    def _check_error_threshold(self):
        """
        检查错误阈值，如果在时间窗口内错误数超过阈值，记录警告
        """
        current_time = time.time()

        # 统计最近1分钟内的错误数
        recent_errors = [t for t in self.error_window if current_time - t < 60]
        error_count = len(recent_errors)

        # 如果1分钟内错误数超过10，记录警告
        if error_count > 10:
            logger.warning(f"错误率过高：在过去60秒内发生了 {error_count} 个错误")

    def get_error_counts(self) -> dict:
        """
        获取错误统计

        Returns:
            dict: 错误类型和对应的数量
        """
        with self._lock:
            return dict(self.error_counts)

    def get_recent_errors(self, count: int = 10) -> list:
        """
        获取最近的错误记录

        Args:
            count: 要获取的错误数量，默认为10

        Returns:
            list: 最近的错误记录列表
        """
        with self._lock:
            return list(self.recent_errors)[-count:]

    def get_error_rate(self, window_seconds: int = 60) -> float:
        """
        获取指定时间窗口内的错误率

        Args:
            window_seconds: 时间窗口（秒），默认为60秒

        Returns:
            float: 错误率（错误数/秒）
        """
        with self._lock:
            current_time = time.time()
            recent_errors = [
                t for t in self.error_window if current_time - t < window_seconds
            ]
            return len(recent_errors) / window_seconds if window_seconds > 0 else 0

    def clear_errors(self):
        """
        清空错误记录
        """
        with self._lock:
            self.error_counts.clear()
            self.recent_errors.clear()
            self.error_window.clear()
            logger.info("错误记录已清空")


# 创建全局错误监控实例
error_monitor = ErrorMonitor()
