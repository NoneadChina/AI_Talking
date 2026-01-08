# -*- coding: utf-8 -*-
"""
初始化管理器测试
"""

import unittest
import time
from unittest.mock import MagicMock, patch
from src.utils.init_manager import InitManager, InitTask


class TestInitManager(unittest.TestCase):
    """
    测试初始化管理器的功能
    """
    
    def setUp(self):
        """
        每个测试方法前的设置
        """
        self.init_manager = InitManager()
    
    def tearDown(self):
        """
        每个测试方法后的清理
        """
        # 确保所有任务都已完成
        self.init_manager.clear_tasks()
    
    def test_init(self):
        """
        测试初始化管理器的初始化
        """
        self.assertIsNotNone(self.init_manager)
        self.assertIsInstance(self.init_manager, InitManager)
        self.assertEqual(len(self.init_manager._tasks), 0)
        self.assertFalse(self.init_manager._is_initializing)
    
    def test_add_task(self):
        """
        测试添加任务功能
        """
        # 创建测试任务
        task = InitTask("test_task", lambda: None)
        self.init_manager.add_task(task)
        
        # 验证任务已添加
        self.assertEqual(len(self.init_manager._tasks), 1)
        self.assertEqual(self.init_manager._tasks[0], task)
    
    def test_add_task_func(self):
        """
        测试添加任务函数功能
        """
        # 添加任务函数
        test_func = lambda: None
        self.init_manager.add_task_func("test_task_func", test_func, priority=1, blocking=True)
        
        # 验证任务已添加
        self.assertEqual(len(self.init_manager._tasks), 1)
        self.assertEqual(self.init_manager._tasks[0].name, "test_task_func")
        self.assertEqual(self.init_manager._tasks[0].priority, 1)
        self.assertTrue(self.init_manager._tasks[0].blocking)
    
    def test_start_initialization(self):
        """
        测试开始初始化功能
        """
        # 添加测试任务
        task_called = [False]
        
        def test_task():
            task_called[0] = True
        
        self.init_manager.add_task_func("test_task", test_task)
        self.init_manager.start_initialization()
        
        # 等待任务执行完成
        time.sleep(0.1)
        
        # 验证任务已执行
        self.assertTrue(task_called[0])
    
    def test_task_priority(self):
        """
        测试任务优先级功能
        """
        # 用于记录任务执行顺序
        execution_order = []
        
        def task1():
            execution_order.append(1)
        
        def task2():
            execution_order.append(2)
        
        def task3():
            execution_order.append(3)
        
        # 添加不同优先级的任务
        self.init_manager.add_task_func("task1", task1, priority=1)
        self.init_manager.add_task_func("task2", task2, priority=3)
        self.init_manager.add_task_func("task3", task3, priority=2)
        
        # 开始初始化
        self.init_manager.start_initialization()
        
        # 等待任务执行完成
        time.sleep(0.1)
        
        # 验证任务按优先级顺序执行
        self.assertEqual(execution_order, [2, 3, 1])
    
    def test_task_execution(self):
        """
        测试任务执行功能
        """
        # 用于记录任务执行结果
        result = []
        
        def test_task():
            result.append("task_executed")
            return "success"
        
        # 添加任务
        self.init_manager.add_task_func("test_task", test_task)
        self.init_manager.start_initialization()
        
        # 等待任务执行完成
        time.sleep(0.1)
        
        # 验证任务执行结果
        self.assertEqual(result, ["task_executed"])
    
    def test_task_failure(self):
        """
        测试任务失败处理
        """
        def failing_task():
            raise Exception("Task failed")
        
        # 添加失败任务
        self.init_manager.add_task_func("failing_task", failing_task)
        self.init_manager.start_initialization()
        
        # 等待任务执行完成
        time.sleep(0.1)
        
        # 验证管理器可以处理任务失败
        self.assertFalse(self.init_manager._is_initializing)
    
    def test_clear_tasks(self):
        """
        测试清空任务功能
        """
        # 添加多个任务
        self.init_manager.add_task_func("task1", lambda: None)
        self.init_manager.add_task_func("task2", lambda: None)
        self.init_manager.add_task_func("task3", lambda: None)
        
        # 验证任务已添加
        self.assertEqual(len(self.init_manager._tasks), 3)
        
        # 清空任务
        self.init_manager.clear_tasks()
        
        # 验证任务已清空
        self.assertEqual(len(self.init_manager._tasks), 0)
    
    def test_get_task_count(self):
        """
        测试获取任务数量功能
        """
        # 初始任务数量为0
        self.assertEqual(self.init_manager.get_task_count(), 0)
        
        # 添加任务后验证数量变化
        self.init_manager.add_task_func("task1", lambda: None)
        self.assertEqual(self.init_manager.get_task_count(), 1)
        
        self.init_manager.add_task_func("task2", lambda: None)
        self.assertEqual(self.init_manager.get_task_count(), 2)
    
    def test_is_initializing(self):
        """
        测试检查是否正在初始化功能
        """
        # 初始状态应为False
        self.assertFalse(self.init_manager.is_initializing())
        
        # 添加一个长时间运行的任务
        def long_running_task():
            time.sleep(0.5)
        
        self.init_manager.add_task_func("long_task", long_running_task, blocking=False)
        
        # 开始初始化
        self.init_manager.start_initialization()
        
        # 验证正在初始化
        self.assertTrue(self.init_manager.is_initializing())
        
        # 等待任务执行完成
        time.sleep(0.6)
        
        # 验证初始化已完成
        self.assertFalse(self.init_manager.is_initializing())
    
    def test_blocking_vs_non_blocking_tasks(self):
        """
        测试阻塞与非阻塞任务
        """
        execution_order = []
        
        def blocking_task():
            time.sleep(0.2)
            execution_order.append("blocking")
        
        def non_blocking_task():
            execution_order.append("non_blocking")
        
        # 添加阻塞任务和非阻塞任务
        self.init_manager.add_task_func("blocking", blocking_task, blocking=True)
        self.init_manager.add_task_func("non_blocking", non_blocking_task, blocking=False)
        
        # 开始初始化
        self.init_manager.start_initialization()
        
        # 等待任务执行完成
        time.sleep(0.3)
        
        # 验证执行顺序
        self.assertEqual(execution_order, ["blocking", "non_blocking"])
    
    def test_duplicate_task_names(self):
        """
        测试重复任务名称
        """
        # 添加相同名称的任务
        self.init_manager.add_task_func("duplicate_name", lambda: None)
        self.init_manager.add_task_func("duplicate_name", lambda: None)
        
        # 验证可以添加相同名称的任务
        self.assertEqual(len(self.init_manager._tasks), 2)
        self.assertEqual(self.init_manager._tasks[0].name, "duplicate_name")
        self.assertEqual(self.init_manager._tasks[1].name, "duplicate_name")


if __name__ == '__main__':
    unittest.main()
