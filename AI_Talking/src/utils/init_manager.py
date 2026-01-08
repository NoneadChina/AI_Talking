# -*- coding: utf-8 -*-
"""
初始化管理器，用于优化UI组件的初始化顺序，提高启动速度

该模块负责管理应用程序各组件的初始化顺序，将耗时操作放在后台线程中执行，
避免阻塞UI线程，从而提高应用程序的启动速度和响应性。
"""

import threading
from typing import List, Callable, Any
from PyQt5.QtCore import QObject, pyqtSignal
from src.utils.logger_config import get_logger

logger = get_logger(__name__)


class InitTask:
    """
    初始化任务类，封装初始化任务的相关信息
    
    设计目的：
    1. 封装初始化任务的所有属性，包括名称、函数、优先级和阻塞状态
    2. 提供统一的任务接口，便于初始化管理器管理和执行
    3. 支持优先级排序，确保重要任务先执行
    
    属性说明：
    - name: 任务名称，用于日志记录和进度显示
    - func: 任务函数，实际执行的初始化逻辑
    - priority: 优先级，值越高优先级越高，默认值为0
    - blocking: 是否阻塞UI线程，True表示在UI线程执行，False表示在后台线程执行
    """
    
    def __init__(self, name: str, func: Callable, priority: int = 0, blocking: bool = False):
        """
        初始化任务
        
        Args:
            name: 任务名称，用于标识和日志记录
            func: 任务函数，无参数，无返回值或返回任意值
            priority: 优先级，值越高优先级越高，默认值为0
            blocking: 是否阻塞UI线程，True表示在当前线程执行，False表示在后台线程执行
        """
        self.name = name  # 任务名称
        self.func = func  # 任务函数
        self.priority = priority  # 优先级
        self.blocking = blocking  # 是否阻塞UI线程


class InitManager(QObject):
    """
    初始化管理器，负责管理应用程序各组件的初始化顺序
    
    设计目的：
    1. 优化UI组件的初始化顺序，提高应用程序启动速度
    2. 将耗时操作放在后台线程中执行，避免阻塞UI线程
    3. 支持任务优先级，确保重要任务先执行
    4. 提供初始化进度反馈，便于UI显示启动进度
    5. 支持阻塞和非阻塞任务，灵活处理不同类型的初始化逻辑
    
    使用方式：
    - 通过全局实例init_manager访问初始化管理功能
    - 使用add_task或add_task_func方法添加初始化任务
    - 使用start_initialization方法开始执行初始化任务
    - 连接信号以获取初始化进度和状态变化
    
    信号说明：
    - init_started: 初始化开始时发出
    - init_progress: 初始化进度更新时发出，携带任务名称和进度百分比
    - init_completed: 所有任务完成时发出
    - task_completed: 单个任务完成时发出，携带任务名称
    """
    
    # 信号定义
    init_started = pyqtSignal()  # 初始化开始信号
    init_progress = pyqtSignal(str, int)  # 初始化进度信号，参数：任务名称，进度百分比
    init_completed = pyqtSignal()  # 初始化完成信号
    task_completed = pyqtSignal(str)  # 单个任务完成信号，参数：任务名称
    
    def __init__(self):
        """
        初始化管理器
        
        初始化内部状态，包括任务列表、已完成任务数、总任务数和初始化状态
        """
        super().__init__()
        self._tasks: List[InitTask] = []  # 初始化任务列表
        self._completed_tasks = 0  # 已完成的任务数
        self._total_tasks = 0  # 总任务数
        self._is_initializing = False  # 是否正在初始化
        
    def add_task(self, task: InitTask):
        """
        添加初始化任务
        
        Args:
            task: InitTask实例，包含任务的所有信息
        """
        self._tasks.append(task)
    
    def add_task_func(self, name: str, func: Callable, priority: int = 0, blocking: bool = False):
        """
        添加初始化任务函数，简化任务创建过程
        
        Args:
            name: 任务名称
            func: 任务函数，无参数，无返回值或返回任意值
            priority: 优先级，值越高优先级越高，默认值为0
            blocking: 是否阻塞UI线程，True表示在当前线程执行，False表示在后台线程执行
        """
        # 创建InitTask实例并添加到任务列表
        task = InitTask(name, func, priority, blocking)
        self.add_task(task)
    
    def start_initialization(self):
        """
        开始执行初始化任务
        
        执行流程：
        1. 检查是否正在初始化，如果是则返回
        2. 设置初始化状态为True
        3. 重置已完成任务数和总任务数
        4. 按优先级对任务进行排序
        5. 发出初始化开始信号
        6. 开始执行第一个任务
        """
        if self._is_initializing:
            logger.warning("Initialization already in progress")
            return
        
        # 设置初始化状态
        self._is_initializing = True
        self._completed_tasks = 0
        self._total_tasks = len(self._tasks)
        
        # 按优先级排序，优先级高的任务先执行
        self._tasks.sort(key=lambda x: x.priority, reverse=True)
        
        # 发出初始化开始信号
        self.init_started.emit()
        
        # 开始执行第一个任务
        self._execute_next_task()
    
    def _execute_next_task(self):
        """
        执行下一个任务
        
        执行流程：
        1. 检查是否所有任务都已完成，如果是则结束初始化
        2. 获取下一个要执行的任务
        3. 根据任务类型（阻塞/非阻塞）选择执行方式
        4. 阻塞任务在当前线程执行，非阻塞任务在后台线程执行
        """
        if self._completed_tasks >= self._total_tasks:
            # 所有任务执行完成
            self._is_initializing = False
            self.init_completed.emit()
            logger.info("All initialization tasks completed")
            return
        
        # 获取下一个任务
        task = self._tasks[self._completed_tasks]
        logger.info(f"Executing initialization task: {task.name}")
        
        if task.blocking:
            # 阻塞任务，在当前线程执行
            self._execute_task(task)
        else:
            # 非阻塞任务，在后台线程执行
            thread = threading.Thread(target=self._execute_task, args=(task,), daemon=True)
            thread.start()
    
    def _execute_task(self, task: InitTask):
        """
        执行单个任务
        
        执行流程：
        1. 尝试执行任务函数
        2. 记录任务执行结果（成功或失败）
        3. 更新已完成任务数和进度
        4. 发出任务完成和进度更新信号
        5. 递归调用执行下一个任务
        
        Args:
            task: 要执行的InitTask实例
        """
        try:
            # 执行任务
            result = task.func()
            logger.info(f"Initialization task completed: {task.name}")
        except Exception as e:
            # 记录任务执行失败日志
            logger.error(f"Initialization task failed: {task.name}, error: {str(e)}")
        
        # 更新进度
        self._completed_tasks += 1
        progress = int((self._completed_tasks / self._total_tasks) * 100)
        
        # 发送信号
        self.task_completed.emit(task.name)
        self.init_progress.emit(task.name, progress)
        
        # 执行下一个任务
        self._execute_next_task()
    
    def clear_tasks(self):
        """
        清空所有任务
        
        用于重置初始化管理器，清除所有已添加的任务
        """
        self._tasks.clear()
    
    def get_task_count(self) -> int:
        """
        获取当前任务数量
        
        Returns:
            int: 当前已添加的任务数量
        """
        return len(self._tasks)
    
    def is_initializing(self) -> bool:
        """
        检查是否正在初始化
        
        Returns:
            bool: True表示正在初始化，False表示未在初始化
        """
        return self._is_initializing


# 创建全局初始化管理器实例
init_manager = InitManager()
