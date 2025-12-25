# -*- coding: utf-8 -*-
"""
UI工具类，提供UI组件的公共创建和样式设置功能
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox, QLineEdit, QComboBox, QPushButton, QLabel


def create_group_box(title: str, style_sheet: str = None) -> QGroupBox:
    """创建带样式的分组框

    Args:
        title: 分组框标题
        style_sheet: 样式表

    Returns:
        QGroupBox: 创建的分组框
    """
    group_box = QGroupBox(title)
    if style_sheet:
        group_box.setStyleSheet(style_sheet)
    return group_box


def create_line_edit(placeholder: str = "", style_sheet: str = None) -> QLineEdit:
    """创建带样式的行编辑器

    Args:
        placeholder: 占位文本
        style_sheet: 样式表

    Returns:
        QLineEdit: 创建的行编辑器
    """
    line_edit = QLineEdit()
    if placeholder:
        line_edit.setPlaceholderText(placeholder)
    if style_sheet:
        line_edit.setStyleSheet(style_sheet)
    return line_edit


def create_combo_box(
    items: list = None, current_text: str = None, style_sheet: str = None
) -> QComboBox:
    """创建带样式的下拉框

    Args:
        items: 下拉框选项列表
        current_text: 当前选中的文本
        style_sheet: 样式表

    Returns:
        QComboBox: 创建的下拉框
    """
    combo_box = QComboBox()
    if items:
        combo_box.addItems(items)
    if current_text:
        combo_box.setCurrentText(current_text)
    if style_sheet:
        combo_box.setStyleSheet(style_sheet)
    return combo_box


def create_push_button(
    text: str, style_sheet: str = None, fixed_width: int = None
) -> QPushButton:
    """创建带样式的按钮

    Args:
        text: 按钮文本
        style_sheet: 样式表
        fixed_width: 固定宽度

    Returns:
        QPushButton: 创建的按钮
    """
    button = QPushButton(text)
    if style_sheet:
        button.setStyleSheet(style_sheet)
    if fixed_width:
        button.setFixedWidth(fixed_width)
    return button


def create_label(
    text: str, style_sheet: str = None, alignment: Qt.AlignmentFlag = None
) -> QLabel:
    """创建带样式的标签

    Args:
        text: 标签文本
        style_sheet: 样式表
        alignment: 对齐方式

    Returns:
        QLabel: 创建的标签
    """
    label = QLabel(text)
    if style_sheet:
        label.setStyleSheet(style_sheet)
    if alignment:
        label.setAlignment(alignment)
    return label


def get_default_styles() -> dict:
    """获取默认样式表

    Returns:
        dict: 包含各种UI组件默认样式的字典
    """
    return {
        "group_box": """QGroupBox {
            font-weight: bold;
            font-size: 11pt;
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
        "combo_box": "QComboBox { font-size: 9pt; padding: 4px; border: 1px solid #ddd; border-radius: 6px; } QComboBox::item:selected { background-color: rgba(0, 0, 0, 0.15); color: black; } QComboBox::drop-down { border: 0px; } QComboBox::down-arrow { image: url(None); width: 0px; height: 0px; }",
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
    }
