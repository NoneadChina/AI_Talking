# -*- coding: utf-8 -*-
"""
AI服务单元测试
"""

import unittest
import time
import requests
from unittest.mock import MagicMock, patch, call
from src.utils.ai_service import (
    retry_with_backoff,
    RateLimiter,
    AIServiceFactory,
    OllamaAIService,
    OpenAIAIService,
    DeepSeekAIService,
    OllamaCloudAIService
)
from src.utils.secure_storage import (
    SecureStorage,
    init_secure_storage,
    encrypt_data,
    decrypt_data
)


class TestRetryWithBackoff(unittest.TestCase):
    """
    测试重试装饰器
    """
    
    def test_retry_success(self):
        """
        测试重试成功的情况
        """
        # 创建一个会失败两次然后成功的函数，使用requests.Timeout异常，这会被重试
        mock_func = MagicMock(side_effect=[requests.Timeout("第一次失败"), requests.Timeout("第二次失败"), "成功结果"])
        
        # 应用装饰器
        decorated_func = retry_with_backoff(max_retries=3, base_delay=0.1)(mock_func)
        
        # 调用函数
        result = decorated_func()
        
        # 验证结果和调用次数
        self.assertEqual(result, "成功结果")
        self.assertEqual(mock_func.call_count, 3)
    
    def test_retry_max_failed(self):
        """
        测试达到最大重试次数仍失败的情况
        """
        # 创建一个总是失败的函数，使用requests.ConnectionError异常，这会被重试
        mock_func = MagicMock(side_effect=requests.ConnectionError("总是失败"))
        
        # 应用装饰器
        decorated_func = retry_with_backoff(max_retries=2, base_delay=0.1)(mock_func)
        
        # 验证是否抛出异常
        with self.assertRaises(requests.ConnectionError):
            decorated_func()
        
        # 验证调用次数
        self.assertEqual(mock_func.call_count, 3)  # 初始调用 + 2次重试
    
    def test_retry_with_different_exceptions(self):
        """
        测试不同异常类型的重试
        """
        # 创建一个抛出不同异常的函数
        mock_func = MagicMock(side_effect=[
            ConnectionError("连接错误"),
            TimeoutError("超时错误"),
            "成功结果"
        ])
        
        # 应用装饰器，只重试ConnectionError
        decorated_func = retry_with_backoff(
            max_retries=3,
            base_delay=0.1,
            retry_exceptions=(ConnectionError,)
        )(mock_func)
        
        # 验证TimeoutError不会被重试
        with self.assertRaises(TimeoutError):
            decorated_func()
        
        # 验证调用次数
        self.assertEqual(mock_func.call_count, 2)  # 初始调用 + 1次重试ConnectionError


class TestRateLimiter(unittest.TestCase):
    """
    测试速率限制器
    """
    
    def test_rate_limiter_basic(self):
        """
        测试基本的速率限制功能
        """
        # 创建速率限制器：2次/秒
        rate_limiter = RateLimiter(max_calls=2, period=1.0)
        
        # 应用装饰器
        mock_func = MagicMock()
        decorated_func = rate_limiter(mock_func)
        
        # 快速调用3次
        decorated_func()
        decorated_func()
        
        # 记录开始时间
        start_time = time.time()
        decorated_func()  # 这次应该会被限制
        end_time = time.time()
        
        # 验证调用次数
        self.assertEqual(mock_func.call_count, 3)
        
        # 验证第三次调用是否被延迟了至少0.5秒（因为前两次是快速调用的）
        self.assertGreaterEqual(end_time - start_time, 0.5)
    
    def test_rate_limiter_different_service_types(self):
        """
        测试不同服务类型的独立速率限制
        """
        # 创建速率限制器：2次/秒
        rate_limiter = RateLimiter(max_calls=2, period=1.0)
        
        # 使用实际的AI服务类进行测试，这样会有正确的服务类型识别
        from src.utils.ai_service import OllamaAIService, OpenAIAIService
        
        # 创建不同类型的AI服务实例
        ollama_service = OllamaAIService(base_url="http://localhost:11434")
        openai_service = OpenAIAIService(api_key="test_key")
        
        # 记录调用时间
        start_time = time.time()
        
        # 对每个服务调用2次（不超过限制）
        for _ in range(2):
            # 调用不会实际执行，因为我们使用了mock
            with patch('requests.get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"models": []}
                ollama_service._fetch_models()
        
        for _ in range(2):
            # 调用不会实际执行，因为我们使用了mock
            with patch('requests.get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"data": []}
                openai_service._fetch_models()
        
        end_time = time.time()
        
        # 验证总时间不超过0.5秒（因为两个服务独立限制，都没有触发等待）
        self.assertLess(end_time - start_time, 0.5)


class TestSecureStorage(unittest.TestCase):
    """
    测试安全存储模块
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        # 初始化安全存储
        init_secure_storage("test_password")
    
    def test_encrypt_decrypt(self):
        """
        测试加密解密功能
        """
        test_data = "test_api_key_12345"
        
        # 加密数据
        encrypted = encrypt_data(test_data)
        
        # 验证加密后的数据与原数据不同
        self.assertNotEqual(encrypted, test_data)
        
        # 解密数据
        decrypted = decrypt_data(encrypted)
        
        # 验证解密后的数据与原数据相同
        self.assertEqual(decrypted, test_data)
    
    def test_secure_storage_instance(self):
        """
        测试安全存储实例的创建和使用
        """
        # 创建安全存储实例
        secure_storage = SecureStorage("test_password")
        
        test_data = "test_secure_data"
        
        # 加密数据
        encrypted = secure_storage.encrypt(test_data)
        
        # 解密数据
        decrypted = secure_storage.decrypt(encrypted)
        
        # 验证结果
        self.assertEqual(decrypted, test_data)
    
    def test_different_passwords(self):
        """
        测试不同密码的加密解密
        """
        test_data = "test_data"
        
        # 使用不同密码创建两个安全存储实例
        storage1 = SecureStorage("password1")
        storage2 = SecureStorage("password2")
        
        # 加密数据
        encrypted1 = storage1.encrypt(test_data)
        
        # 尝试用不同的密码解密，应该失败
        with self.assertRaises(Exception):
            storage2.decrypt(encrypted1)
    
    def test_encrypt_empty_string(self):
        """
        测试加密空字符串
        """
        result = encrypt_data("")
        self.assertEqual(result, "")
    
    def test_decrypt_empty_string(self):
        """
        测试解密空字符串
        """
        result = decrypt_data("")
        self.assertEqual(result, "")


class TestAIServiceFactory(unittest.TestCase):
    """
    测试AI服务工厂
    """
    
    def test_create_ollama_service(self):
        """
        测试创建Ollama服务
        """
        service = AIServiceFactory.create_ai_service("ollama", base_url="http://localhost:11434")
        self.assertIsInstance(service, OllamaAIService)
        self.assertEqual(service.base_url, "http://localhost:11434")
    
    def test_create_openai_service(self):
        """
        测试创建OpenAI服务
        """
        service = AIServiceFactory.create_ai_service("openai", api_key="test_key", base_url="https://api.openai.com/v1")
        self.assertIsInstance(service, OpenAIAIService)
        self.assertEqual(service.api_key, "test_key")
        self.assertEqual(service.base_url, "https://api.openai.com/v1")
    
    def test_create_deepseek_service(self):
        """
        测试创建DeepSeek服务
        """
        service = AIServiceFactory.create_ai_service("deepseek", api_key="test_key")
        self.assertIsInstance(service, DeepSeekAIService)
        self.assertEqual(service.api_key, "test_key")
    
    def test_create_ollama_cloud_service(self):
        """
        测试创建Ollama Cloud服务
        """
        service = AIServiceFactory.create_ai_service("ollama_cloud", api_key="test_key", base_url="http://localhost:11434")
        self.assertIsInstance(service, OllamaCloudAIService)
        self.assertEqual(service.api_key, "test_key")
        self.assertEqual(service.base_url, "http://localhost:11434")
    
    def test_create_invalid_service(self):
        """
        测试创建无效服务类型
        """
        with self.assertRaises(ValueError):
            AIServiceFactory.create_ai_service("invalid_service")


class TestAIServices(unittest.TestCase):
    """
    测试各种AI服务
    """
    
    def setUp(self):
        """
        测试前的设置工作
        """
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            "choices": [{"message": {"content": "测试响应"}}]
        }
        self.mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "test"}}]}',
            b'data: {"choices": [{"delta": {"content": "response"}}]}',
            b'data: [DONE]'
        ]
    
    @patch('requests.get')
    def test_ollama_get_models(self, mock_get):
        """
        测试Ollama获取模型列表
        """
        # 配置mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "models": [{"name": "llama2:7b"}, {"name": "deepseek-r1:8b"}]
        }
        
        # 创建服务实例
        service = OllamaAIService(base_url="http://localhost:11434")
        
        # 调用方法
        models = service._fetch_models()
        
        # 验证结果
        self.assertEqual(models, ["llama2:7b", "deepseek-r1:8b"])
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)
    
    @patch('requests.post')
    def test_openai_chat_completion(self, mock_post):
        """
        测试OpenAI聊天完成
        """
        # 配置mock
        mock_post.return_value = self.mock_response
        
        # 创建服务实例
        service = OpenAIAIService(api_key="test_key")
        
        # 调用方法
        result = service.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            model="gpt-3.5-turbo",
            temperature=0.8,
            stream=False
        )
        
        # 验证结果
        self.assertEqual(result, "测试响应")
    
    @patch('requests.post')
    def test_deepseek_chat_completion(self, mock_post):
        """
        测试DeepSeek聊天完成
        """
        # 配置mock
        mock_post.return_value = self.mock_response
        
        # 创建服务实例
        service = DeepSeekAIService(api_key="test_key")
        
        # 调用方法
        result = service.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            model="deepseek-chat",
            temperature=0.8,
            stream=False
        )
        
        # 验证结果
        self.assertEqual(result, "测试响应")
    
    @patch('requests.post')
    def test_ollama_cloud_chat_completion(self, mock_post):
        """
        测试Ollama Cloud聊天完成
        """
        # 配置mock
        self.mock_response.json.return_value = {"message": {"content": "测试响应"}}
        mock_post.return_value = self.mock_response
        
        # 创建服务实例
        service = OllamaCloudAIService(api_key="test_key", base_url="http://localhost:11434")
        
        # 调用方法
        result = service.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            model="minimax-m2:cloud",
            temperature=0.8,
            stream=False
        )
        
        # 验证结果
        self.assertEqual(result, "测试响应")
    
    @patch('requests.get')
    def test_openai_fetch_models_success(self, mock_get):
        """
        测试OpenAI成功获取模型列表
        """
        # 配置mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {"id": "gpt-3.5-turbo"}, 
                {"id": "gpt-4"}, 
                {"id": "dall-e-3"}  # 这个不会被返回，因为不匹配gpt-前缀
            ]
        }
        
        # 创建服务实例
        service = OpenAIAIService(api_key="test_key")
        
        # 调用方法
        models = service._fetch_models()
        
        # 验证结果
        self.assertEqual(models, ["gpt-3.5-turbo", "gpt-4"])
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_deepseek_fetch_models_success(self, mock_get):
        """
        测试DeepSeek成功获取模型列表
        """
        # 配置mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {"id": "deepseek-chat"}, 
                {"id": "deepseek-coder"}
            ]
        }
        
        # 创建服务实例
        service = DeepSeekAIService(api_key="test_key")
        
        # 调用方法
        models = service._fetch_models()
        
        # 验证结果
        self.assertEqual(models, ["deepseek-chat", "deepseek-coder"])
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_openai_fetch_models_unauthorized(self, mock_get):
        """
        测试OpenAI认证失败
        """
        import requests
        # 配置mock
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.text = "Invalid API key"
        mock_get.return_value = mock_response
        
        # 创建服务实例
        service = OpenAIAIService(api_key="invalid_key")
        
        # 模拟response.raise_for_status抛出HTTPError
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Unauthorized", response=mock_response)
        
        # 验证是否抛出异常
        with self.assertRaises(ValueError) as context:
            service._fetch_models()
        
        self.assertIn("认证失败", str(context.exception))
    
    @patch('requests.get')
    def test_deepseek_fetch_models_unauthorized(self, mock_get):
        """
        测试DeepSeek认证失败
        """
        import requests
        # 配置mock
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.text = "Invalid API key"
        mock_get.return_value = mock_response
        
        # 创建服务实例
        service = DeepSeekAIService(api_key="invalid_key")
        
        # 模拟response.raise_for_status抛出HTTPError
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Unauthorized", response=mock_response)
        
        # 验证是否抛出异常
        with self.assertRaises(ValueError) as context:
            service._fetch_models()
        
        self.assertIn("认证失败", str(context.exception))
    
    @patch('requests.post')
    def test_openai_chat_completion_stream(self, mock_post):
        """
        测试OpenAI流式聊天完成
        """
        # 配置mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "test"}}]}',
            b'data: {"choices": [{"delta": {"content": " stream"}}]}',
            b'data: [DONE]'
        ]
        mock_post.return_value = mock_response
        
        # 创建服务实例
        service = OpenAIAIService(api_key="test_key")
        
        # 调用方法
        result = service.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            model="gpt-3.5-turbo",
            temperature=0.8,
            stream=True
        )
        
        # 验证结果是生成器
        self.assertIsInstance(result, type((x for x in [])))
        
        # 收集生成器结果
        results = list(result)
        self.assertEqual(results, ["test", "test stream"])
    
    @patch('requests.post')
    def test_deepseek_chat_completion_stream(self, mock_post):
        """
        测试DeepSeek流式聊天完成
        """
        # 配置mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "test"}}]}',
            b'data: {"choices": [{"delta": {"content": " stream"}}]}',
            b'data: [DONE]'
        ]
        mock_post.return_value = mock_response
        
        # 创建服务实例
        service = DeepSeekAIService(api_key="test_key")
        
        # 调用方法
        result = service.chat_completion(
            messages=[{"role": "user", "content": "你好"}],
            model="deepseek-chat",
            temperature=0.8,
            stream=True
        )
        
        # 验证结果是生成器
        self.assertIsInstance(result, type((x for x in [])))
        
        # 收集生成器结果
        results = list(result)
        self.assertEqual(results, ["test", "test stream"])
    
    @patch('requests.post')
    def test_openai_chat_completion_rate_limit(self, mock_post):
        """
        测试OpenAI聊天完成限流
        """
        import requests
        # 配置mock返回429错误
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.reason = "Too Many Requests"
        mock_post.return_value = mock_response
        
        # 模拟response.raise_for_status抛出HTTPError
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Too Many Requests", response=mock_response)
        
        # 创建服务实例
        service = OpenAIAIService(api_key="test_key")
        
        # 验证是否抛出异常
        with self.assertRaises(ValueError) as context:
            service.chat_completion(
                messages=[{"role": "user", "content": "你好"}],
                model="gpt-3.5-turbo",
                temperature=0.8,
                stream=False
            )
        
        self.assertIn("限流", str(context.exception))
    
    @patch('requests.post')
    def test_deepseek_chat_completion_rate_limit(self, mock_post):
        """
        测试DeepSeek聊天完成限流
        """
        import requests
        # 配置mock返回429错误
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.reason = "Too Many Requests"
        mock_post.return_value = mock_response
        
        # 模拟response.raise_for_status抛出HTTPError
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Too Many Requests", response=mock_response)
        
        # 创建服务实例
        service = DeepSeekAIService(api_key="test_key")
        
        # 验证是否抛出异常
        with self.assertRaises(ValueError) as context:
            service.chat_completion(
                messages=[{"role": "user", "content": "你好"}],
                model="deepseek-chat",
                temperature=0.8,
                stream=False
            )
        
        self.assertIn("限流", str(context.exception))


class TestAIServiceInterface(unittest.TestCase):
    """
    测试AIServiceInterface的通用方法
    """
    
    def test_get_models_caching(self):
        """
        测试模型列表缓存机制
        """
        from src.utils.ai_service import AIServiceInterface
        
        # 创建一个测试子类
        class TestAIService(AIServiceInterface):
            def __init__(self):
                super().__init__()
                self.fetch_count = 0
            
            def _fetch_models(self):
                self.fetch_count += 1
                return ["model1", "model2", "model3"]
            
            def chat_completion(self, messages, model, temperature=0.8, stream=False, yield_full_response=True, **kwargs):
                return "test response"
        
        service = TestAIService()
        
        # 第一次调用，应该调用_fetch_models
        models1 = service.get_models()
        self.assertEqual(models1, ["model1", "model2", "model3"])
        self.assertEqual(service.fetch_count, 1)
        
        # 第二次调用，应该使用缓存
        models2 = service.get_models()
        self.assertEqual(models2, ["model1", "model2", "model3"])
        self.assertEqual(service.fetch_count, 1)
    
    def test_clear_cache(self):
        """
        测试清除缓存功能
        """
        from src.utils.ai_service import AIServiceInterface
        
        class TestAIService(AIServiceInterface):
            def __init__(self):
                super().__init__()
                self.fetch_count = 0
            
            def _fetch_models(self):
                self.fetch_count += 1
                return ["model1", "model2", "model3"]
            
            def chat_completion(self, messages, model, temperature=0.8, stream=False, yield_full_response=True, **kwargs):
                return "test response"
        
        service = TestAIService()
        service.get_models()  # 填充缓存
        self.assertEqual(service.fetch_count, 1)
        
        service.clear_cache()
        models = service.get_models()  # 应该重新获取
        self.assertEqual(models, ["model1", "model2", "model3"])
        self.assertEqual(service.fetch_count, 2)
    
    def test_refresh_cache(self):
        """
        测试刷新缓存功能
        """
        from src.utils.ai_service import AIServiceInterface
        
        class TestAIService(AIServiceInterface):
            def __init__(self):
                super().__init__()
                self.fetch_count = 0
            
            def _fetch_models(self):
                self.fetch_count += 1
                return [f"model1", f"model2", f"model3_v{self.fetch_count}"]
            
            def chat_completion(self, messages, model, temperature=0.8, stream=False, yield_full_response=True, **kwargs):
                return "test response"
        
        service = TestAIService()
        models1 = service.get_models()
        self.assertEqual(models1, ["model1", "model2", "model3_v1"])
        self.assertEqual(service.fetch_count, 1)
        
        models2 = service.refresh_cache()
        self.assertEqual(models2, ["model1", "model2", "model3_v2"])
        self.assertEqual(service.fetch_count, 2)
    
    def test_process_stream_response_openai_format(self):
        """
        测试处理OpenAI格式的流式响应
        """
        from src.utils.ai_service import AIServiceInterface
        
        class TestAIService(AIServiceInterface):
            def __init__(self):
                super().__init__()
            
            def _fetch_models(self):
                return []
            
            def chat_completion(self, messages, model, temperature=0.8, stream=False, yield_full_response=True, **kwargs):
                return "test response"
        
        # 创建响应模拟对象
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "test"}}]}',
            b'data: {"choices": [{"delta": {"content": " response"}}]}',
            b'data: [DONE]'
        ]
        
        service = TestAIService()
        stream_response = service._process_stream_response(
            mock_response, 
            response_format="openai", 
            yield_full_response=True
        )
        
        # 收集生成器结果
        results = list(stream_response)
        # OpenAI格式在收到data: [DONE]时不会yield结果
        self.assertEqual(results, ["test", "test response"])
    
    def test_process_stream_response_ollama_format(self):
        """
        测试处理Ollama格式的流式响应
        """
        from src.utils.ai_service import AIServiceInterface
        
        class TestAIService(AIServiceInterface):
            def __init__(self):
                super().__init__()
            
            def _fetch_models(self):
                return []
            
            def chat_completion(self, messages, model, temperature=0.8, stream=False, yield_full_response=True, **kwargs):
                return "test response"
        
        # 创建响应模拟对象
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            b'{"message": {"content": "test"}}',
            b'{"message": {"content": " response"}}',
            b'{"message": {"content": ""}, "done": true}'
        ]
        
        service = TestAIService()
        stream_response = service._process_stream_response(
            mock_response, 
            response_format="ollama", 
            yield_full_response=True
        )
        
        # 收集生成器结果
        results = list(stream_response)
        # Ollama格式在收到done: true时仍会yield最后一次结果
        self.assertEqual(results, ["test", "test response", "test response"])
    
    def test_process_stream_response_yield_partial(self):
        """
        测试流式响应只返回新增内容
        """
        from src.utils.ai_service import AIServiceInterface
        
        class TestAIService(AIServiceInterface):
            def __init__(self):
                super().__init__()
            
            def _fetch_models(self):
                return []
            
            def chat_completion(self, messages, model, temperature=0.8, stream=False, yield_full_response=True, **kwargs):
                return "test response"
        
        # 创建响应模拟对象
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "test"}}]}',
            b'data: {"choices": [{"delta": {"content": " response"}}]}',
            b'data: [DONE]'
        ]
        
        service = TestAIService()
        stream_response = service._process_stream_response(
            mock_response, 
            response_format="openai", 
            yield_full_response=False
        )
        
        # 收集生成器结果
        results = list(stream_response)
        self.assertEqual(results, ["test", " response"])


if __name__ == '__main__':
    unittest.main()