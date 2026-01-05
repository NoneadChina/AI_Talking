# -*- coding: utf-8 -*-
"""
测试聊天历史添加功能
验证通过add_history方法添加历史时会自动创建文件
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.chat_history_manager import ChatHistoryManager
from utils.config_manager import get_app_data_dir

def test_chat_history_add():
    """测试通过add_history添加历史记录时的文件创建功能"""
    print("=== 测试通过add_history添加历史记录 ===")
    
    # 获取应用数据目录
    app_data_dir = get_app_data_dir()
    print(f"应用数据目录: {app_data_dir}")
    
    # 测试文件名
    test_history_file = "test_add_chat_histories.json"
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
    
    # 使用add_history方法添加一条测试聊天历史
    print("使用add_history方法添加测试聊天历史...")
    success = chat_manager.add_history(
        func_type="聊天",
        topic="测试主题",
        model1_name="test_model",
        model2_name=None,
        api1="test_api",
        api2="",
        rounds=1,
        chat_content="这是一条通过add_history添加的测试聊天记录",
        start_time="2024-01-01 12:00:00",
        end_time="2024-01-01 12:01:00"
    )
    
    assert success, "添加聊天历史失败"
    print(f"✓ 成功通过add_history添加聊天历史")
    
    # 验证文件已创建
    assert os.path.exists(test_history_path), f"测试文件 {test_history_path} 应该已创建"
    print(f"✓ 测试文件 {test_history_path} 已成功创建")
    
    # 验证文件内容
    import json
    with open(test_history_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    assert isinstance(loaded_data, list), "加载的数据应该是列表"
    assert len(loaded_data) > 0, "应该至少加载了一条记录"
    print(f"✓ 测试文件内容验证成功，共包含 {len(loaded_data)} 条记录")
    print(f"  第一条记录主题: {loaded_data[0]['topic']}")
    
    # 清理测试文件
    if os.path.exists(test_history_path):
        print(f"清理测试文件: {test_history_path}")
        os.remove(test_history_path)
    
    print("=== 测试完成: 通过add_history添加历史记录功能正常 ===")

if __name__ == "__main__":
    test_chat_history_add()
