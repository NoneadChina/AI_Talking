import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
import sys
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_between_ais import AIChatManager
from chat_gui import ChatThread

class TestAIChatManagerIntegration:
    """测试AIChatManager的集成功能"""
    
    def test_ai_chat_manager_init(self):
        """测试AIChatManager初始化集成"""
        # 测试AIChatManager初始化
        manager = AIChatManager(
            model1_name="gemma3:270m",
            model2_name="gemma3:1b",
            model1_api="ollama",
            model2_api="ollama",
            openai_api_key="test-key",
            deepseek_api_key="test-key",
            ollama_base_url="http://localhost:11434",
            temperature=0.8
        )
        
        # 验证初始化
        assert manager is not None
        assert manager.model1_name == "gemma3:270m"
        assert manager.model2_name == "gemma3:1b"
        assert manager.model1_api == "ollama"
        assert manager.model2_api == "ollama"
        assert manager.temperature == 0.8
    
    @patch('chat_between_ais.requests.Session')
    def test_get_ollama_models(self, mock_session_class):
        """测试获取Ollama模型列表集成"""
        # 创建模拟会话和响应
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # 模拟/api/tags端点响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "gemma3:270m"},
                {"name": "gemma3:1b"},
                {"name": "deepseek-r1:8b"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        # 创建AIChatManager实例
        manager = AIChatManager()
        
        # 调用_get_ollama_models方法
        models = manager._get_ollama_models()
        
        # 验证结果
        assert isinstance(models, list)
        assert len(models) == 3
        assert "gemma3:270m" in models
        assert "gemma3:1b" in models
        assert "deepseek-r1:8b" in models
    
    def test_select_smallest_model(self):
        """测试选择最小模型功能集成"""
        # 创建AIChatManager实例
        manager = AIChatManager()
        
        # 测试模型选择
        models = ["gemma3:270m", "gemma3:1b", "deepseek-r1:8b", "qwen3:14b"]
        smallest_model = manager._select_smallest_model(models)
        
        # 验证结果
        assert smallest_model == "gemma3:270m"
    
    def test_api_handler_dispatching(self):
        """测试API处理函数调度集成"""
        # 创建AIChatManager实例
        manager = AIChatManager()
        
        # 测试API处理函数调度
        with patch.object(manager, '_handle_ollama_request', return_value="ollama response"):
            response = manager.get_ai_response(
                "test-model", 
                [{"role": "user", "content": "test message"}], 
                "ollama"
            )
            assert response == "ollama response"
        
        with patch.object(manager, '_handle_openai_request', return_value="openai response"):
            response = manager.get_ai_response(
                "gpt-3.5-turbo", 
                [{"role": "user", "content": "test message"}], 
                "openai"
            )
            assert response == "openai response"
        
        with patch.object(manager, '_handle_deepseek_request', return_value="deepseek response"):
            response = manager.get_ai_response(
                "deepseek-chat", 
                [{"role": "user", "content": "test message"}], 
                "deepseek"
            )
            assert response == "deepseek response"
        

    
    def test_invalid_api_type(self):
        """测试无效API类型处理"""
        # 创建AIChatManager实例
        manager = AIChatManager()
        
        # 测试无效API类型
        response = manager.get_ai_response(
            "test-model", 
            [{"role": "user", "content": "test message"}], 
            "invalid-api"
        )
        
        # 验证结果
        assert response == "抱歉，不支持的AI模型类型。"

class TestChatThreadIntegration:
    """测试ChatThread的集成功能"""
    
    def test_chat_thread_with_mock_manager(self):
        """测试ChatThread与模拟AIChatManager的集成"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 模拟get_ai_response方法
        mock_manager.get_ai_response.side_effect = [
            "AI1: 这是我的第一个观点",
            "AI2: 我不同意，我的观点是...",
            "AI1: 我理解你的观点，但...",
            "AI2: 但是...",
            "AI1: 总结一下..."
        ]
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试集成主题",
            rounds=5,
            time_limit=0
        )
        
        # 验证初始化
        assert thread is not None
        assert thread.topic == "测试集成主题"
        assert thread.rounds == 5
        assert not thread.is_stopped()
    
    def test_chat_thread_debate_mode(self):
        """测试辩论模式的ChatThread集成"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 模拟get_ai_response方法
        mock_manager.get_ai_response.side_effect = [
            "正方: 我支持...",
            "反方: 我反对...",
            "正方: 我的论据是...",
            "反方: 我的反驳是..."
        ]
        
        # 初始化辩论模式的ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试辩论主题",
            rounds=4,
            time_limit=0,
            is_debate=True
        )
        
        # 验证初始化
        assert thread is not None
        assert thread.is_debate is True
        assert thread.topic == "测试辩论主题"
    
    @patch('chat_gui.ChatThread.run')
    def test_chat_thread_lifecycle(self, mock_run):
        """测试ChatThread完整生命周期集成"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试生命周期主题",
            rounds=3,
            time_limit=0
        )
        
        # 测试生命周期
        assert not thread.is_stopped()
        
        # 启动线程
        thread.start()
        time.sleep(0.1)  # 等待线程启动
        assert thread.isRunning() is True
        
        # 停止线程
        thread.stop()
        assert thread.is_stopped()
        
        # 等待线程结束
        thread.wait()
        assert thread.isFinished() is True

class TestEndToEnd:
    """端到端测试"""
    
    def test_basic_chat_flow(self):
        """测试基本聊天流程"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 模拟聊天流程
        mock_manager.get_ai_response.side_effect = [
            "AI1: 你好，很高兴与你讨论。",
            "AI2: 你好，我也很高兴。",
            "AI1: 今天我们讨论的主题是...",
            "AI2: 我对这个主题的看法是..."
        ]
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试端到端聊天",
            rounds=4,
            time_limit=0
        )
        
        # 验证初始化
        assert thread is not None
        assert thread.topic == "测试端到端聊天"
        assert thread.rounds == 4
    
    def test_discussion_flow(self):
        """测试讨论流程"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 模拟讨论流程
        mock_manager.get_ai_response.side_effect = [
            "学者AI1: 关于这个问题，我的研究表明...",
            "学者AI2: 我的研究结果有所不同...",
            "学者AI1: 我理解你的观点，但我的数据显示...",
            "学者AI2: 但是，如果你考虑到...",
            "学者AI1: 总结一下我们的讨论..."
        ]
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试端到端讨论",
            rounds=5,
            time_limit=0
        )
        
        # 验证初始化
        assert thread is not None
        assert thread.topic == "测试端到端讨论"
        assert thread.rounds == 5
    
    def test_debate_flow(self):
        """测试辩论流程"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 模拟辩论流程
        mock_manager.get_ai_response.side_effect = [
            "正方AI1: 我方观点是支持...",
            "反方AI2: 我方观点是反对...",
            "正方AI1: 我方的论据是...",
            "反方AI2: 我方的反驳是...",
            "正方AI1: 我方进一步的论据是...",
            "反方AI2: 我方进一步的反驳是..."
        ]
        
        # 初始化辩论模式的ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试端到端辩论",
            rounds=6,
            time_limit=0,
            is_debate=True
        )
        
        # 验证初始化
        assert thread is not None
        assert thread.is_debate is True
        assert thread.topic == "测试端到端辩论"
        assert thread.rounds == 6

if __name__ == "__main__":
    pytest.main([__file__])
