import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_gui import ChatGUI

# 用于存储全局应用实例
app = None

@pytest.fixture(scope="session")
def setup_application():
    """创建QApplication实例，用于所有测试"""
    global app
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def chat_gui(setup_application):
    """创建ChatGUI实例，用于每个测试"""
    gui = ChatGUI()
    yield gui
    gui.close()

class TestChatGUI:
    """测试ChatGUI类的功能"""
    
    def test_init(self, chat_gui):
        """测试ChatGUI初始化"""
        assert chat_gui is not None
        assert chat_gui.windowTitle() == "AI Talking - NONEAD Corporation"
        assert chat_gui.tabs is not None
        assert chat_gui.tabs.count() > 0
    
    def test_tabs(self, chat_gui):
        """测试标签页功能"""
        # 获取标签页数量
        tab_count = chat_gui.tabs.count()
        assert tab_count >= 3  # 聊天、讨论、辩论、设置
        
        # 检查标签页名称
        tab_names = [chat_gui.tabs.tabText(i) for i in range(tab_count)]
        assert "聊天" in tab_names
        assert "讨论" in tab_names
        assert "辩论" in tab_names
        assert "设置" in tab_names
    
    def test_chat_model_combo(self, chat_gui):
        """测试聊天模型下拉框"""
        # 聊天标签页的模型下拉框
        assert hasattr(chat_gui, 'chat_model_combo')
        assert chat_gui.chat_model_combo.count() > 0
        
        # 默认模型设置
        assert chat_gui.chat_model_combo.currentText() == "deepseek-v3.1:671b-cloud"
    
    def test_discussion_models(self, chat_gui):
        """测试讨论模式的模型设置"""
        assert hasattr(chat_gui, 'model1_combo')
        assert hasattr(chat_gui, 'model2_combo')
        
        # 默认模型设置
        assert chat_gui.model1_combo.currentText() == "deepseek-v3.1:671b-cloud"
        assert chat_gui.model2_combo.currentText() == "qwen3-vl:235b-instruct-cloud"
    
    def test_debate_models(self, chat_gui):
        """测试辩论模式的模型设置"""
        assert hasattr(chat_gui, 'debate_model1_combo')
        assert hasattr(chat_gui, 'debate_model2_combo')
        
        # 默认模型设置
        assert chat_gui.debate_model1_combo.currentText() == "deepseek-v3.1:671b-cloud"
        assert chat_gui.debate_model2_combo.currentText() == "qwen3-vl:235b-instruct-cloud"
    
    def test_model_combo_width(self, chat_gui):
        """测试模型下拉框宽度设置"""
        # 模型下拉框宽度应为250px
        assert chat_gui.chat_model_combo.width() >= 250
        assert chat_gui.model1_combo.width() >= 250
        assert chat_gui.model2_combo.width() >= 250
        assert chat_gui.debate_model1_combo.width() >= 250
        assert chat_gui.debate_model2_combo.width() >= 250
    
    def test_chat_thread_initialization(self, chat_gui):
        """测试聊天线程初始化"""
        from chat_gui import ChatThread
        
        # 创建聊天线程实例
        thread = ChatThread(
            manager=None, 
            topic="测试主题", 
            rounds=3, 
            time_limit=0
        )
        
        assert thread is not None
        assert thread.topic == "测试主题"
        assert thread.rounds == 3
        assert thread.time_limit == 0
        assert not thread.is_stopped()
        
        # 测试线程停止功能
        thread.stop()
        assert thread.is_stopped()
    
    def test_temperature_spinbox(self, chat_gui):
        """测试温度调节功能"""
        # 聊天标签页的温度调节
        assert hasattr(chat_gui, 'chat_temperature_spin')
        assert chat_gui.chat_temperature_spin.value() == 0.8
        assert chat_gui.chat_temperature_spin.minimum() == 0.0
        assert chat_gui.chat_temperature_spin.maximum() == 2.0
        
        # 讨论标签页的温度调节
        assert hasattr(chat_gui, 'temp_spin')
        assert chat_gui.temp_spin.value() == 0.8
        
        # 辩论标签页的温度调节
        assert hasattr(chat_gui, 'debate_temp_spin')
        assert chat_gui.debate_temp_spin.value() == 0.8
    
    def test_rounds_spinbox(self, chat_gui):
        """测试轮数调节功能"""
        # 讨论标签页的轮数调节
        assert hasattr(chat_gui, 'rounds_spin')
        assert chat_gui.rounds_spin.value() == 5
        assert chat_gui.rounds_spin.minimum() == 1
        
        # 辩论标签页的轮数调节
        assert hasattr(chat_gui, 'debate_rounds_spin')
        assert chat_gui.debate_rounds_spin.value() == 5
        assert chat_gui.debate_rounds_spin.minimum() == 1

if __name__ == "__main__":
    pytest.main([__file__])
