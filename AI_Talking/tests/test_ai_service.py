# -*- coding: utf-8 -*-
"""
AI 服务模块单元测试
"""

import os
import tempfile
import json
import pytest
import sys
from unittest.mock import patch, MagicMock
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.ai_service import (
    AIServiceInterface,
    AIServiceFactory,
    retry_with_backoff,
    get_retry_decorator,
    RateLimiter
)


class TestAIServiceFactory:
    """
    测试AI服务工厂类
    """
    
    def test_register_service(self):
        """
        测试动态注册新的AI服务类型
        """
        # 创建一个测试服务类
        class TestAIService(AIServiceInterface):
            def __init__(self, api_key=None, **kwargs):
                super().__init__()
                self.api_key = api_key
            
            def _fetch_models(self):
                return ["test-model"]
            
            def chat_completion(self, messages, model, temperature=0.8, stream=False, yield_full_response=True, **kwargs):
                return "test response"
        
        # 注册新服务
        AIServiceFactory.register_service("test_service", TestAIService, ["api_key"])
        
        # 验证服务已注册
        assert "test_service" in AIServiceFactory.get_supported_services()
        
        # 测试创建服务实例
        ai_service = AIServiceFactory.create_ai_service("test_service", api_key="test-key")
        assert isinstance(ai_service, TestAIService)
        assert ai_service.api_key == "test-key"
        
        # 注销服务
        AIServiceFactory.unregister_service("test_service")
        assert "test_service" not in AIServiceFactory.get_supported_services()
    
    def test_get_supported_services(self):
        """
        测试获取所有支持的AI服务类型
        """
        services = AIServiceFactory.get_supported_services()
        assert isinstance(services, list)
        assert len(services) > 0
    
    def test_create_ai_service(self):
        """
        测试创建AI服务实例
        """
        # 测试创建已注册的服务实例
        ai_service = AIServiceFactory.create_ai_service("openai", api_key="test-key")
        assert isinstance(ai_service, AIServiceInterface)
    
    def test_clear_cache(self):
        """
        测试清除AI服务实例缓存
        """
        # 先创建一个服务实例
        AIServiceFactory.create_ai_service("openai", api_key="test-key")
        # 清除缓存
        AIServiceFactory.clear_cache()
        # 缓存已清除，应该返回新实例
        ai_service = AIServiceFactory.create_ai_service("openai", api_key="test-key")
        assert isinstance(ai_service, AIServiceInterface)


class TestRetryDecorator:
    """
    测试重试装饰器
    """
    
    def test_retry_with_backoff(self):
        """
        测试重试装饰器的基本功能
        """
        # 创建一个会失败的函数
        call_count = 0
        
        # 让装饰器重试所有类型的异常
        @retry_with_backoff(max_retries=2, base_delay=0.1, max_delay=0.5, retry_exceptions=(Exception,))
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Test exception")
            return "Success"
        
        # 调用函数，应该重试3次后成功
        result = failing_function()
        assert result == "Success"
        assert call_count == 3
    
    def test_retry_with_different_strategies(self):
        """
        测试不同的退避策略
        """
        # 测试指数退避
        @retry_with_backoff(max_retries=1, base_delay=0.1, backoff_strategy="exponential")
        def exponential_backoff_func():
            raise Exception("Test exception")
        
        # 测试线性退避
        @retry_with_backoff(max_retries=1, base_delay=0.1, backoff_strategy="linear")
        def linear_backoff_func():
            raise Exception("Test exception")
        
        # 测试固定退避
        @retry_with_backoff(max_retries=1, base_delay=0.1, backoff_strategy="fixed")
        def fixed_backoff_func():
            raise Exception("Test exception")
        
        # 这些函数应该都会抛出异常，但会按照不同策略重试
        with pytest.raises(Exception):
            exponential_backoff_func()
        
        with pytest.raises(Exception):
            linear_backoff_func()
        
        with pytest.raises(Exception):
            fixed_backoff_func()
    
    def test_get_retry_decorator(self):
        """
        测试根据服务类型获取重试装饰器
        """
        # 获取不同服务类型的重试装饰器
        openai_retry = get_retry_decorator("openai")
        ollama_retry = get_retry_decorator("ollama")
        default_retry = get_retry_decorator("default")
        
        # 验证返回的是可调用对象
        assert callable(openai_retry)
        assert callable(ollama_retry)
        assert callable(default_retry)


class TestRateLimiter:
    """
    测试速率限制器
    """
    
    def test_rate_limiter_basic(self):
        """
        测试速率限制器的基本功能
        """
        # 创建速率限制器实例
        rate_limiter = RateLimiter(max_calls=2, period=1)
        
        # 定义一个测试函数
        @rate_limiter
        def test_function():
            return "test result"
        
        # 调用函数两次，应该都成功
        result1 = test_function()
        result2 = test_function()
        assert result1 == "test result"
        assert result2 == "test result"
    
    def test_rate_limiter_adjustment(self):
        """
        测试速率限制器的动态调整功能
        """
        # 创建速率限制器实例
        rate_limiter = RateLimiter()
        
        # 调整速率限制
        rate_limiter.adjust_rate_limit("test_service", 10, 60)
        
        # 获取配置，验证调整是否成功
        config = rate_limiter._get_rate_limit_config("test_service")
        assert config["max_calls"] == 10
        assert config["period"] == 60
    
    def test_rate_limiter_event_recording(self):
        """
        测试速率限制器的事件记录功能
        """
        # 创建速率限制器实例
        rate_limiter = RateLimiter(max_calls=1, period=1)
        
        # 定义一个测试函数
        @rate_limiter
        def test_function():
            return "test result"
        
        # 调用函数两次，第二次会触发限流
        result1 = test_function()
        time.sleep(0.1)  # 稍等一下，确保时间差
        result2 = test_function()
        
        # 验证两次调用都成功（因为第一次调用后，第二次调用会等待）
        assert result1 == "test result"
        assert result2 == "test result"
    
    def test_get_rate_limit_config(self):
        """
        测试获取速率限制配置
        """
        # 创建速率限制器实例
        rate_limiter = RateLimiter()
        
        # 获取默认配置
        config = rate_limiter._get_rate_limit_config("openai")
        assert isinstance(config, dict)
        assert "max_calls" in config
        assert "period" in config
        assert "burst_limit" in config
        assert "adjust_factor" in config
    
    def test_record_rate_limit_event(self):
        """
        测试记录限流事件
        """
        # 创建速率限制器实例
        rate_limiter = RateLimiter(max_calls=100, period=60, adjust_factor=0.9)
        
        # 记录5次限流事件，应该不会触发调整
        for _ in range(5):
            rate_limiter.record_rate_limit_event("test_service")
        
        # 获取配置，验证没有调整
        config = rate_limiter._get_rate_limit_config("test_service")
        assert config["max_calls"] == 100
        
        # 再记录1次限流事件，应该触发调整
        rate_limiter.record_rate_limit_event("test_service")
        
        # 获取配置，验证已调整
        config = rate_limiter._get_rate_limit_config("test_service")
        assert config["max_calls"] == 90  # 100 * 0.9


if __name__ == "__main__":
    pytest.main([__file__])
