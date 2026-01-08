# -*- coding: utf-8 -*-
"""
测试聊天历史管理功能
验证聊天历史文件在保存时会自动创建
"""

import os
import sys
import tempfile
import shutil

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.chat_history_manager import ChatHistoryManager
from utils.config_manager import get_app_data_dir

def test_chat_history_creation():
    """测试聊天历史文件创建功能"""
    print("=== 测试聊天历史文件自动创建 ===")
    
    # 获取应用数据目录
    app_data_dir = get_app_data_dir()
    print(f"应用数据目录: {app_data_dir}")
    
    # 测试文件名
    test_history_file = "test_chat_histories.json"
    test_history_path = os.path.join(app_data_dir, test_history_file)
    
    # 如果测试文件已存在，先删除
    if os.path.exists(test_history_path):
        print(f"删除已存在的测试文件: {test_history_path}")
        os.remove(test_history_path)
    
    # 验证文件不存在
    assert not os.path.exists(test_history_path), f"测试文件 {test_history_path} 应该不存在"
    print(f"✓ 测试文件 {test_history_path} 不存在，准备测试创建功能")
    
    # 创建聊天历史管理器实例
    chat_manager = ChatHistoryManager(test_history_file)
    print(f"✓ 创建了ChatHistoryManager实例，历史文件路径: {chat_manager.history_file}")
    
    # 添加一条测试聊天历史
    test_history = {
        "topic": "【测试】2024-01-01 12:00:00",
        "model1": "test_model",
        "model2": None,
        "api1": "test_api",
        "api2": "",
        "rounds": 1,
        "chat_content": "这是一条测试聊天记录",
        "start_time": "2024-01-01 12:00:00",
        "end_time": "2024-01-01 12:01:00"
    }
    
    # 保存历史记录
    print("保存测试聊天历史...")
    success = chat_manager.save_history([test_history])
    assert success, "保存聊天历史失败"
    print(f"✓ 成功保存聊天历史")
    
    # 验证文件已创建
    assert os.path.exists(test_history_path), f"测试文件 {test_history_path} 应该已创建"
    print(f"✓ 测试文件 {test_history_path} 已成功创建")
    
    # 验证文件内容
    import json
    with open(test_history_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    assert isinstance(loaded_data, list), "加载的数据应该是列表"
    assert len(loaded_data) == 1, "应该只加载了一条记录"
    assert loaded_data[0]["topic"] == test_history["topic"], "记录主题不匹配"
    print(f"✓ 测试文件内容验证成功")
    
    # 清理测试文件
    if os.path.exists(test_history_path):
        print(f"清理测试文件: {test_history_path}")
        os.remove(test_history_path)
    
    print("=== 测试完成: 聊天历史文件自动创建功能正常 ===")

if __name__ == "__main__":
    test_chat_history_creation()
