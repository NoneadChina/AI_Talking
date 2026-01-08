# -*- coding: utf-8 -*-
"""
UI工具类，提供UI组件的公共创建和样式设置功能
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox, QLineEdit, QComboBox, QPushButton, QLabel, QWidget
from .ui_theme import ui_theme


def create_group_box(title: str, style_sheet: str = None, style_type: str = "group_box") -> QGroupBox:
    """创建带样式的分组框

    Args:
        title: 分组框标题
        style_sheet: 样式表（兼容旧版本）
        style_type: 样式类型名称

    Returns:
        QGroupBox: 创建的分组框
    """
    group_box = QGroupBox(title)
    if style_sheet:
        group_box.setStyleSheet(style_sheet)
    else:
        ui_theme.apply_style(group_box, style_type)
    return group_box


def create_line_edit(placeholder: str = "", style_sheet: str = None, style_type: str = "line_edit") -> QLineEdit:
    """创建带样式的行编辑器

    Args:
        placeholder: 占位文本
        style_sheet: 样式表（兼容旧版本）
        style_type: 样式类型名称

    Returns:
        QLineEdit: 创建的行编辑器
    """
    line_edit = QLineEdit()
    if placeholder:
        line_edit.setPlaceholderText(placeholder)
    if style_sheet:
        line_edit.setStyleSheet(style_sheet)
    else:
        ui_theme.apply_style(line_edit, style_type)
    return line_edit


def create_combo_box(
    items: list = None, current_text: str = None, style_sheet: str = None, style_type: str = "combo_box"
) -> QComboBox:
    """创建带样式的下拉框

    Args:
        items: 下拉框选项列表
        current_text: 当前选中的文本
        style_sheet: 样式表（兼容旧版本）
        style_type: 样式类型名称

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
    else:
        ui_theme.apply_style(combo_box, style_type)
    return combo_box


def create_push_button(
    text: str, style_sheet: str = None, fixed_width: int = None, style_type: str = "history_button"
) -> QPushButton:
    """创建带样式的按钮

    Args:
        text: 按钮文本
        style_sheet: 样式表（兼容旧版本）
        fixed_width: 固定宽度
        style_type: 样式类型名称

    Returns:
        QPushButton: 创建的按钮
    """
    button = QPushButton(text)
    if style_sheet:
        button.setStyleSheet(style_sheet)
    else:
        ui_theme.apply_style(button, style_type)
    if fixed_width:
        button.setFixedWidth(fixed_width)
    return button


def create_label(
    text: str, style_sheet: str = None, alignment: Qt.AlignmentFlag = None, style_type: str = None
) -> QLabel:
    """创建带样式的标签

    Args:
        text: 标签文本
        style_sheet: 样式表（兼容旧版本）
        alignment: 对齐方式
        style_type: 样式类型名称

    Returns:
        QLabel: 创建的标签
    """
    label = QLabel(text)
    if style_sheet:
        label.setStyleSheet(style_sheet)
    elif style_type:
        ui_theme.apply_style(label, style_type)
    if alignment:
        label.setAlignment(alignment)
    return label


def get_default_styles() -> dict:
    """获取默认样式表

    Returns:
        dict: 包含各种UI组件默认样式的字典
    """
    return ui_theme.get_all_styles()


def apply_theme_to_widget(widget: QWidget, style_type: str):
    """将主题样式应用到指定组件

    Args:
        widget: 要应用样式的组件
        style_type: 样式类型名称
    """
    ui_theme.apply_style(widget, style_type)
