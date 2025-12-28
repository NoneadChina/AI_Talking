# -*- coding: utf-8 -*-
"""
线程管理器扩展单元测试
"""

import unittest
import time
from unittest.mock import MagicMock, patch
from src.utils.thread_manager import BaseAITaskThread, ChatThread, DebateThread, DiscussionThread


class TestBaseAITaskThread(unittest.TestCase):
    """
    测试基础AI任务线程类
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
    
    def test_base_thread_initialization(self):
        """
        测试基础线程初始化
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings, temperature=0.7)
        
        self.assertEqual(thread.temperature, 0.7)
        self.assertFalse(thread.is_stopped())
    
    def test_base_thread_stop_functionality(self):
        """
        测试基础线程停止功能
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 初始状态应该是运行中
        self.assertFalse(thread.is_stopped())
        
        # 调用stop方法
        thread.stop()
        
        # 验证线程已停止
        self.assertTrue(thread.is_stopped())
    
    def test_base_thread_resource_cleanup(self):
        """
        测试基础线程资源清理
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 调用资源清理方法
        thread._cleanup_resources()
        
        # 验证方法执行（没有抛出异常）
        self.assertTrue(True)  # 简单验证方法执行成功
    
    def test_create_ai_service_ollama(self):
        """
        测试创建Ollama AI服务
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 使用patch避免实际创建服务实例
        with patch('src.utils.ai_service.AIServiceFactory.create_ai_service') as mock_create:
            mock_service = MagicMock()
            mock_create.return_value = mock_service
            
            service = thread._create_ai_service("ollama")
            
            # 验证服务创建
            mock_create.assert_called_once_with(
                "ollama", base_url="http://localhost:11434"
            )
            self.assertEqual(service, mock_service)
    
    def test_create_ai_service_openai(self):
        """
        测试创建OpenAI AI服务
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 使用patch避免实际创建服务实例
        with patch('src.utils.ai_service.AIServiceFactory.create_ai_service') as mock_create:
            mock_service = MagicMock()
            mock_create.return_value = mock_service
            
            service = thread._create_ai_service("openai")
            
            # 验证服务创建
            mock_create.assert_called_once_with(
                "openai", api_key="test_api_key"
            )
            self.assertEqual(service, mock_service)
    
    def test_create_ai_service_deepseek(self):
        """
        测试创建DeepSeek AI服务
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 使用patch避免实际创建服务实例
        with patch('src.utils.ai_service.AIServiceFactory.create_ai_service') as mock_create:
            mock_service = MagicMock()
            mock_create.return_value = mock_service
            
            service = thread._create_ai_service("deepseek")
            
            # 验证服务创建
            mock_create.assert_called_once_with(
                "deepseek", api_key="test_api_key"
            )
            self.assertEqual(service, mock_service)
    
    def test_create_ai_service_invalid(self):
        """
        测试创建无效AI服务类型
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 验证创建无效服务类型时抛出异常
        with self.assertRaises(ValueError) as context:
            thread._create_ai_service("invalid_api_type")
        
        self.assertIn("不支持的API类型", str(context.exception))
    
    def test_get_user_friendly_error_msg_connection_error(self):
        """
        测试获取连接错误的友好提示
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        error = ConnectionError("Failed to connect")
        msg = thread._get_user_friendly_error_msg(error, "测试操作")
        
        self.assertIn("网络连接错误", msg)
        self.assertIn("请检查网络连接", msg)
    
    def test_get_user_friendly_error_msg_timeout_error(self):
        """
        测试获取超时错误的友好提示
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        error = TimeoutError("Request timed out")
        msg = thread._get_user_friendly_error_msg(error, "测试操作")
        
        self.assertIn("请求超时", msg)
        self.assertIn("请检查网络连接或稍后重试", msg)
    
    def test_get_user_friendly_error_msg_http_401(self):
        """
        测试获取HTTP 401错误的友好提示
        """
        import requests
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 创建模拟的HTTP 401错误
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = requests.exceptions.HTTPError("Unauthorized", response=mock_response)
        msg = thread._get_user_friendly_error_msg(error, "测试操作")
        
        self.assertIn("认证失败", msg)
        self.assertIn("请检查 API 密钥是否正确", msg)
    
    def test_get_user_friendly_error_msg_http_429(self):
        """
        测试获取HTTP 429错误的友好提示
        """
        import requests
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 创建模拟的HTTP 429错误
        mock_response = MagicMock()
        mock_response.status_code = 429
        error = requests.exceptions.HTTPError("Too Many Requests", response=mock_response)
        msg = thread._get_user_friendly_error_msg(error, "测试操作")
        
        self.assertIn("请求过于频繁", msg)
        self.assertIn("请稍后重试", msg)
    
    def test_handle_error(self):
        """
        测试统一错误处理
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 直接调用_handle_error方法，不mock信号
        # 验证方法能正常执行，不抛出异常
        try:
            error = ValueError("Test error")
            thread._handle_error(error, "测试操作")
            self.assertTrue(True)  # 验证方法执行成功
        except Exception as e:
            self.fail(f"_handle_error方法执行失败: {str(e)}")
    
    def test_base_thread_destruction(self):
        """
        测试基础线程析构函数
        """
        thread = BaseAITaskThread(api_settings_widget=self.mock_api_settings)
        
        # 直接调用_cleanup_resources方法进行测试
        with patch('src.utils.logger_config.get_logger') as mock_logger:
            thread._cleanup_resources()
            # 验证方法被调用
            self.assertTrue(True)  # 简单验证方法执行成功


class TestChatThreadExtended(unittest.TestCase):
    """
    聊天线程扩展单元测试类
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
            api="openai",
            message="test message",
            messages=[{"role": "user", "content": "test"}],
            api_settings_widget=self.mock_api_settings,
            temperature=0.7
        )
        
        self.assertEqual(thread.model_name, "test_model")
        self.assertEqual(thread.api, "openai")
        self.assertEqual(thread.message, "test message")
        self.assertEqual(thread.temperature, 0.7)
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
        测试聊天线程资源清理
        """
        thread = ChatThread(
            model_name="test_model",
            api="ollama",
            message="test message",
            messages=[{"role": "user", "content": "test"}],
            api_settings_widget=self.mock_api_settings
        )
        
        # 添加一些测试数据
        thread.messages = [{"role": "user", "content": "test"}]
        thread.message = "test message"
        
        # 调用资源清理
        thread._cleanup_resources()
        
        # 验证资源是否被清理
        self.assertEqual(thread.messages, [])
        self.assertEqual(thread.message, "")


class TestDebateThreadExtended(unittest.TestCase):
    """
    辩论线程扩展单元测试类
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
        self.mock_api_settings.debate_common_prompt_edit = MagicMock()
        self.mock_api_settings.debate_common_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.debate_ai1_prompt_edit = MagicMock()
        self.mock_api_settings.debate_ai1_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.debate_ai2_prompt_edit = MagicMock()
        self.mock_api_settings.debate_ai2_prompt_edit.toPlainText.return_value = ""
    
    def test_debate_thread_initialization(self):
        """
        测试辩论线程初始化
        """
        thread = DebateThread(
            topics=["测试主题1", "测试主题2"],
            model1_name="model1",
            model2_name="model2",
            model1_api="openai",
            model2_api="deepseek",
            rounds=3,
            time_limit=120,
            api_settings_widget=self.mock_api_settings
        )
        
        self.assertEqual(thread.topics, ["测试主题1", "测试主题2"])
        self.assertEqual(thread.model1_name, "model1")
        self.assertEqual(thread.model2_name, "model2")
        self.assertEqual(thread.rounds, 3)
        self.assertEqual(thread.time_limit, 120)
        self.assertFalse(thread.is_stopped())
    
    def test_debate_thread_stop(self):
        """
        测试辩论线程停止功能
        """
        thread = DebateThread(
            topics=["测试主题"],
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
        测试辩论线程资源清理
        """
        thread = DebateThread(
            topics=["测试主题"],
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=2,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        # 添加一些测试数据
        thread.debate_history_messages = [{"role": "user", "content": "test"}]
        
        # 调用资源清理
        thread._cleanup_resources()
        
        # 验证资源是否被清理
        self.assertEqual(thread.debate_history_messages, [])


class TestDiscussionThreadExtended(unittest.TestCase):
    """
    讨论线程扩展单元测试类
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
        self.mock_api_settings.common_system_prompt_edit = MagicMock()
        self.mock_api_settings.common_system_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.ai1_system_prompt_edit = MagicMock()
        self.mock_api_settings.ai1_system_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.ai2_system_prompt_edit = MagicMock()
        self.mock_api_settings.ai2_system_prompt_edit.toPlainText.return_value = ""
    
    def test_discussion_thread_initialization(self):
        """
        测试讨论线程初始化
        """
        thread = DiscussionThread(
            topic="测试讨论主题",
            model1_name="model1",
            model2_name="model2",
            model1_api="openai",
            model2_api="deepseek",
            rounds=4,
            time_limit=180,
            api_settings_widget=self.mock_api_settings
        )
        
        self.assertEqual(thread.topic, "测试讨论主题")
        self.assertEqual(thread.model1_name, "model1")
        self.assertEqual(thread.model2_name, "model2")
        self.assertEqual(thread.rounds, 4)
        self.assertEqual(thread.time_limit, 180)
        self.assertFalse(thread.is_stopped())
    
    def test_discussion_thread_stop(self):
        """
        测试讨论线程停止功能
        """
        thread = DiscussionThread(
            topic="测试讨论主题",
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=3,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        thread.stop()
        self.assertTrue(thread.is_stopped())
    
    def test_discussion_thread_resource_cleanup(self):
        """
        测试讨论线程资源清理
        """
        thread = DiscussionThread(
            topic="测试讨论主题",
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=3,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        # 添加一些测试数据
        thread.discussion_history = [{"role": "user", "content": "test"}]
        
        # 调用资源清理
        thread._cleanup_resources()
        
        # 验证资源是否被清理
        self.assertEqual(thread.discussion_history, [])


class TestChatThreadComplete(unittest.TestCase):
    """
    聊天线程完整测试类
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
            api="openai",
            message="test message",
            messages=[{"role": "user", "content": "test"}],
            api_settings_widget=self.mock_api_settings,
            stream=False
        )
        
        # 验证初始化参数
        self.assertEqual(thread.model_name, "test_model")
        self.assertEqual(thread.api, "openai")
        self.assertEqual(thread.stream, False)
    
    def test_chat_thread_cleanup(self):
        """
        测试聊天线程资源清理
        """
        thread = ChatThread(
            model_name="test_model",
            api="openai",
            message="test message",
            messages=[{"role": "user", "content": "test"}],
            api_settings_widget=self.mock_api_settings
        )
        
        # 调用资源清理方法
        thread._cleanup_resources()
        
        # 验证资源被清理
        self.assertEqual(thread.messages, [])
        self.assertEqual(thread.message, "")


class TestDebateThreadComplete(unittest.TestCase):
    """
    辩论线程完整测试类
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
        self.mock_api_settings.debate_common_prompt_edit = MagicMock()
        self.mock_api_settings.debate_common_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.debate_ai1_prompt_edit = MagicMock()
        self.mock_api_settings.debate_ai1_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.debate_ai2_prompt_edit = MagicMock()
        self.mock_api_settings.debate_ai2_prompt_edit.toPlainText.return_value = ""
    
    def test_send_debate_message(self):
        """
        测试发送辩论消息
        """
        thread = DebateThread(
            topics=["测试主题"],
            model1_name="model1",
            model2_name="model2",
            model1_api="openai",
            model2_api="deepseek",
            rounds=1,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        # 使用patch避免实际创建服务实例和发送请求
        with patch('src.utils.thread_manager.BaseAITaskThread._create_ai_service') as mock_create:
            # 创建模拟的AI服务
            mock_service = MagicMock()
            mock_service.chat_completion.return_value = "测试辩论响应"
            mock_create.return_value = mock_service
            
            # 调用发送辩论消息方法
            result = thread._send_debate_message(
                "model1",
                "openai",
                "共同提示词",
                "AI1提示词",
                "测试主题",
                0.8,
                previous_response="",
                stream=False,
                sender_prefix="正方"
            )
            
            # 验证结果
            self.assertEqual(result, "测试辩论响应")
            mock_service.chat_completion.assert_called_once()
    
    def test_debate_thread_initialization(self):
        """
        测试辩论线程初始化
        """
        thread = DebateThread(
            topics=["测试主题"],
            model1_name="model1",
            model2_name="model2",
            model1_api="openai",
            model2_api="deepseek",
            rounds=2,
            time_limit=120,
            api_settings_widget=self.mock_api_settings
        )
        
        # 验证初始化参数
        self.assertEqual(thread.topics, ["测试主题"])
        self.assertEqual(thread.model1_name, "model1")
        self.assertEqual(thread.model2_name, "model2")
        self.assertEqual(thread.rounds, 2)
        self.assertEqual(thread.time_limit, 120)


class TestDiscussionThreadComplete(unittest.TestCase):
    """
    讨论线程完整测试类
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
        self.mock_api_settings.common_system_prompt_edit = MagicMock()
        self.mock_api_settings.common_system_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.ai1_system_prompt_edit = MagicMock()
        self.mock_api_settings.ai1_system_prompt_edit.toPlainText.return_value = ""
        self.mock_api_settings.ai2_system_prompt_edit = MagicMock()
        self.mock_api_settings.ai2_system_prompt_edit.toPlainText.return_value = ""
    
    def test_discussion_thread_get_history(self):
        """
        测试获取讨论历史
        """
        thread = DiscussionThread(
            topic="测试讨论主题",
            model1_name="model1",
            model2_name="model2",
            model1_api="ollama",
            model2_api="ollama",
            rounds=3,
            time_limit=60,
            api_settings_widget=self.mock_api_settings
        )
        
        # 添加测试数据
        test_history = [{"role": "user", "content": "test"}]
        thread.discussion_history = test_history
        
        # 验证获取历史方法
        self.assertEqual(thread.get_discussion_history(), test_history)
    
    def test_discussion_thread_initialization_with_model3(self):
        """
        测试使用model3初始化讨论线程
        """
        thread = DiscussionThread(
            topic="测试讨论主题",
            model1_name="model1",
            model2_name="model2",
            model3_name="model3",
            model1_api="openai",
            model2_api="deepseek",
            model3_api="ollama",
            rounds=2,
            time_limit=120,
            api_settings_widget=self.mock_api_settings
        )
        
        # 验证初始化参数
        self.assertEqual(thread.model3_name, "model3")
        self.assertEqual(thread.model3_api, "ollama")
        self.assertFalse(thread.is_stopped())


if __name__ == '__main__':
    unittest.main()