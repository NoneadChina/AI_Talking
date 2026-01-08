# -*- coding: utf-8 -*-
"""
虚拟列表使用示例

该示例展示了如何使用 VirtualListWidget 组件来高效渲染大量数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt5.QtCore import Qt
from src.ui.virtual_list_widget import VirtualListWidget
from src.ui.ui_theme import ui_theme
from src.utils.init_manager import init_manager


class ItemWidget(QWidget):
    """
    列表项组件
    """
    
    def __init__(self, data, index, parent=None):
        """
        初始化列表项组件
        
        Args:
            data: 数据项
            index: 索引
            parent: 父控件
        """
        super().__init__(parent)
        self.init_ui(data, index)
    
    def init_ui(self, data, index):
        """
        初始化UI
        
        Args:
            data: 数据项
            index: 索引
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 使用统一的UI样式
        self.label = QLabel(f"Item {index}: {data}")
        ui_theme.apply_style(self, "message_ai")
        
        layout.addWidget(self.label)


class VirtualListExample(QWidget):
    """
    虚拟列表示例窗口
    """
    
    def __init__(self, parent=None):
        """
        初始化示例窗口
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """
        初始化UI
        """
        layout = QVBoxLayout(self)
        
        # 创建标题
        title = QLabel("Virtual List Example")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title)
        
        # 创建虚拟列表
        self.virtual_list = VirtualListWidget()
        # 设置项目高度
        self.virtual_list.set_item_height(100)
        # 设置项目渲染函数
        self.virtual_list.set_item_renderer(self._render_item)
        
        layout.addWidget(self.virtual_list)
        
        # 创建按钮
        self.load_button = QPushButton("Load Large Dataset")
        self.load_button.clicked.connect(self._load_large_dataset)
        layout.addWidget(self.load_button)
        
        # 设置窗口属性
        self.setWindowTitle("Virtual List Example")
        self.resize(800, 600)
    
    def _render_item(self, data, index):
        """
        项目渲染函数
        
        Args:
            data: 数据项
            index: 索引
            
        Returns:
            QWidget: 渲染后的项目组件
        """
        return ItemWidget(data, index)
    
    def _load_large_dataset(self):
        """
        加载大数据集
        """
        # 创建大数据集
        data = [f"Data {i}" for i in range(10000)]
        
        # 使用初始化管理器来优化加载过程
        init_manager.add_task_func(
            name="Load Data",
            func=lambda: self.virtual_list.set_data(data),
            priority=1,
            blocking=False
        )
        
        # 开始初始化
        init_manager.start_initialization()


if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # 应用全局主题样式
    ui_theme.apply_style(app, "app")
    
    window = VirtualListExample()
    window.show()
    
    sys.exit(app.exec_())
