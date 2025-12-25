# -*- coding: utf-8 -*-
"""
AI配置面板组件，用于配置AI参数
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout


class AIConfigPanel(QWidget):
    """
    AI配置面板组件，用于配置AI参数
    """

    def __init__(self, api_settings_widget=None):
        """
        初始化AI配置面板

        Args:
            api_settings_widget: API设置组件，用于获取API配置
        """
        super().__init__()
        self.api_settings_widget = api_settings_widget
        self.init_ui()

    def init_ui(self):
        """
        初始化AI配置面板UI
        """
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 当前没有需要更新的UI元素，保留空方法以保持一致性
        pass
