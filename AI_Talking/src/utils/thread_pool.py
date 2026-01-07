# -*- coding: utf-8 -*-
"""
线程池管理模块
用于管理和复用线程，提高线程使用效率
"""

import threading
import queue
from typing import Callable, Any, Optional
from .logger_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class ThreadPool:
    """
    线程池类，用于管理和复用线程
    """
    
    def __init__(self, max_workers: int = 5):
        """
        初始化线程池
        
        Args:
            max_workers: 线程池最大线程数，默认为5
        """
        self._max_workers = max_workers
        self._queue = queue.Queue()
        self._workers = []
        self._running = False
        self._lock = threading.Lock()
        
        logger.info(f"线程池已初始化，最大线程数: {max_workers}")
    
    def start(self):
        """
        启动线程池
        """
        with self._lock:
            if not self._running:
                self._running = True
                # 创建工作线程
                for i in range(self._max_workers):
                    worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"ThreadPoolWorker-{i}")
                    self._workers.append(worker)
                    worker.start()
                logger.info(f"线程池已启动，创建了 {self._max_workers} 个工作线程")
    
    def stop(self, wait: bool = True):
        """
        停止线程池
        
        Args:
            wait: 是否等待所有任务完成，默认为True
        """
        with self._lock:
            if self._running:
                self._running = False
                
                # 如果不需要等待，清空队列
                if not wait:
                    while not self._queue.empty():
                        try:
                            self._queue.get_nowait()
                        except queue.Empty:
                            break
                        self._queue.task_done()
                
                # 唤醒所有工作线程
                for _ in range(self._max_workers):
                    self._queue.put(None)  # 发送终止信号
                
                # 等待所有工作线程结束
                for worker in self._workers:
                    worker.join(2.0)  # 最多等待2秒
                
                # 清空工作线程列表
                self._workers.clear()
                logger.info(f"线程池已停止，等待任务完成: {wait}")
    
    def submit(self, task: Callable, *args, **kwargs) -> Optional[threading.Event]:
        """
        提交任务到线程池
        
        Args:
            task: 要执行的任务函数
            *args: 任务函数的位置参数
            **kwargs: 任务函数的关键字参数
        
        Returns:
            threading.Event: 用于标记任务完成的事件，None表示线程池未运行
        """
        with self._lock:
            if not self._running:
                logger.warning("线程池未运行，无法提交任务")
                return None
        
        done_event = threading.Event()
        
        def wrapper():
            """任务包装器，用于执行任务并标记完成"""
            try:
                task(*args, **kwargs)
            except Exception as e:
                logger.error(f"线程池任务执行出错: {str(e)}")
            finally:
                done_event.set()
        
        self._queue.put(wrapper)
        return done_event
    
    def _worker_loop(self):
        """
        工作线程循环，从队列中获取任务并执行
        """
        thread_name = threading.current_thread().name
        logger.debug(f"工作线程 {thread_name} 已启动")
        
        while True:
            try:
                task = self._queue.get()
                
                # 检查是否是终止信号
                if task is None:
                    logger.debug(f"工作线程 {thread_name} 收到终止信号")
                    self._queue.task_done()
                    break
                
                # 执行任务
                logger.debug(f"工作线程 {thread_name} 开始执行任务")
                task()
                logger.debug(f"工作线程 {thread_name} 完成任务")
                
                # 标记任务完成
                self._queue.task_done()
            except Exception as e:
                logger.error(f"工作线程 {thread_name} 出错: {str(e)}")
                # 标记任务完成，避免队列阻塞
                self._queue.task_done()
        
        logger.debug(f"工作线程 {thread_name} 已退出")
    
    def join(self):
        """
        等待所有任务完成
        """
        self._queue.join()
    
    def get_queue_size(self) -> int:
        """
        获取队列中的任务数量
        
        Returns:
            int: 队列中的任务数量
        """
        return self._queue.qsize()
    
    def is_running(self) -> bool:
        """
        检查线程池是否正在运行
        
        Returns:
            bool: 线程池是否正在运行
        """
        return self._running


# 创建全局线程池实例
# 根据系统CPU核心数调整，最大不超过8个线程
import os
try:
    cpu_count = os.cpu_count() or 4
    max_workers = min(cpu_count * 2, 8)
    thread_pool = ThreadPool(max_workers=max_workers)
except Exception as e:
    logger.error(f"创建全局线程池失败: {str(e)}")
    thread_pool = ThreadPool(max_workers=5)  # 失败时使用默认值
