# -*- coding: utf-8 -*-
"""
集成测试，测试模块之间的交互
"""

import unittest
import os
import json
from src.utils.chat_history_manager import ChatHistoryManager
from src.utils.error_monitor import ErrorMonitor

class IntegrationTest(unittest.TestCase):
    """
    集成测试类，测试模块之间的交互
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        # 创建临时测试文件
        self.test_file = "test_integration_chat_history.json"
        
        # 初始化组件
        self.chat_history_manager = ChatHistoryManager(self.test_file)
        self.error_monitor = ErrorMonitor()
        
        # 清空错误记录
        self.error_monitor.clear_errors()
    
    def tearDown(self):
        """
        测试后的清理工作
        """
        # 删除临时测试文件
        if os.path.exists(self.chat_history_manager.history_file):
            os.remove(self.chat_history_manager.history_file)
        
        # 清空错误记录
        self.error_monitor.clear_errors()
    
    def test_chat_history_and_error_monitor_integration(self):
        """
        测试聊天历史管理器与错误监控模块的集成
        """
        # 添加一些聊天历史
        for i in range(3):
            success = self.chat_history_manager.add_history(
                func_type="聊天",
                topic=f"集成测试主题{i}",
                model1_name=f"model{i}",
                model2_name=f"model{i+1}",
                api1=f"api{i}",
                api2=f"api{i+1}",
                rounds=2,
                chat_content=f"集成测试内容{i}",
                start_time=f"2023-01-01 12:00:00",
                end_time=f"2023-01-01 12:05:00"
            )
            self.assertTrue(success)
        
        # 检查聊天历史是否正确保存
        self.assertEqual(len(self.chat_history_manager.chat_histories), 3)
        
        # 检查错误监控是否记录了相关错误（应该没有错误）
        error_counts = self.error_monitor.get_error_counts()
        self.assertEqual(len(error_counts), 0)
        
        # 测试异常情况：尝试从不存在的文件加载历史
        non_existent_manager = ChatHistoryManager("non_existent_file.json")
        histories = non_existent_manager.load_history()
        
        # 应该返回空列表，而不是抛出异常
        self.assertEqual(len(histories), 0)
    
    def test_chat_history_size_limit(self):
        """
        测试聊天历史大小限制功能
        """
        # 设置较小的历史记录大小限制
        self.chat_history_manager.max_history_size = 2
        
        # 添加超过限制数量的历史记录
        for i in range(5):
            self.chat_history_manager.add_history(
                func_type="聊天",
                topic=f"测试主题{i}",
                model1_name=f"model{i}",
                model2_name=f"model{i+1}",
                api1=f"api{i}",
                api2=f"api{i+1}",
                rounds=1,
                chat_content=f"测试内容{i}",
                start_time=f"2023-01-01 12:00:00",
                end_time=f"2023-01-01 12:05:00"
            )
        
        # 保存历史记录
        self.chat_history_manager.save_history()
        
        # 重新加载历史记录
        new_manager = ChatHistoryManager(self.test_file)
        new_manager.load_history()
        
        # 检查历史记录数量是否符合限制
        self.assertEqual(len(new_manager.chat_histories), 2)
        
        # 检查是否只保留了最新的记录，通过检查模型名称来验证
        model1_names = [history["model1"] for history in new_manager.chat_histories]
        self.assertIn("model3", model1_names)
        self.assertIn("model4", model1_names)
    
    def test_error_monitor_integration(self):
        """
        测试错误监控模块与其他模块的集成
        """
        # 模拟一些错误
        for i in range(6):
            self.error_monitor.record_error(
                f"TestError{i}",
                f"Test error message {i}",
                f"test_module{i}"
            )
        
        # 检查错误计数
        error_counts = self.error_monitor.get_error_counts()
        self.assertEqual(len(error_counts), 6)
        
        # 检查最近错误记录
        recent_errors = self.error_monitor.get_recent_errors(3)
        self.assertEqual(len(recent_errors), 3)
        
        # 检查错误率
        error_rate = self.error_monitor.get_error_rate()
        self.assertGreater(error_rate, 0)
    
    def test_chat_history_workflow(self):
        """
        测试完整的聊天历史工作流
        """
        # 1. 添加聊天历史
        topic = "完整工作流测试"
        generated_topic = self.chat_history_manager.generate_formatted_topic("聊天", topic)
        success = self.chat_history_manager.add_history(
            func_type="聊天",
            topic=topic,
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=5,
            chat_content="这是一个完整的聊天历史工作流测试",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:10:00"
        )
        self.assertTrue(success)
        
        # 2. 根据主题获取历史记录
        history = self.chat_history_manager.get_history_by_topic(generated_topic)
        self.assertIsNotNone(history)
        self.assertEqual(history["model1"], "model1")
        
        # 3. 更新聊天历史
        success = self.chat_history_manager.add_history(
            func_type="聊天",
            topic=topic,
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=6,  # 更新轮数
            chat_content="这是更新后的聊天内容",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:15:00"
        )
        self.assertTrue(success)
        
        # 4. 检查历史记录是否已更新
        updated_history = self.chat_history_manager.get_history_by_topic(generated_topic)
        self.assertEqual(updated_history["rounds"], 6)
        self.assertEqual(updated_history["chat_content"], "这是更新后的聊天内容")
        
        # 5. 删除历史记录
        success = self.chat_history_manager.delete_history(0)
        self.assertTrue(success)
        
        # 6. 检查历史记录是否已删除
        deleted_history = self.chat_history_manager.get_history_by_topic(generated_topic)
        self.assertIsNone(deleted_history)

if __name__ == '__main__':
    unittest.main()
