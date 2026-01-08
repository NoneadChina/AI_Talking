# -*- coding: utf-8 -*-
"""
虚拟列表组件，用于高效渲染大量数据

该组件实现了虚拟滚动功能，只渲染可见区域内的项目，从而提高长列表的渲染性能。
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLayout
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from typing import List, Callable, Any


class VirtualListWidget(QWidget):
    """
    虚拟列表组件，用于高效渲染大量数据
    
    该组件实现了虚拟滚动功能，只渲染可见区域内的项目，从而提高长列表的渲染性能。
    通过缓冲机制减少滚动时的闪烁，支持自定义项目渲染函数和动态调整项目高度。
    """
    
    # 信号定义
    item_clicked = pyqtSignal(int)  # 当项目被点击时发出，携带项目索引
    
    def __init__(self, parent=None):
        """
        初始化虚拟列表组件
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.init_ui()
        
        # 数据相关
        self._data = []  # 完整数据列表
        self._visible_items = {}  # 当前可见的项目，使用字典存储，提高查找效率 {index: widget}
        self._item_height = 50  # 每个项目的高度
        self._buffer_size = 5  # 可见区域外的缓冲项目数量，减少滚动时的渲染次数
        self._total_height = 0  # 列表总高度
        
        # 渲染回调
        self._item_renderer: Callable[[Any, int], QWidget] = None  # 项目渲染函数，由外部提供
        
        # 滚动相关
        self._scroll_pos = 0  # 当前滚动位置
        self._last_start_index = -1  # 上一次渲染的起始索引，用于优化渲染逻辑
        self._last_end_index = -1  # 上一次渲染的结束索引，用于优化渲染逻辑
        
    def init_ui(self):
        """
        初始化UI
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 连接滚动信号
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        # 创建内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        # 设置布局为可扩展
        self.content_layout.addStretch()
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
    
    def set_item_renderer(self, renderer: Callable[[Any, int], QWidget]):
        """
        设置项目渲染函数
        
        Args:
            renderer: 项目渲染函数，接收数据项和索引，返回QWidget
        """
        self._item_renderer = renderer
    
    def set_item_height(self, height: int):
        """
        设置项目高度
        
        Args:
            height: 项目高度
        """
        self._item_height = height
    
    def set_data(self, data: List[Any]):
        """
        设置数据列表
        
        Args:
            data: 数据列表
        """
        self._data = data
        self._update_total_height()
        self._render_visible_items()
    
    def _update_total_height(self):
        """
        更新总高度
        """
        self._total_height = len(self._data) * self._item_height
        # 设置内容容器高度
        self.content_widget.setMinimumHeight(self._total_height)
    
    def _on_scroll(self, value: int):
        """
        滚动事件处理
        
        Args:
            value: 滚动位置
        """
        self._scroll_pos = value
        self._render_visible_items()
    
    def _render_visible_items(self):
        """
        渲染可见区域内的项目
        
        优化点：
        1. 使用字典存储可见项目，提高查找效率
        2. 只处理实际可见范围内的项目，减少渲染次数
        3. 缓存上一次渲染的索引范围，避免不必要的重复渲染
        4. 优化项目创建和销毁逻辑，减少内存使用
        """
        if not self._item_renderer or not self._data:
            return
        
        # 计算可见区域
        viewport_size = self.scroll_area.viewport().size()
        visible_rect = QRect(
            QPoint(0, self._scroll_pos),
            viewport_size
        )
        
        # 计算可见项目的索引范围
        start_index = max(0, self._scroll_pos // self._item_height - self._buffer_size)
        end_index = min(
            len(self._data),
            (self._scroll_pos + viewport_size.height()) // self._item_height + self._buffer_size + 1
        )
        
        # 如果索引范围没有变化，不进行渲染
        if start_index == self._last_start_index and end_index == self._last_end_index:
            return
        
        # 更新缓存的索引范围
        self._last_start_index = start_index
        self._last_end_index = end_index
        
        # 收集需要保留的项目索引
        visible_indices = set(range(start_index, end_index))
        current_indices = set(self._visible_items.keys())
        
        # 计算需要移除的项目索引
        indices_to_remove = current_indices - visible_indices
        
        # 移除不可见的项目
        for index in indices_to_remove:
            widget = self._visible_items.pop(index)
            widget.setParent(None)
            widget.deleteLater()
        
        # 计算需要添加的项目索引
        indices_to_add = visible_indices - current_indices
        
        # 渲染可见的项目
        for i in sorted(indices_to_add):
            # 创建新项目
            widget = self._item_renderer(self._data[i], i)
            widget.setProperty("_virtual_index", i)
            
            # 设置项目位置和大小
            widget.setGeometry(0, i * self._item_height, visible_rect.width(), self._item_height)
            
            # 添加到布局和可见项目字典
            self.content_layout.addWidget(widget)
            self._visible_items[i] = widget
        
        # 确保布局正确
        self.content_layout.update()
    
    def resizeEvent(self, event):
        """
        窗口大小变化事件处理
        """
        super().resizeEvent(event)
        self._render_visible_items()
    
    def get_visible_items(self) -> List[QWidget]:
        """
        获取当前可见的项目
        
        Returns:
            List[QWidget]: 当前可见的项目列表，按索引顺序排序
        """
        # 按索引顺序返回可见项目
        return [self._visible_items[i] for i in sorted(self._visible_items.keys())]
    
    def clear(self):
        """
        清空列表
        
        清空所有数据和可见项目，重置组件状态
        """
        # 移除所有可见项目
        for widget in self._visible_items.values():
            widget.setParent(None)
            widget.deleteLater()
        
        # 清空可见项目字典
        self._visible_items.clear()
        
        # 清空数据
        self._data = []
        self._total_height = 0
        self._scroll_pos = 0
        self._last_start_index = -1
        self._last_end_index = -1
        
        # 重置内容容器高度
        self.content_widget.setMinimumHeight(0)
        
        # 更新布局
        self.content_layout.update()
