# -*- coding: utf-8 -*-
"""
聊天历史管理器单元测试
"""

import unittest
import os
import json
from src.utils.chat_history_manager import ChatHistoryManager

class TestChatHistoryManager(unittest.TestCase):
    """
    聊天历史管理器单元测试类
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        # 创建临时测试文件
        self.test_file = "test_chat_history.json"
        self.manager = ChatHistoryManager(self.test_file)
        
    def tearDown(self):
        """
        测试后的清理工作
        """
        # 删除临时测试文件
        if os.path.exists(self.manager.history_file):
            os.remove(self.manager.history_file)
    
    def test_initialization(self):
        """
        测试初始化
        """
        self.assertEqual(len(self.manager.chat_histories), 0)
        # 检查文件路径是否正确（包含文件名）
        self.assertIn(self.test_file, self.manager.history_file)
    
    def test_add_history(self):
        """
        测试添加聊天历史
        """
        # 添加第一条历史记录
        success = self.manager.add_history(
            func_type="聊天",
            topic="测试主题",
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=3,
            chat_content="测试内容",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:05:00"
        )
        self.assertTrue(success)
        self.assertEqual(len(self.manager.chat_histories), 1)
        
        # 测试同一个模型组合的历史记录更新
        success = self.manager.add_history(
            func_type="聊天",
            topic="测试主题更新",
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=4,
            chat_content="测试内容更新",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:06:00"
        )
        self.assertTrue(success)
        self.assertEqual(len(self.manager.chat_histories), 1)  # 应该还是1条，因为是更新
        # 检查格式化后的主题是否正确
        self.assertIn("【聊天】", self.manager.chat_histories[0]["topic"])
    
    def test_load_history(self):
        """
        测试加载聊天历史
        """
        # 先添加一些历史记录
        self.manager.add_history(
            func_type="聊天",
            topic="测试主题",
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=3,
            chat_content="测试内容",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:05:00"
        )
        
        # 创建新的管理器实例，从文件加载历史
        new_manager = ChatHistoryManager(self.test_file)
        histories = new_manager.load_history()
        
        self.assertEqual(len(histories), 1)
        self.assertIn("【聊天】", histories[0]["topic"])
    
    def test_save_history(self):
        """
        测试保存聊天历史
        """
        # 添加历史记录
        self.manager.add_history(
            func_type="聊天",
            topic="测试主题",
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=3,
            chat_content="测试内容",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:05:00"
        )
        
        # 检查文件是否存在并包含正确内容
        self.assertTrue(os.path.exists(self.manager.history_file))
        
        with open(self.manager.history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 1)
        self.assertIn("【聊天】", data[0]["topic"])
    
    def test_get_history_by_topic(self):
        """
        测试根据主题获取聊天历史
        """
        # 添加历史记录并保存主题
        topic1 = self.manager.generate_formatted_topic("聊天", "测试主题1")
        self.manager.add_history(
            func_type="聊天",
            topic="测试主题1",
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=3,
            chat_content="测试内容1",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:05:00"
        )
        
        topic2 = self.manager.generate_formatted_topic("聊天", "测试主题2")
        self.manager.add_history(
            func_type="聊天",
            topic="测试主题2",
            model1_name="model3",
            model2_name="model4",
            api1="api3",
            api2="api4",
            rounds=2,
            chat_content="测试内容2",
            start_time="2023-01-01 13:00:00",
            end_time="2023-01-01 13:05:00"
        )
        
        # 根据主题获取历史记录
        history1 = self.manager.get_history_by_topic(topic1)
        history2 = self.manager.get_history_by_topic(topic2)
        non_existent_history = self.manager.get_history_by_topic("不存在的主题")
        
        self.assertIsNotNone(history1)
        self.assertEqual(history1["topic"], topic1)
        self.assertIsNotNone(history2)
        self.assertEqual(history2["topic"], topic2)
        self.assertIsNone(non_existent_history)
    
    def test_clear_history(self):
        """
        测试清空聊天历史
        """
        # 添加历史记录
        self.manager.add_history(
            func_type="聊天",
            topic="测试主题",
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=3,
            chat_content="测试内容",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:05:00"
        )
        
        # 清空历史记录
        success = self.manager.clear_history()
        
        self.assertTrue(success)
        self.assertEqual(len(self.manager.chat_histories), 0)
        
        # 检查文件是否也被清空
        self.assertTrue(os.path.exists(self.manager.history_file))
        with open(self.manager.history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 0)
    
    def test_delete_history(self):
        """
        测试删除指定索引的聊天历史
        """
        # 添加两条历史记录
        self.manager.add_history(
            func_type="聊天",
            topic="测试主题1",
            model1_name="model1",
            model2_name="model2",
            api1="api1",
            api2="api2",
            rounds=3,
            chat_content="测试内容1",
            start_time="2023-01-01 12:00:00",
            end_time="2023-01-01 12:05:00"
        )
        
        # 使用不同的模型组合添加第二条记录，确保不会被更新
        self.manager.add_history(
            func_type="聊天",
            topic="测试主题2",
            model1_name="model3",
            model2_name="model4",
            api1="api3",
            api2="api4",
            rounds=2,
            chat_content="测试内容2",
            start_time="2023-01-01 13:00:00",
            end_time="2023-01-01 13:05:00"
        )
        
        # 删除第一条历史记录
        success = self.manager.delete_history(0)
        
        self.assertTrue(success)
        self.assertEqual(len(self.manager.chat_histories), 1)
        # 检查剩余的记录是否包含正确的模型信息
        self.assertEqual(self.manager.chat_histories[0]["model1"], "model3")
        self.assertEqual(self.manager.chat_histories[0]["model2"], "model4")
        
        # 测试删除无效索引
        success = self.manager.delete_history(5)  # 无效索引
        self.assertFalse(success)
    
    def test_history_size_limit(self):
        """
        测试历史记录大小限制
        """
        # 设置较小的历史记录大小限制，便于测试
        self.manager.max_history_size = 3
        
        # 添加超过限制数量的历史记录
        for i in range(5):
            self.manager.add_history(
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
        
        # 保存并重新加载，检查是否超过限制
        self.manager.save_history()
        
        # 创建新的管理器实例，加载历史记录
        new_manager = ChatHistoryManager(self.test_file)
        new_manager.load_history()
        
        # 检查历史记录数量是否符合限制
        self.assertEqual(len(new_manager.chat_histories), 3)

if __name__ == '__main__':
    unittest.main()
