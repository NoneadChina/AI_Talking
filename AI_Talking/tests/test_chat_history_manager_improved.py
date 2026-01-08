# -*- coding: utf-8 -*-
"""
改进的聊天历史管理器单元测试
"""

import os
import tempfile
import json
import pytest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.chat_history_manager import ChatHistoryManager, ChatHistoryItem


class TestChatHistoryManager:
    """
    测试聊天历史管理器
    """
    
    def setup_method(self):
        """
        每个测试方法前的设置
        """
        # 创建临时文件用于测试
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        # 创建ChatHistoryManager实例
        self.manager = ChatHistoryManager(self.temp_file_path)
    
    def teardown_method(self):
        """
        每个测试方法后的清理
        """
        # 删除临时文件
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
    
    def test_initialization(self):
        """
        测试初始化
        """
        assert self.manager.history_file == self.temp_file_path
        assert self.manager.max_history_size == 1000
        assert self.manager._history_cache == []
        assert self.manager.chat_histories == []
        assert self.manager._is_cache_loaded is False
    
    def test_generate_formatted_topic(self):
        """
        测试生成格式化主题
        """
        # 测试聊天主题
        chat_topic = self.manager.generate_formatted_topic("聊天")
        assert "【" in chat_topic  # 只检查有格式化标记，不依赖具体翻译
        assert "】" in chat_topic
        
        # 测试讨论主题
        discussion_topic = self.manager.generate_formatted_topic("讨论", "测试主题")
        assert "【" in discussion_topic
        assert "】" in discussion_topic
        assert "测试主题" in discussion_topic
        
        # 测试辩论主题
        debate_topic = self.manager.generate_formatted_topic("辩论", "测试主题")
        assert "【" in debate_topic
        assert "】" in debate_topic
        assert "测试主题" in debate_topic
        
        # 测试批量主题
        batch_topic = self.manager.generate_formatted_topic("批量", "测试主题")
        assert "【" in batch_topic
        assert "】" in batch_topic
        assert "测试主题" in batch_topic
    
    def test_add_history_chat(self):
        """
        测试添加聊天历史
        """
        # 添加聊天历史
        result = self.manager.add_history(
            func_type="聊天",
            topic="测试聊天",
            model1_name="test-model-1",
            model2_name=None,
            api1="test-api-1",
            api2="",
            rounds=1,
            chat_content="测试聊天内容",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        assert result is True
        assert len(self.manager._history_cache) == 1
        assert len(self.manager.chat_histories) == 1
        
        # 测试添加相同模型的聊天历史（应该更新现有记录）
        result = self.manager.add_history(
            func_type="聊天",
            topic="测试聊天更新",
            model1_name="test-model-1",
            model2_name=None,
            api1="test-api-1",
            api2="",
            rounds=2,
            chat_content="测试聊天内容更新",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        assert result is True
        assert len(self.manager._history_cache) == 1  # 应该还是1条记录
        assert len(self.manager.chat_histories) == 1
        # 聊天主题格式只包含时间，不包含原始主题内容，所以不检查原始主题
        assert self.manager._history_cache[0]["rounds"] == 2
        assert "测试聊天内容更新" in self.manager._history_cache[0]["chat_content"]
    
    def test_add_history_discussion(self):
        """
        测试添加讨论历史
        """
        # 添加讨论历史
        result = self.manager.add_history(
            func_type="讨论",
            topic="测试讨论",
            model1_name="test-model-1",
            model2_name="test-model-2",
            api1="test-api-1",
            api2="test-api-2",
            rounds=3,
            chat_content="测试讨论内容",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        assert result is True
        assert len(self.manager._history_cache) == 1
        assert len(self.manager.chat_histories) == 1
        
        # 测试添加另一条讨论历史（应该添加新记录）
        result = self.manager.add_history(
            func_type="讨论",
            topic="测试讨论2",
            model1_name="test-model-1",
            model2_name="test-model-2",
            api1="test-api-1",
            api2="test-api-2",
            rounds=2,
            chat_content="测试讨论内容2",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        assert result is True
        assert len(self.manager._history_cache) == 2  # 应该是2条记录
        assert len(self.manager.chat_histories) == 2
    
    def test_get_history_by_topic(self):
        """
        测试根据主题获取历史记录
        """
        # 添加聊天历史
        self.manager.add_history(
            func_type="聊天",
            topic="测试聊天",
            model1_name="test-model-1",
            model2_name=None,
            api1="test-api-1",
            api2="",
            rounds=1,
            chat_content="测试聊天内容",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 获取历史记录
        history = self.manager.get_history_by_topic(self.manager._history_cache[0]["topic"])
        assert history is not None
        assert "测试聊天内容" in history["chat_content"]
        
        # 测试获取不存在的主题
        history = self.manager.get_history_by_topic("不存在的主题")
        assert history is None
    
    def test_clear_history(self):
        """
        测试清空历史记录
        """
        # 添加聊天历史
        self.manager.add_history(
            func_type="聊天",
            topic="测试聊天",
            model1_name="test-model-1",
            model2_name=None,
            api1="test-api-1",
            api2="",
            rounds=1,
            chat_content="测试聊天内容",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        assert len(self.manager._history_cache) == 1
        
        # 清空历史记录
        result = self.manager.clear_history()
        assert result is True
        assert len(self.manager._history_cache) == 0
        assert len(self.manager.chat_histories) == 0
    
    def test_save_and_load_history(self):
        """
        测试保存和加载历史记录
        """
        # 添加聊天历史
        self.manager.add_history(
            func_type="聊天",
            topic="测试聊天",
            model1_name="test-model-1",
            model2_name=None,
            api1="test-api-1",
            api2="",
            rounds=1,
            chat_content="测试聊天内容",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 保存历史记录
        result = self.manager.save_history()
        assert result is True
        
        # 创建新的ChatHistoryManager实例，测试加载
        new_manager = ChatHistoryManager(self.temp_file_path)
        new_manager.load_history()
        
        assert len(new_manager._history_cache) == 1
        assert len(new_manager.chat_histories) == 1
        assert "测试聊天内容" in new_manager._history_cache[0]["chat_content"]
    
    def test_get_history_page(self):
        """
        测试分页获取历史记录
        """
        # 添加多条历史记录
        for i in range(25):
            self.manager.add_history(
                func_type="讨论",
                topic=f"测试讨论{i}",
                model1_name="test-model-1",
                model2_name="test-model-2",
                api1="test-api-1",
                api2="test-api-2",
                rounds=3,
                chat_content=f"测试讨论内容{i}",
                start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        
        # 获取第一页（20条）
        page1 = self.manager.get_history_page(page=1, page_size=20)
        assert len(page1) == 20
        
        # 获取第二页（5条）
        page2 = self.manager.get_history_page(page=2, page_size=20)
        assert len(page2) == 5
        
        # 获取第3页（0条，超出范围）
        page3 = self.manager.get_history_page(page=3, page_size=20)
        assert len(page3) == 0
    
    def test_get_history_count(self):
        """
        测试获取历史记录总数
        """
        # 初始计数为0
        count = self.manager.get_history_count()
        assert count == 0
        
        # 添加历史记录
        self.manager.add_history(
            func_type="聊天",
            topic="测试聊天",
            model1_name="test-model-1",
            model2_name=None,
            api1="test-api-1",
            api2="",
            rounds=1,
            chat_content="测试聊天内容",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 计数应为1
        count = self.manager.get_history_count()
        assert count == 1
    
    def test_prune_old_history(self):
        """
        测试修剪旧历史记录
        """
        # 调整max_history_size为5，便于测试
        self.manager.max_history_size = 5
        
        # 添加6条历史记录
        for i in range(6):
            self.manager.add_history(
                func_type="讨论",
                topic=f"测试讨论{i}",
                model1_name="test-model-1",
                model2_name="test-model-2",
                api1="test-api-1",
                api2="test-api-2",
                rounds=3,
                chat_content=f"测试讨论内容{i}",
                start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        
        # 保存并重新加载，触发修剪
        self.manager.save_history()
        
        # 应该只有5条记录
        assert len(self.manager._history_cache) == 5
        assert len(self.manager.chat_histories) == 5
