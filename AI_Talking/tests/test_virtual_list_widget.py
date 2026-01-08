# -*- coding: utf-8 -*-
"""
虚拟列表组件测试
"""

import unittest
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt
from src.ui.virtual_list_widget import VirtualListWidget


class TestVirtualListWidget(unittest.TestCase):
    """
    测试虚拟列表组件的功能
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
        self.virtual_list = VirtualListWidget()
        self.virtual_list.set_item_height(50)
        
        # 设置简单的渲染函数
        def simple_renderer(data, index):
            widget = QWidget()
            label = QLabel(f"Item {index}: {data}", widget)
            label.setGeometry(0, 0, 200, 50)
            return widget
        
        self.virtual_list.set_item_renderer(simple_renderer)
    
    def test_init(self):
        """
        测试虚拟列表的初始化
        """
        self.assertIsNotNone(self.virtual_list)
        self.assertEqual(self.virtual_list._item_height, 50)
        self.assertEqual(len(self.virtual_list._data), 0)
    
    def test_set_data(self):
        """
        测试设置数据功能
        """
        test_data = [f"Data {i}" for i in range(100)]
        self.virtual_list.set_data(test_data)
        
        self.assertEqual(len(self.virtual_list._data), 100)
        self.assertEqual(self.virtual_list._total_height, 100 * 50)  # 100个项目，每个50高度
    
    def test_set_item_height(self):
        """
        测试设置项目高度功能
        """
        self.virtual_list.set_item_height(100)
        self.assertEqual(self.virtual_list._item_height, 100)
        
        # 设置数据并验证总高度
        test_data = [f"Data {i}" for i in range(50)]
        self.virtual_list.set_data(test_data)
        self.assertEqual(self.virtual_list._total_height, 50 * 100)  # 50个项目，每个100高度
    
    def test_render_visible_items(self):
        """
        测试渲染可见项目功能
        """
        test_data = [f"Data {i}" for i in range(100)]
        self.virtual_list.set_data(test_data)
        
        # 设置滚动区域大小
        self.virtual_list.resize(800, 600)
        
        # 模拟滚动位置
        self.virtual_list._scroll_pos = 0
        self.virtual_list._render_visible_items()
        
        # 获取可见项目数量
        visible_items = self.virtual_list.get_visible_items()
        # 可见区域高度600，每个项目50高度，加上缓冲5个，应该有12+10=22个左右
        self.assertGreater(len(visible_items), 0)
        self.assertLess(len(visible_items), 30)  # 应该远小于总项目数100
    
    def test_on_scroll(self):
        """
        测试滚动事件处理
        """
        test_data = [f"Data {i}" for i in range(100)]
        self.virtual_list.set_data(test_data)
        
        # 模拟滚动到位置1000
        self.virtual_list._on_scroll(1000)
        self.assertEqual(self.virtual_list._scroll_pos, 1000)
        
        # 验证可见项目数量
        visible_items = self.virtual_list.get_visible_items()
        self.assertGreater(len(visible_items), 0)
    
    def test_clear(self):
        """
        测试清空列表功能
        """
        test_data = [f"Data {i}" for i in range(100)]
        self.virtual_list.set_data(test_data)
        self.virtual_list.clear()
        
        self.assertEqual(len(self.virtual_list._data), 0)
        self.assertEqual(self.virtual_list._total_height, 0)
        self.assertEqual(len(self.virtual_list.get_visible_items()), 0)
    
    def test_item_clicked_signal(self):
        """
        测试项目点击信号
        """
        clicked_index = -1
        
        def on_item_clicked(index):
            nonlocal clicked_index
            clicked_index = index
        
        self.virtual_list.item_clicked.connect(on_item_clicked)
        
        # 模拟点击信号发射
        self.virtual_list.item_clicked.emit(5)
        self.assertEqual(clicked_index, 5)
    
    def test_resize_event(self):
        """
        测试窗口大小变化事件
        """
        test_data = [f"Data {i}" for i in range(100)]
        self.virtual_list.set_data(test_data)
        
        # 直接修改滚动区域的可见高度来测试
        # 保存原始的viewport size方法
        original_viewport_size = self.virtual_list.scroll_area.viewport().size
        
        try:
            # 设置小的可见高度
            from PyQt5.QtCore import QSize
            self.virtual_list.scroll_area.viewport().size = lambda: QSize(800, 300)
            self.virtual_list._scroll_pos = 0
            self.virtual_list._render_visible_items()
            
            # 记录初始可见项目数量
            initial_visible = len(self.virtual_list.get_visible_items())
            
            # 设置大的可见高度
            self.virtual_list.scroll_area.viewport().size = lambda: QSize(800, 1000)
            self.virtual_list._render_visible_items()
            
            # 验证可见项目数量变化
            new_visible = len(self.virtual_list.get_visible_items())
            self.assertGreater(new_visible, initial_visible)  # 可见高度变大，可见项目应该更多
        finally:
            # 恢复原始方法
            self.virtual_list.scroll_area.viewport().size = original_viewport_size


if __name__ == '__main__':
    unittest.main()
