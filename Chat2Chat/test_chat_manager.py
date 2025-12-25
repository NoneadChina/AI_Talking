import os
import pytest
from unittest.mock import patch, MagicMock
# 导入日志配置模块
from logger_config import get_logger
from chat_between_ais import AIChatManager

class TestAIChatManager:
    """
    AIChatManager类的单元测试
    """
    
    @pytest.fixture
    def manager(self):
        """
        测试前的设置，创建AIChatManager实例
        """
        # 使用mock来避免实际创建OpenAI客户端
        with patch('chat_between_ais.OpenAI'):
            yield AIChatManager(
                model1_name="test-model-1",
                model2_name="test-model-2",
                model1_api="ollama",
                model2_api="ollama",
                openai_api_key="test-openai-key",
                deepseek_api_key="test-deepseek-key",
                ollama_base_url="http://localhost:11434",
                temperature=0.8
            )
    
    @patch('chat_between_ais.OpenAI')
    def test_initialization(self, mock_openai, manager):
        """
        测试AIChatManager的初始化
        """
        # 验证初始化
        assert manager.model1_name == "test-model-1"
        assert manager.model2_name == "test-model-2"
        assert manager.model1_api == "ollama"
        assert manager.model2_api == "ollama"
        assert manager.openai_api_key == "test-openai-key"
        assert manager.deepseek_api_key == "test-deepseek-key"
        assert manager.ollama_base_url == "http://localhost:11434"
        assert manager.temperature == 0.8
    
    def test_select_smallest_model(self, manager):
        """
        测试选择最小模型的功能
        """
        models = ["llama2:7b", "mistral:7b", "gemma:2b", "qwen3:14b"]
        smallest_model = manager._select_smallest_model(models)
        assert smallest_model == "gemma:2b"
        
        # 测试空列表
        assert manager._select_smallest_model([]) is None
        
        # 测试单个模型
        assert manager._select_smallest_model(["test-model"]) == "test-model"
    
    @patch('chat_between_ais.requests.Session')
    def test_get_ollama_models_success(self, mock_session_class, manager):
        """
        测试成功获取Ollama模型列表
        """
        # 模拟Session和响应
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # 模拟/api/tags端点响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "mistral"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        models = manager._get_ollama_models()
        assert models == ["llama2", "mistral"]
        mock_session.get.assert_called_once_with("http://localhost:11434/api/tags", timeout=30)
    
    @patch('chat_between_ais.requests.Session')
    def test_get_ollama_models_failure(self, mock_session_class, manager):
        """
        测试获取Ollama模型列表失败
        """
        # 模拟Session和响应
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # 模拟连接错误
        from requests.exceptions import ConnectionError
        mock_session.get.side_effect = ConnectionError("Connection refused")
        
        models = manager._get_ollama_models()
        assert models == []
    
    def test_api_handler_dispatching(self, manager):
        """
        测试API处理函数的调度
        """
        # 测试Ollama API处理
        with patch.object(manager, '_handle_ollama_request', return_value="ollama response"):
            response = manager.get_ai_response("test-model", [{"role": "user", "content": "test"}], "ollama")
            assert response == "ollama response"
        
        # 测试OpenAI API处理
        with patch.object(manager, '_handle_openai_request', return_value="openai response"):
            response = manager.get_ai_response("test-model", [{"role": "user", "content": "test"}], "openai")
            assert response == "openai response"
        
        # 测试DeepSeek API处理
        with patch.object(manager, '_handle_deepseek_request', return_value="deepseek response"):
            response = manager.get_ai_response("test-model", [{"role": "user", "content": "test"}], "deepseek")
            assert response == "deepseek response"
        

    
    def test_unknown_api_type(self, manager):
        """
        测试未知API类型的处理
        """
        response = manager.get_ai_response("test-model", [{"role": "user", "content": "test"}], "unknown")
        assert response == "抱歉，不支持的AI模型类型。"

if __name__ == '__main__':
    pytest.main([__file__])
