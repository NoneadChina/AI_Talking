# -*- coding: utf-8 -*-
"""
UI主题系统测试
"""

import unittest
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication
from src.ui.ui_theme import UITheme, ui_theme


class TestUITheme(unittest.TestCase):
    """
    测试UI主题系统的功能
    """
    
    @classmethod
    def setUpClass(cls):
        """
        类级别的测试前设置
        """
        cls.app = QApplication([])
    
    @classmethod
    def tearDownClass(cls):
        """
        类级别的测试后清理
        """
        cls.app.quit()
    
    def setUp(self):
        """
        每个测试方法前的设置
        """
        self.theme = UITheme()
        self.test_widget = QWidget()
    
    def test_init(self):
        """
        测试主题管理器的初始化
        """
        self.assertIsNotNone(self.theme)
        self.assertIsInstance(self.theme, UITheme)
        self.assertGreater(len(self.theme._current_styles), 0)
    
    def test_get_style(self):
        """
        测试获取样式功能
        """
        # 测试获取默认样式
        group_box_style = self.theme.get_style("group_box")
        self.assertIsInstance(group_box_style, str)
        self.assertGreater(len(group_box_style), 0)
        
        # 测试获取不存在的样式
        non_existent_style = self.theme.get_style("non_existent_style")
        self.assertEqual(non_existent_style, "")
    
    def test_set_style(self):
        """
        测试设置样式功能
        """
        # 保存原始样式
        original_style = self.theme.get_style("group_box")
        
        # 设置新样式
        new_style = "QGroupBox { background-color: red; }"
        self.theme.set_style("group_box", new_style)
        
        # 验证样式已更新
        self.assertEqual(self.theme.get_style("group_box"), new_style)
        
        # 测试设置新的组件类型样式
        self.theme.set_style("custom_style", "QWidget { color: blue; }")
        self.assertEqual(self.theme.get_style("custom_style"), "QWidget { color: blue; }")
    
    def test_apply_style(self):
        """
        测试应用样式功能
        """
        # 创建测试按钮
        test_button = QPushButton()
        
        # 应用样式
        self.theme.apply_style(test_button, "start_button")
        
        # 验证样式已应用
        button_style = test_button.styleSheet()
        self.assertIsInstance(button_style, str)
        self.assertGreater(len(button_style), 0)
    
    def test_reset_to_default(self):
        """
        测试重置样式为默认值功能
        """
        # 修改样式
        self.theme.set_style("group_box", "QGroupBox { background-color: red; }")
        self.theme.set_style("custom_style", "QWidget { color: blue; }")
        
        # 重置为默认值
        self.theme.reset_to_default()
        
        # 验证内置样式已重置
        default_group_box_style = UITheme().get_style("group_box")
        self.assertEqual(self.theme.get_style("group_box"), default_group_box_style)
        
        # 验证自定义样式已被移除
        self.assertEqual(self.theme.get_style("custom_style"), "")
    
    def test_get_all_styles(self):
        """
        测试获取所有样式功能
        """
        all_styles = self.theme.get_all_styles()
        self.assertIsInstance(all_styles, dict)
        self.assertGreater(len(all_styles), 0)
        
        # 验证返回的是副本
        all_styles["group_box"] = "modified"
        self.assertNotEqual(self.theme.get_style("group_box"), "modified")
    
    def test_global_theme_instance(self):
        """
        测试全局主题实例
        """
        self.assertIsNotNone(ui_theme)
        self.assertIsInstance(ui_theme, UITheme)
        
        # 测试全局实例的功能
        global_group_box_style = ui_theme.get_style("group_box")
        self.assertIsInstance(global_group_box_style, str)
        self.assertGreater(len(global_group_box_style), 0)
    
    def test_style_consistency(self):
        """
        测试样式一致性
        """
        # 创建两个主题实例，验证默认样式一致
        theme1 = UITheme()
        theme2 = UITheme()
        
        for style_type in theme1._current_styles:
            self.assertEqual(theme1.get_style(style_type), theme2.get_style(style_type))
    
    def test_different_component_styles(self):
        """
        测试不同组件类型的样式
        """
        # 验证不同组件类型有不同的样式
        start_button_style = self.theme.get_style("start_button")
        stop_button_style = self.theme.get_style("stop_button")
        message_ai_style = self.theme.get_style("message_ai")
        
        self.assertNotEqual(start_button_style, stop_button_style)
        self.assertNotEqual(stop_button_style, message_ai_style)
        self.assertNotEqual(message_ai_style, start_button_style)


if __name__ == '__main__':
    unittest.main()
