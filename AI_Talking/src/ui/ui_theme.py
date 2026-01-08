# -*- coding: utf-8 -*-
"""
UI主题管理模块，负责统一管理所有UI组件的样式

该模块提供了统一的样式管理，确保所有UI组件的样式一致，便于维护和主题切换。
"""

from PyQt5.QtWidgets import QWidget
from typing import Dict, Any


class UITheme:
    """
    UI主题管理类，负责统一管理所有UI组件的样式
    
    设计目的：
    1. 提供统一的样式管理，确保所有UI组件的样式一致
    2. 支持动态切换主题，便于维护和扩展
    3. 提供默认样式，简化组件开发
    4. 支持自定义样式，满足个性化需求
    
    使用方式：
    - 通过全局实例ui_theme访问主题管理功能
    - 使用apply_style方法将样式应用到组件
    - 使用set_style方法自定义组件样式
    - 使用reset_to_default方法恢复默认样式
    """
    
    # 默认主题样式定义
    # 采用现代化的扁平化设计，使用柔和的颜色和圆角
    _default_styles = {
        "group_box": """QGroupBox {
            font-weight: bold;
            font-size: 10pt;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }""",
        
        "sub_group_box": """QGroupBox {
            font-weight: normal;
            font-size: 10pt;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            margin-top: 5px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }""",
        
        "line_edit": """QLineEdit {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 10pt;
        }
        QLineEdit:focus {
            border-color: #4caf50;
            outline: none;
        }""",
        
        "combo_box": """QComboBox {
            font-size: 9pt;
            padding: 4px;
            border: 1px solid #ddd;
            border-radius: 6px;
        }
        QComboBox::item:selected {
            background-color: rgba(0, 0, 0, 0.15);
            color: black;
        }
        QComboBox::drop-down {
            border: 0px;
        }""",
        
        "spin_box": "font-size: 9pt; padding: 4px; border: 1px solid #ddd; border-radius: 6px;",
        
        "history_button": """QPushButton {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background-color: #f5f5f5;
            font-size: 9pt;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }""",
        
        "start_button": """QPushButton {
            padding: 9px 20px;
            border: none;
            border-radius: 6px;
            font-size: 10pt;
            font-weight: bold;
            background-color: #4caf50;
            color: white;
        }
        QPushButton:hover {
            background-color: #43a047;
        }""",
        
        "stop_button": """QPushButton {
            padding: 9px 20px;
            border: none;
            border-radius: 6px;
            font-size: 10pt;
            font-weight: bold;
            background-color: #f44336;
            color: white;
        }
        QPushButton:hover {
            background-color: #e53935;
        }""",
        
        "status_label": """QLabel {
            font-weight: bold;
            color: #2e7d32;
            padding: 8px 12px;
            background-color: #e8f5e8;
            border: 1px solid #c8e6c9;
            border-radius: 6px;
        }""",
        
        "message_user": """QWidget {
            background-color: #e8f5e8;
            border: 1px solid #c8e6c9;
            border-radius: 18px;
            border-bottom-right-radius: 4px;
            padding: 15px;
            margin: 4px 0;
        }""",
        
        "message_ai": """QWidget {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            padding: 15px;
            margin: 4px 0;
        }""",
        
        "message_system": """QWidget {
            background-color: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 12px;
            padding: 12px;
            margin: 15px auto;
            text-align: center;
            font-weight: bold;
            max-width: 60%;
            color: #1565c0;
        }""",
    }
    
    def __init__(self):
        """
        初始化UI主题管理器
        
        初始化时加载默认样式，创建当前样式字典
        """
        # 创建当前样式字典，初始化为默认样式的副本
        self._current_styles = self._default_styles.copy()
    
    def get_style(self, component_type: str) -> str:
        """
        获取指定组件类型的样式
        
        Args:
            component_type: 组件类型名称，如"group_box"、"button"等
            
        Returns:
            str: 组件样式表字符串，若未找到则返回空字符串
        """
        return self._current_styles.get(component_type, "")
    
    def set_style(self, component_type: str, style: str):
        """
        设置指定组件类型的样式
        
        Args:
            component_type: 组件类型名称
            style: 组件样式表字符串，支持完整的CSS语法
        """
        self._current_styles[component_type] = style
    
    def apply_style(self, widget: QWidget, component_type: str):
        """
        将样式应用到指定组件
        
        Args:
            widget: 要应用样式的PyQt5组件实例
            component_type: 组件类型名称，用于查找对应的样式表
        """
        # 获取组件类型对应的样式
        style = self.get_style(component_type)
        # 只有当样式不为空时才应用
        if style:
            widget.setStyleSheet(style)
    
    def reset_to_default(self):
        """
        重置所有样式为默认值
        
        将当前样式字典恢复为初始的默认样式
        """
        self._current_styles = self._default_styles.copy()
    
    def get_all_styles(self) -> Dict[str, str]:
        """
        获取所有样式的副本
        
        Returns:
            Dict[str, str]: 包含所有组件类型及其对应样式的字典副本
        """
        # 返回当前样式字典的副本，避免外部直接修改内部状态
        return self._current_styles.copy()


# 创建全局UI主题实例
ui_theme = UITheme()
