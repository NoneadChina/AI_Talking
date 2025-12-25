import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_gui import ChatThread
from chat_between_ais import AIChatManager

class TestChatThread:
    """测试ChatThread类的功能"""
    
    def test_init(self):
        """测试ChatThread初始化"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试主题",
            rounds=5,
            time_limit=0
        )
        
        # 验证初始化
        assert thread is not None
        assert thread.topic == "测试主题"
        assert thread.rounds == 5
        assert thread.time_limit == 0
        assert not thread.is_stopped()
        assert thread.manager == mock_manager
    
    def test_init_with_debate_mode(self):
        """测试辩论模式的ChatThread初始化"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化辩论模式的ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试辩论主题",
            rounds=3,
            time_limit=10,
            is_debate=True
        )
        
        # 验证初始化
        assert thread is not None
        assert thread.topic == "测试辩论主题"
        assert thread.rounds == 3
        assert thread.time_limit == 10
        assert thread.is_debate is True
        assert not thread.is_stopped()
    
    def test_stop(self):
        """测试线程停止功能"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试主题",
            rounds=5,
            time_limit=0
        )
        
        # 验证初始状态
        assert not thread.is_stopped()
        
        # 测试停止功能
        thread.stop()
        assert thread.is_stopped()
        
        # 多次调用stop()应该不会出错
        thread.stop()
        assert thread.is_stopped()
    
    def test_is_stopped(self):
        """测试is_stopped方法"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试主题",
            rounds=5,
            time_limit=0
        )
        
        # 验证初始状态
        assert thread.is_stopped() is False
        
        # 测试停止后状态
        thread.stop()
        assert thread.is_stopped() is True
    
    def test_resource_cleanup(self):
        """测试资源清理功能"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试主题",
            rounds=5,
            time_limit=0
        )
        
        # 模拟设置一些资源
        thread.messages1 = [{"role": "user", "content": "测试消息"}]
        thread.messages2 = [{"role": "assistant", "content": "测试响应"}]
        thread.ai2_history = [{"role": "system", "content": "系统提示"}]
        
        # 调用资源清理方法
        thread._cleanup_resources()
        
        # 验证资源已清理（_cleanup_resources方法将属性设置为None或清空，而不是删除它们）
        assert thread.messages1 is None or thread.messages1 == []
        assert thread.messages2 is None or thread.messages2 == []
        assert thread.ai2_history is None or thread.ai2_history == []
    
    def test___del__(self):
        """测试析构函数"""
        # 注意：在Python中，析构函数的调用时机是不确定的，因为它依赖于垃圾回收机制
        # 所以这个测试只验证析构函数的逻辑，而不验证它是否被自动调用
        
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试主题",
            rounds=5,
            time_limit=0
        )
        
        # 模拟设置一些资源
        thread.messages1 = [{"role": "user", "content": "测试消息"}]
        thread.messages2 = [{"role": "assistant", "content": "测试响应"}]
        
        # 直接测试析构函数的逻辑（调用清理资源方法）
        # 而不是依赖于del语句自动调用析构函数
        cleanup_mock = MagicMock()
        thread._cleanup_resources = cleanup_mock
        
        # 手动调用析构函数
        thread.__del__()
        
        # 验证资源清理方法被调用
        cleanup_mock.assert_called_once()
    
    @patch('chat_gui.ChatThread.run')
    def test_start_stop_behavior(self, mock_run):
        """测试线程启动和停止行为"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试主题",
            rounds=5,
            time_limit=0
        )
        
        # 启动线程
        thread.start()
        
        # 验证线程状态
        assert thread.isRunning() is True
        
        # 停止线程
        thread.stop()
        
        # 等待线程结束
        thread.wait()
        
        # 验证线程已停止
        assert thread.isFinished() is True
        assert thread.is_stopped() is True
    
    def test_signal_connections(self):
        """测试信号连接"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread
        thread = ChatThread(
            manager=mock_manager,
            topic="测试主题",
            rounds=5,
            time_limit=0
        )
        
        # 验证信号存在
        assert hasattr(thread, 'update_signal')
        assert hasattr(thread, 'status_signal')
        assert hasattr(thread, 'finished_signal')
        assert hasattr(thread, 'error_signal')
        
        # 测试信号连接
        update_called = threading.Event()
        status_called = threading.Event()
        finished_called = threading.Event()
        error_called = threading.Event()
        
        def on_update(sender, content):
            update_called.set()
        
        def on_status(status):
            status_called.set()
        
        def on_finished():
            finished_called.set()
        
        def on_error(error):
            error_called.set()
        
        # 连接信号
        thread.update_signal.connect(on_update)
        thread.status_signal.connect(on_status)
        thread.finished_signal.connect(on_finished)
        thread.error_signal.connect(on_error)
        
        # 触发信号
        thread.update_signal.emit("AI1", "测试响应")
        thread.status_signal.emit("测试状态")
        thread.finished_signal.emit()
        thread.error_signal.emit("测试错误")
        
        # 验证信号被处理
        assert update_called.is_set()
        assert status_called.is_set()
        assert finished_called.is_set()
        assert error_called.is_set()
    
    @patch('chat_gui.ChatThread.run')
    def test_thread_id(self, mock_run):
        """测试线程ID"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化两个不同的ChatThread实例
        thread1 = ChatThread(
            manager=mock_manager,
            topic="测试主题1",
            rounds=5,
            time_limit=0
        )
        
        thread2 = ChatThread(
            manager=mock_manager,
            topic="测试主题2",
            rounds=3,
            time_limit=0
        )
        
        # 启动线程
        thread1.start()
        thread2.start()
        
        # 等待线程启动
        time.sleep(0.1)
        
        # 验证线程ID不同
        assert thread1.currentThreadId() != thread2.currentThreadId()
        
        # 停止线程
        thread1.stop()
        thread2.stop()
        thread1.wait()
        thread2.wait()
    
    def test_time_limit(self):
        """测试时间限制功能"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 初始化ChatThread，设置时间限制为1秒
        thread = ChatThread(
            manager=mock_manager,
            topic="测试主题",
            rounds=5,
            time_limit=1  # 1秒时间限制
        )
        
        # 验证时间限制设置
        assert thread.time_limit == 1
    
    @patch('chat_gui.ChatThread.run')
    def test_multiple_threads(self, mock_run):
        """测试多个ChatThread实例"""
        # 创建模拟的AIChatManager
        mock_manager = MagicMock(spec=AIChatManager)
        
        # 创建多个ChatThread实例
        threads = []
        for i in range(3):
            thread = ChatThread(
                manager=mock_manager,
                topic=f"测试主题{i}",
                rounds=3,
                time_limit=0
            )
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 验证所有线程都在运行
        for thread in threads:
            assert thread.isRunning() is True
        
        # 停止所有线程
        for thread in threads:
            thread.stop()
        
        # 等待所有线程结束
        for thread in threads:
            thread.wait()
        
        # 验证所有线程都已停止
        for thread in threads:
            assert thread.isFinished() is True
            assert thread.is_stopped() is True

if __name__ == "__main__":
    pytest.main([__file__])
