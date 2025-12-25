# -*- coding: utf-8 -*-
"""
线程管理器单元测试
"""

import unittest
import time
from unittest.mock import MagicMock, patch
from src.utils.thread_manager import ChatThread, DebateThread, DiscussionThread

class TestChatThread(unittest.TestCase):
    """
    聊天线程单元测试类
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        # 创建模拟的API设置组件
        self.mock_api_settings = MagicMock()
        self.mock_api_settings.get_ollama_base_url.return_value = "http://localhost:11434"
        self.mock_api_settings.get_openai_api_key.return_value = "test_api_key"
        self.mock_api_settings.get_deepseek_api_key.return_value = "test_api_key"
        
    def test_chat_thread_initialization(self):
        """
        测试聊天线程初始化
        """
        thread = ChatThread(
            model_name="test_model",
            api="ollama",
            message="test message",
            messages=[{"role": "user", "content": "test"}],
            api_settings_widget=self.mock_api_settings
        )
        
        self.assertEqual(thread.model_name, "test_model")
        self.assertEqual(thread.api, "ollama")
        self.assertFalse(thread.is_stopped())
    
    def test_chat_thread_stop(self):
        """
        测试聊天线程停止功能
        """
        thread = ChatThread(
            model_name="test_model",
            api="ollama",
            message="test message",
            messages=[{"role": "user", "content": "test"}],
            api_settings_widget=self.mock_api_settings
        )
        
        thread.stop()
        self.assertTrue(thread.is_stopped())
    
    def test_chat_thread_resource_cleanup(self):
        """
        测试聊天线程资源清理功能
        """
        thread = ChatThread(
            model_name="test_model",
            api="ollama",
            message="test message",
            messages=[{"role": "user", "content": "test"}],
            api_settings_widget=self.mock_api_settings
        )
        
        # 模拟线程运行和停止
        thread._cleanup_resources()
        
        # 检查资源是否被清理
        self.assertEqual(thread.messages, [])
        self.assertEqual(thread.message, "")

class TestDebateThread(unittest.TestCase):
    """
    辩论线程单元测试类
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        # 创建模拟的API设置组件
        self.mock_api_settings = MagicMock()
        self.mock_api_settings.get_ollama_base_url.return_value = "http://localhost:11434"
        self.mock_api_settings.get_openai_api_key.return_value = "test_api_key"
        self.mock_api_settings.get_deepseek_api_key.return_value = "test_api_key"
        self.mock_api_settings.debate_common_prompt_edit.toPlainText.return_value = ""  
        self.mock_api_settings.debate_ai1_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.debate_ai2_prompt_edit.toPlainText.return_value = ""
    
    def test_debate_thread_initialization(self):
        """
        测试辩论线程初始化
        """
        thread = DebateThread(
            topics=["test topic"],
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=2,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        self.assertEqual(thread.model1_name, "model1")
        self.assertEqual(thread.model2_name, "model2")
        self.assertEqual(thread.rounds, 2)
        self.assertFalse(thread.is_stopped())
    
    def test_debate_thread_stop(self):
        """
        测试辩论线程停止功能
        """
        thread = DebateThread(
            topics=["test topic"],
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=2,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        thread.stop()
        self.assertTrue(thread.is_stopped())
    
    def test_debate_thread_resource_cleanup(self):
        """
        测试辩论线程资源清理功能
        """
        thread = DebateThread(
            topics=["test topic"],
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=2,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        # 添加一些测试数据到辩论历史
        thread.debate_history_messages.append({"role": "user", "content": "test"})
        
        # 测试资源清理
        thread._cleanup_resources()
        
        # 检查资源是否被清理
        self.assertEqual(thread.debate_history_messages, [])

class TestDiscussionThread(unittest.TestCase):
    """
    讨论线程单元测试类
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        # 创建模拟的API设置组件
        self.mock_api_settings = MagicMock()
        self.mock_api_settings.get_ollama_base_url.return_value = "http://localhost:11434"
        self.mock_api_settings.get_openai_api_key.return_value = "test_api_key"
        self.mock_api_settings.get_deepseek_api_key.return_value = "test_api_key"
        self.mock_api_settings.common_system_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.ai1_system_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.ai2_system_prompt_edit.toPlainText.return_value = ""
    
    def test_discussion_thread_initialization(self):
        """
        测试讨论线程初始化
        """
        thread = DiscussionThread(
            topic="test topic",
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=2,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        self.assertEqual(thread.topic, "test topic")
        self.assertEqual(thread.model1_name, "model1")
        self.assertEqual(thread.rounds, 2)
        self.assertFalse(thread.is_stopped())
    
    def test_discussion_thread_stop(self):
        """
        测试讨论线程停止功能
        """
        thread = DiscussionThread(
            topic="test topic",
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=2,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        thread.stop()
        self.assertTrue(thread.is_stopped())
    
    def test_discussion_thread_resource_cleanup(self):
        """
        测试讨论线程资源清理功能
        """
        thread = DiscussionThread(
            topic="test topic",
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=2,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        # 添加一些测试数据到讨论历史
        thread.discussion_history.append({"role": "user", "content": "test"})
        
        # 测试资源清理
        thread._cleanup_resources()
        
        # 检查资源是否被清理
        self.assertEqual(thread.discussion_history, [])
    
    def test_discussion_thread_time_limit(self):
        """
        测试讨论线程时间限制
        """
        thread = DiscussionThread(
            topic="test topic",
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=10,  # 大量轮次，确保触发时间限制
            time_limit=1,  # 1秒时间限制
            api_settings_widget=self.mock_api_settings
        )
        
        # 测试时间限制属性
        self.assertEqual(thread.time_limit, 1)

if __name__ == '__main__':
    unittest.main()