# -*- coding: utf-8 -*-
"""
集成测试模块，测试完整的功能流程
"""

import unittest
from unittest.mock import MagicMock, patch
from src.utils.ai_service import AIServiceFactory
from src.utils.thread_manager import ChatThread
from src.utils.secure_storage import (
    SecureStorage,
    init_secure_storage,
    encrypt_data,
    decrypt_data
)


class TestAIWorkflowIntegration(unittest.TestCase):
    """
    测试AI工作流程的集成测试
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        # 初始化安全存储
        init_secure_storage("test_password")
        
        # 创建模拟的API设置组件
        self.mock_api_settings = MagicMock()
        self.mock_api_settings.get_ollama_base_url.return_value = "http://localhost:11434"
        self.mock_api_settings.get_openai_api_key.return_value = "test_api_key"
        self.mock_api_settings.get_deepseek_api_key.return_value = "test_api_key"
    
    def test_secure_storage_integration(self):
        """
        测试安全存储完整流程
        """
        # 测试数据
        test_api_key = "my_secure_api_key_123"
        
        # 加密数据
        encrypted_key = encrypt_data(test_api_key)
        
        # 验证加密后的数据与原数据不同
        self.assertNotEqual(encrypted_key, test_api_key)
        
        # 解密数据
        decrypted_key = decrypt_data(encrypted_key)
        
        # 验证解密后的数据与原数据相同
        self.assertEqual(decrypted_key, test_api_key)
        
        # 测试空字符串处理
        self.assertEqual(encrypt_data(""), "")
        self.assertEqual(decrypt_data(""), "")
    
    def test_ai_service_factory_integration(self):
        """
        测试AI服务工厂集成
        """
        # 测试创建不同类型的AI服务
        with patch('src.utils.ai_service.OllamaAIService') as mock_ollama:
            with patch('src.utils.ai_service.OpenAIAIService') as mock_openai:
                with patch('src.utils.ai_service.DeepSeekAIService') as mock_deepseek:
                    with patch('src.utils.ai_service.OllamaCloudAIService') as mock_ollama_cloud:
                        # 配置mock返回值
                        mock_ollama.return_value = MagicMock()
                        mock_openai.return_value = MagicMock()
                        mock_deepseek.return_value = MagicMock()
                        mock_ollama_cloud.return_value = MagicMock()
                        
                        # 创建不同类型的服务
                        ollama_service = AIServiceFactory.create_ai_service("ollama", base_url="http://localhost:11434")
                        openai_service = AIServiceFactory.create_ai_service("openai", api_key="test_key")
                        deepseek_service = AIServiceFactory.create_ai_service("deepseek", api_key="test_key")
                        ollama_cloud_service = AIServiceFactory.create_ai_service("ollama_cloud", api_key="test_key")
                        
                        # 验证服务创建
                        self.assertIsNotNone(ollama_service)
                        self.assertIsNotNone(openai_service)
                        self.assertIsNotNone(deepseek_service)
                        self.assertIsNotNone(ollama_cloud_service)
    
    def test_chat_thread_workflow(self):
        """
        测试聊天线程完整工作流程
        """
        # 创建聊天线程
        thread = ChatThread(
            model_name="test_model",
            api="openai",
            message="test message",
            messages=[{"role": "user", "content": "test"}],
            api_settings_widget=self.mock_api_settings,
            stream=False
        )
        
        # 测试线程初始化和属性
        self.assertEqual(thread.model_name, "test_model")
        self.assertEqual(thread.api, "openai")
        self.assertEqual(thread.stream, False)
        
        # 测试资源清理
        thread._cleanup_resources()
        self.assertEqual(thread.messages, [])
        self.assertEqual(thread.message, "")
    
    def test_rate_limiter_integration(self):
        """
        测试速率限制器集成
        """
        from src.utils.ai_service import RateLimiter
        
        # 创建速率限制器：2次/秒
        rate_limiter = RateLimiter(max_calls=2, period=1.0)
        
        # 应用装饰器
        mock_func = MagicMock()
        decorated_func = rate_limiter(mock_func)
        
        # 快速调用2次（应该不会被限制）
        decorated_func()
        decorated_func()
        
        # 验证调用次数
        self.assertEqual(mock_func.call_count, 2)
    
    def test_retry_decorator_integration(self):
        """
        测试重试装饰器集成
        """
        from src.utils.ai_service import retry_with_backoff
        
        # 创建一个会失败两次然后成功的函数
        mock_func = MagicMock(side_effect=[
            Exception("第一次失败"), 
            Exception("第二次失败"), 
            "成功结果"
        ])
        
        # 应用装饰器
        decorated_func = retry_with_backoff(max_retries=3, base_delay=0.1)(mock_func)
        
        # 调用函数
        result = decorated_func()
        
        # 验证结果和调用次数
        self.assertEqual(result, "成功结果")
        self.assertEqual(mock_func.call_count, 3)
    
    def test_full_ai_service_integration(self):
        """
        测试完整的AI服务集成
        """
        # 测试完整的AI服务创建和方法调用
        with patch('src.utils.ai_service.requests.post') as mock_post:
            # 配置mock响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "测试响应"}}]
            }
            mock_post.return_value = mock_response
            
            # 创建服务实例
            service = AIServiceFactory.create_ai_service(
                "openai", 
                api_key="test_key",
                base_url="https://api.openai.com/v1"
            )
            
            # 验证服务创建
            self.assertIsNotNone(service)
    
    def test_secure_storage_with_ai_service(self):
        """
        测试安全存储与AI服务的集成
        """
        # 测试安全存储的API密钥被正确使用
        with patch('src.utils.ai_service.OpenAIAIService._fetch_models') as mock_fetch:
            # 配置mock返回值
            mock_fetch.return_value = ["gpt-3.5-turbo", "gpt-4"]
            
            # 创建安全存储实例
            secure_storage = SecureStorage("test_password")
            
            # 加密API密钥
            test_key = "my_secure_key"
            encrypted_key = secure_storage.encrypt(test_key)
            
            # 解密API密钥
            decrypted_key = secure_storage.decrypt(encrypted_key)
            
            # 创建AI服务并使用解密后的密钥
            service = AIServiceFactory.create_ai_service(
                "openai", 
                api_key=decrypted_key
            )
            
            # 验证服务创建
            self.assertIsNotNone(service)


if __name__ == '__main__':
    unittest.main()
