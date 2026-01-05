# -*- coding: utf-8 -*-
"""
测试配置文件路径选择逻辑
验证调试阶段和发布阶段使用不同的配置文件路径
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.config_manager import ConfigManager, get_app_data_dir

def test_config_path_selection():
    """测试配置文件路径选择逻辑"""
    print("=== 测试配置文件路径选择逻辑 ===")
    
    # 获取预期的路径
    project_root = os.path.abspath(os.path.dirname(__file__))
    expected_debug_path = os.path.join(project_root, 'config.yaml')
    expected_release_path = os.path.join(get_app_data_dir(), 'config.yaml')
    
    print(f"项目根目录: {project_root}")
    print(f"预期调试路径: {expected_debug_path}")
    print(f"预期发布路径: {expected_release_path}")
    print("\n1. 测试调试阶段配置文件路径...")
    
    # 1. 测试调试阶段（正常运行Python脚本时）
    config_manager = ConfigManager()
    actual_debug_path = config_manager.config_file_path
    print(f"实际调试路径: {actual_debug_path}")
    
    # 验证路径是否正确
    assert actual_debug_path == expected_debug_path, f"调试阶段路径错误: 预期 {expected_debug_path}, 实际 {actual_debug_path}"
    print(f"✓ 调试阶段正确使用项目根目录下的配置文件")
    
    # 2. 测试发布阶段（模拟frozen环境）
    print("\n2. 测试发布阶段配置文件路径...")
    
    # 保存原始的frozen属性
    original_frozen = getattr(sys, 'frozen', None)
    
    try:
        # 模拟发布环境
        sys.frozen = True
        
        # 创建新的ConfigManager实例
        config_manager_release = ConfigManager()
        actual_release_path = config_manager_release.config_file_path
        print(f"实际发布路径: {actual_release_path}")
        
        # 验证路径是否正确
        assert actual_release_path == expected_release_path, f"发布阶段路径错误: 预期 {expected_release_path}, 实际 {actual_release_path}"
        print(f"✓ 发布阶段正确使用用户目录下的配置文件")
        
    finally:
        # 恢复原始的frozen属性
        if original_frozen is None:
            delattr(sys, 'frozen')
        else:
            sys.frozen = original_frozen
    
    # 3. 验证配置文件是否存在或能正确创建
    print("\n3. 验证配置文件访问...")
    
    # 测试加载和保存配置
    test_value = "test_config_value"
    config_manager.set("test_key", test_value)
    saved_value = config_manager.get("test_key")
    assert saved_value == test_value, f"配置保存/读取失败: 预期 {test_value}, 实际 {saved_value}"
    print(f"✓ 配置文件可以正常读取和写入")
    
    print("\n=== 测试完成: 配置文件路径选择逻辑正常 ===")
    print("  - 调试阶段: 使用项目根目录下的config.yaml")
    print("  - 发布阶段: 使用用户目录下的AI_Talking\config.yaml")

if __name__ == "__main__":
    test_config_path_selection()
