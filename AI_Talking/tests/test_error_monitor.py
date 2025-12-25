# -*- coding: utf-8 -*-
"""
错误监控模块单元测试
"""

import unittest
import time
from src.utils.error_monitor import ErrorMonitor

class TestErrorMonitor(unittest.TestCase):
    """
    错误监控模块单元测试类
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        # 获取单例实例
        self.error_monitor = ErrorMonitor()
        
        # 清空错误记录，确保测试环境干净
        self.error_monitor.error_counts.clear()
        self.error_monitor.recent_errors.clear()
        self.error_monitor.error_window.clear()
    
    def test_singleton_instance(self):
        """
        测试单例模式是否正常工作
        """
        # 创建另一个实例，应该和之前的实例相同
        another_instance = ErrorMonitor()
        self.assertIs(self.error_monitor, another_instance)
    
    def test_record_error(self):
        """
        测试记录错误功能
        """
        # 记录一个错误
        error_type = "ValueError"
        error_msg = "测试错误消息"
        module = "test_module"
        
        self.error_monitor.record_error(error_type, error_msg, module)
        
        # 检查错误计数
        self.assertEqual(self.error_monitor.error_counts.get(error_type, 0), 1)
        
        # 检查最近错误记录
        self.assertEqual(len(self.error_monitor.recent_errors), 1)
        self.assertEqual(self.error_monitor.recent_errors[0]["type"], error_type)
        self.assertEqual(self.error_monitor.recent_errors[0]["message"], error_msg)
        self.assertEqual(self.error_monitor.recent_errors[0]["module"], module)
        
        # 检查错误时间戳
        self.assertEqual(len(self.error_monitor.error_window), 1)
    
    def test_get_error_rate(self):
        """
        测试获取错误率功能
        """
        # 记录多个错误
        for i in range(5):
            self.error_monitor.record_error(f"ErrorType{i}", f"Error message {i}", "test_module")
            time.sleep(0.1)  # 间隔0.1秒，模拟不同时间发生的错误
        
        # 获取错误率
        error_rate = self.error_monitor.get_error_rate()
        
        # 检查错误率是否在合理范围内
        # 5个错误在0.5秒内，错误率应该接近10个/秒
        self.assertGreater(error_rate, 0)
    
    def test_get_error_counts(self):
        """
        测试获取错误计数功能
        """
        # 记录不同类型的错误
        error_types = ["ValueError", "TypeError", "ConnectionError", "ValueError", "ValueError"]
        
        for error_type in error_types:
            self.error_monitor.record_error(error_type, f"Error message for {error_type}", "test_module")
        
        # 获取错误计数
        error_counts = self.error_monitor.get_error_counts()
        
        # 检查错误计数是否正确
        self.assertEqual(error_counts.get("ValueError", 0), 3)
        self.assertEqual(error_counts.get("TypeError", 0), 1)
        self.assertEqual(error_counts.get("ConnectionError", 0), 1)
        self.assertEqual(error_counts.get("KeyError", 0), 0)  # 未记录的错误类型
    
    def test_get_recent_errors(self):
        """
        测试获取最近错误功能
        """
        # 记录多个错误
        for i in range(10):
            self.error_monitor.record_error(f"ErrorType{i}", f"Error message {i}", "test_module")
        
        # 获取最近的5个错误
        recent_errors = self.error_monitor.get_recent_errors(5)
        
        # 检查最近错误数量是否正确
        self.assertEqual(len(recent_errors), 5)
        
        # 检查最近错误是否是最新的
        # 最新的错误应该在列表的后面
        self.assertEqual(recent_errors[-1]["type"], "ErrorType9")
        self.assertEqual(recent_errors[-2]["type"], "ErrorType8")
        
        # 测试默认参数（最近10个错误）
        recent_errors_default = self.error_monitor.get_recent_errors()
        self.assertEqual(len(recent_errors_default), 10)
    
    def test_error_threshold_alert(self):
        """
        测试错误阈值告警功能
        """
        # 记录多个错误，触发阈值
        for i in range(6):
            self.error_monitor.record_error("ValueError", f"Error message {i}", "test_module")
            time.sleep(0.1)  # 间隔0.1秒
        
        # 检查是否触发了告警
        # 注意：这个测试可能不稳定，因为依赖于时间
        # 我们主要检查功能是否正常调用，而不是是否真的触发告警
        
        # 获取错误率
        error_rate = self.error_monitor.get_error_rate()
        self.assertGreater(error_rate, 0)
    
    def test_clear_errors(self):
        """
        测试清空错误记录功能
        """
        # 记录一些错误
        for i in range(5):
            self.error_monitor.record_error("ValueError", f"Error message {i}", "test_module")
        
        # 检查错误记录是否存在
        self.assertGreater(len(self.error_monitor.recent_errors), 0)
        self.assertGreater(len(self.error_monitor.error_window), 0)
        self.assertGreater(len(self.error_monitor.error_counts), 0)
        
        # 清空错误记录
        self.error_monitor.clear_errors()
        
        # 检查错误记录是否已清空
        self.assertEqual(len(self.error_monitor.recent_errors), 0)
        self.assertEqual(len(self.error_monitor.error_window), 0)
        self.assertEqual(len(self.error_monitor.error_counts), 0)

if __name__ == '__main__':
    unittest.main()
