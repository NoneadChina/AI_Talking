# -*- coding: utf-8 -*-
"""
历史管理标签页组件，用于管理聊天历史记录
"""

import sys
import os
import json
from datetime import datetime
from utils.logger_config import get_logger
from utils.chat_history_manager import ChatHistoryManager
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QGroupBox,
    QMessageBox,
    QFileDialog,
    QSplitter,
    QListWidgetItem,
    QSizePolicy,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 导入国际化管理器
from utils.i18n_manager import i18n

# 获取日志记录器
logger = get_logger(__name__)


class HistoryManagementTabWidget(QWidget):
    """
    历史管理标签页组件，用于管理聊天历史记录

    信号:
        history_selected: 历史记录选中信号，参数为选中的历史记录
        history_deleted: 历史记录删除信号，参数为删除的历史记录索引
        history_cleared: 历史记录清空信号
    """

    # 定义信号
    history_selected = pyqtSignal(dict)
    history_deleted = pyqtSignal(int)
    history_cleared = pyqtSignal()

    def __init__(self):
        """
        初始化历史管理标签页组件
        """
        super().__init__()

        # 初始化聊天历史管理器
        self.chat_history_manager = ChatHistoryManager()

        # 分页相关属性
        self.current_page = 1
        self.page_size = 20  # 每页显示20条记录
        self.total_pages = 1
        self.total_count = 0
        
        # 当前页显示的历史记录
        self.current_page_histories = []
        
        # 加载历史记录总数
        self.total_count = self.chat_history_manager.get_history_count()
        self.calculate_total_pages()

        # 初始化UI
        self.init_ui()

    def init_ui(self):
        """
        初始化历史管理标签页UI
        """
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 设置页面背景
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f5f7fa;
            }
        """
        )

        # 创建分栏布局
        splitter = QSplitter()
        splitter.setOrientation(Qt.Vertical)  # 设置为垂直方向，确保上下结构
        splitter.setStyleSheet(
            """
            QSplitter {
                background-color: transparent;
            }
            QSplitter::handle {
                background-color: #e0e0e0;
                height: 5px;
                margin: 0 20px;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #bdbdbd;
            }
        """
        )

        # 上方历史列表区域
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # 历史列表组
        self.history_list_group = QGroupBox(i18n.translate("history_list"))
        self.history_list_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        history_list_layout = QVBoxLayout()
        history_list_layout.setContentsMargins(10, 5, 10, 10)
        history_list_layout.setSpacing(10)

        # 历史记录列表
        self.history_list = QListWidget()
        # 移除固定最大高度限制，使其能够根据窗口大小变化
        self.history_list.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        self.history_list.itemDoubleClicked.connect(self.on_history_item_double_clicked)
        self.history_list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 9pt;
                background-color: white;
            }
            QListWidget::item {
                padding: 4px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:last-child {
                border-bottom: none;
            }
            QListWidget::item:hover {
                background-color: #f5f7fa;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1b5e20;
                border-radius: 4px;
            }
        """)
        history_list_layout.addWidget(self.history_list)

        self.history_list_group.setLayout(history_list_layout)
        top_layout.addWidget(self.history_list_group)

        top_widget.setLayout(top_layout)
        splitter.addWidget(top_widget)

        # 下方历史详情区域
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)

        # 历史详情组
        self.history_detail_group = QGroupBox(i18n.translate("history_detail"))
        self.history_detail_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        history_detail_layout = QVBoxLayout()
        history_detail_layout.setContentsMargins(10, 5, 10, 10)
        history_detail_layout.setSpacing(10)

        # 历史详情浏览器控件
        self.history_detail_text = QWebEngineView()
        # 禁用右键菜单
        self.history_detail_text.setContextMenuPolicy(Qt.NoContextMenu)
        self.history_detail_text.setStyleSheet(
            """
            QWebEngineView {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
        """)
        history_detail_layout.addWidget(self.history_detail_text)
        # 设置浏览器控件的大小策略，使其能够随窗体大小变化
        self.history_detail_text.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )

        self.history_detail_group.setLayout(history_detail_layout)
        bottom_layout.addWidget(self.history_detail_group)

        # 底部控制区域
        bottom_control_widget = QWidget()
        bottom_control_layout = QVBoxLayout(bottom_control_widget)
        bottom_control_layout.setContentsMargins(0, 0, 0, 0)
        bottom_control_layout.setSpacing(10)
        
        button_style = """
            QPushButton {
                padding: 8px 12px;
                font-size: 9pt;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        
        # 第一行：统计信息和操作按钮
        top_control_widget = QWidget()
        top_control_layout = QHBoxLayout(top_control_widget)
        top_control_layout.setContentsMargins(0, 0, 0, 0)
        top_control_layout.setSpacing(10)
        top_control_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 历史统计信息，靠左
        self.history_stats_label = QLabel(i18n.translate("history_stats"))
        self.history_stats_label.setStyleSheet(
            """
            QLabel {
                font-size: 9pt;
                color: #666;
                background-color: white;
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid #ddd;
            }
        """)
        top_control_layout.addWidget(self.history_stats_label)
        
        # 添加伸缩项，将按钮推到右侧
        top_control_layout.addStretch()
        
        # 导出选中按钮
        self.export_history_button = QPushButton(i18n.translate("export_selected"))
        self.export_history_button.setStyleSheet(button_style)
        self.export_history_button.clicked.connect(self.export_selected_history)
        self.export_history_button.setEnabled(False)
        top_control_layout.addWidget(self.export_history_button)
        
        # 导出所有按钮
        self.export_all_button = QPushButton(i18n.translate("export_all"))
        self.export_all_button.setStyleSheet(button_style)
        self.export_all_button.clicked.connect(self.export_all_history)
        top_control_layout.addWidget(self.export_all_button)
        
        # 刷新按钮
        self.load_history_button = QPushButton(i18n.translate("history_refresh"))
        self.load_history_button.setStyleSheet(button_style)
        self.load_history_button.clicked.connect(self.refresh_history_list)
        top_control_layout.addWidget(self.load_history_button)
        
        # 删除选中按钮
        self.delete_history_button = QPushButton(
            i18n.translate("history_delete_selected")
        )
        self.delete_history_button.setStyleSheet(button_style)
        self.delete_history_button.clicked.connect(self.delete_selected_history)
        self.delete_history_button.setEnabled(False)
        top_control_layout.addWidget(self.delete_history_button)
        
        # 清空所有按钮
        self.clear_history_button = QPushButton(i18n.translate("history_clear_all"))
        self.clear_history_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 12px;
                font-size: 9pt;
                border: 1px solid #e57373;
                border-radius: 6px;
                background-color: #ffebee;
                color: #c62828;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
        """)
        self.clear_history_button.clicked.connect(self.clear_all_history)
        top_control_layout.addWidget(self.clear_history_button)
        
        bottom_control_layout.addWidget(top_control_widget)
        
        # 在顶部控制布局中添加分页控件
        top_control_layout.addStretch()
        
        # 上一页按钮
        self.prev_page_button = QPushButton(i18n.translate("prev_page"))
        self.prev_page_button.setStyleSheet(button_style)
        self.prev_page_button.clicked.connect(self.go_prev_page)
        self.prev_page_button.setEnabled(False)  # 初始时第一页，禁用上一页
        top_control_layout.addWidget(self.prev_page_button)
        
        # 页码显示
        self.page_info_label = QLabel()
        self.page_info_label.setStyleSheet(
            """
            QLabel {
                font-size: 9pt;
                color: #666;
                background-color: white;
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #ddd;
            }
        """)
        top_control_layout.addWidget(self.page_info_label)
        
        # 下一页按钮
        self.next_page_button = QPushButton(i18n.translate("next_page"))
        self.next_page_button.setStyleSheet(button_style)
        self.next_page_button.clicked.connect(self.go_next_page)
        self.next_page_button.setEnabled(self.total_pages > 1)  # 如果只有一页，禁用下一页
        top_control_layout.addWidget(self.next_page_button)
        
        bottom_layout.addWidget(bottom_control_widget)

        bottom_widget.setLayout(bottom_layout)
        splitter.addWidget(bottom_widget)

        # 设置分栏比例，让历史详情区域更大
        splitter.setSizes([200, 500])

        layout.addWidget(splitter)

        # 更新历史列表
        self.refresh_history_list()

        self.setLayout(layout)
        
    def calculate_total_pages(self):
        """
        计算总页数
        """
        if self.page_size > 0:
            self.total_pages = (self.total_count + self.page_size - 1) // self.page_size
        else:
            self.total_pages = 1
        
    def showEvent(self, event):
        """
        标签页显示事件，每次显示时刷新历史列表
        """
        super().showEvent(event)
        self.refresh_history_list()

    def refresh_history_list(self, reset_page=True):
        """
        刷新历史记录列表
        
        Args:
            reset_page (bool): 是否重置到第一页
        """
        logger.info("正在刷新历史记录列表...")

        # 清空列表
        self.history_list.clear()

        # 重新加载历史记录总数
        self.total_count = self.chat_history_manager.get_history_count()
        self.calculate_total_pages()
        
        # 如果重置页码或当前页码超过总页数，重置到第一页
        if reset_page or self.current_page > self.total_pages:
            self.current_page = 1
        
        # 加载当前页的历史记录
        self.load_current_page_histories()
        
        # 更新统计信息
        stats_text = i18n.translate("history_count").format(
            count=self.total_count
        )
        self.history_stats_label.setText(stats_text)
        
        # 更新页码信息
        self.update_page_info()
        
        # 更新分页按钮状态
        self.update_page_buttons()

        # 按结束时间倒序排序当前页的历史记录，最新的放在前面
        self.current_page_histories.sort(key=lambda x: x.get("end_time", ""), reverse=True)

        # 添加当前页的历史记录到列表
        for i, history in enumerate(self.current_page_histories):
            topic = history.get("topic", "无主题")
            model1_name = history.get("model1", "未知模型")
            model2_name = history.get("model2", "未知模型")
            start_time = history.get("start_time", "未知时间")
            end_time = history.get("end_time", "未知时间")

            # 计算原始索引（考虑当前页码和页大小）
            original_index = (self.current_page - 1) * self.page_size + i
            
            # 创建列表项
            item_text = (
                f"{original_index+1}. {topic} - {model1_name} vs {model2_name} ({start_time})"
            )
            item = QListWidgetItem(item_text)
            item.setData(1, original_index)  # 存储原始索引
            item.setToolTip(
                f"开始时间: {start_time}\n结束时间: {end_time}\n模型: {model1_name} vs {model2_name}"
            )

            self.history_list.addItem(item)

        logger.info(f"历史记录列表刷新完成，当前页 {self.current_page}/{self.total_pages}，显示 {len(self.current_page_histories)} 条记录，共 {self.total_count} 条记录")
    
    def load_current_page_histories(self):
        """
        加载当前页的历史记录
        """
        # 获取完整的历史记录
        all_histories = self.chat_history_manager.load_history()
        
        # 按结束时间倒序排序所有历史记录
        all_histories.sort(key=lambda x: x.get("end_time", ""), reverse=True)
        
        # 计算当前页的起始和结束索引
        start_index = (self.current_page - 1) * self.page_size
        end_index = start_index + self.page_size
        
        # 获取当前页的历史记录
        self.current_page_histories = all_histories[start_index:end_index]
    
    def update_page_info(self):
        """
        更新页码信息显示
        """
        page_info_text = i18n.translate("page_info").format(
            current_page=self.current_page,
            total_pages=self.total_pages
        )
        self.page_info_label.setText(page_info_text)
    
    def update_page_buttons(self):
        """
        更新分页按钮状态
        """
        # 更新上一页按钮状态
        self.prev_page_button.setEnabled(self.current_page > 1)
        
        # 更新下一页按钮状态
        self.next_page_button.setEnabled(self.current_page < self.total_pages)
    
    def go_prev_page(self):
        """
        跳转到上一页
        """
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_history_list(reset_page=False)
    
    def go_next_page(self):
        """
        跳转到下一页
        """
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_history_list(reset_page=False)

    def on_history_item_clicked(self, item):
        """
        历史记录项点击事件处理

        Args:
            item: 被点击的列表项
        """
        # 获取选中的历史记录索引
        original_index = item.data(1)

        # 显示历史记录详情
        self.show_history_detail(original_index)

        # 启用删除和导出按钮
        self.delete_history_button.setEnabled(True)
        self.export_history_button.setEnabled(True)

    def on_history_item_double_clicked(self, item):
        """
        历史记录项双击事件处理

        Args:
            item: 被双击的列表项
        """
        # 获取选中的历史记录索引
        original_index = item.data(1)
        
        # 获取完整的历史记录列表用于发出信号
        all_histories = self.chat_history_manager.load_history()
        all_histories.sort(key=lambda x: x.get("end_time", ""), reverse=True)

        # 发出历史记录选中信号
        if 0 <= original_index < len(all_histories):
            self.history_selected.emit(all_histories[original_index])

    def show_history_detail(self, original_index):
        """
        显示历史记录详情

        Args:
            original_index: 历史记录的原始索引
        """
        # 获取完整的历史记录列表
        all_histories = self.chat_history_manager.load_history()
        all_histories.sort(key=lambda x: x.get("end_time", ""), reverse=True)
        
        if 0 <= original_index < len(all_histories):
            history = all_histories[original_index]
            
            # 使用缓存的HTML模板，避免重复构建
            detail_html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='utf-8'>
                <meta name='viewport' content='width=device-width, initial-scale=1.0'>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 15px;
                        padding: 0;
                    }}
                    h1 {{
                        color: #2c3e50;
                        border-bottom: 2px solid #eaecef;
                        padding-bottom: 0.3em;
                    }}
                    h2 {{
                        color: #2c3e50;
                        border-bottom: 1px solid #eaecef;
                        padding-bottom: 0.3em;
                    }}
                    p {{
                        margin: 0.5em 0;
                    }}
                    strong {{
                        color: #2c3e50;
                    }}
                    .chat-content {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 8px;
                        border: 1px solid #e9ecef;
                        margin-top: 10px;
                    }}
                    .history-item {{
                        margin: 10px 0;
                    }}
                </style>
            </head>
            <body>
                <h1>聊天历史详情</h1>
                <div class='history-item'><strong>主题</strong>: {topic}</div>
                <div class='history-item'><strong>模型1</strong>: {model1} ({api1})</div>
                <div class='history-item'><strong>模型2</strong>: {model2} ({api2})</div>
                <div class='history-item'><strong>轮数</strong>: {rounds}</div>
                <div class='history-item'><strong>开始时间</strong>: {start_time}</div>
                <div class='history-item'><strong>结束时间</strong>: {end_time}</div>
                <h2>聊天内容</h2>
                <div class='chat-content'>{chat_content}</div>
            </body>
            </html>
            """
            
            # 替换占位符
            detail_html = detail_html_template.format(
                topic=history.get('topic', '无主题'),
                model1=history.get('model1', '未知模型'),
                api1=history.get('api1', '未知API'),
                model2=history.get('model2', '未知模型'),
                api2=history.get('api2', '未知API'),
                rounds=history.get('rounds', '未知'),
                start_time=history.get('start_time', '未知'),
                end_time=history.get('end_time', '未知'),
                chat_content=history.get("chat_content", "无聊天内容")
            )

            # 显示详情
            self.history_detail_text.setHtml(detail_html)

    def delete_selected_history(self):
        """
        删除选中的历史记录
        """
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, i18n.translate("warning"), i18n.translate("please_select_history")
            )
            return

        # 确认删除
        reply = QMessageBox.question(
            self,
            i18n.translate("confirm_delete"),
            i18n.translate("confirm_delete_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 收集所有要删除的索引
            indices_to_delete = []
            for item in selected_items:
                original_index = item.data(1)
                indices_to_delete.append(original_index)
            
            # 按索引从大到小排序，确保删除不会影响后续索引
            indices_to_delete.sort(reverse=True)
            
            # 删除历史记录
            for index in indices_to_delete:
                self.chat_history_manager.delete_history(index)
                self.history_deleted.emit(index)

            # 刷新列表，保持在当前页（如果当前页为空，则自动跳转到上一页）
            current_items_count = len(self.current_page_histories)
            if current_items_count == len(selected_items):
                # 如果删除了当前页所有记录，且不是第一页，则跳转到上一页
                if self.current_page > 1:
                    self.current_page -= 1
            
            # 刷新列表
            self.refresh_history_list(reset_page=False)

            # 清空详情
            self.history_detail_text.setHtml("<html><body style='margin: 15px;'><p>请选择一条历史记录查看详情</p></body></html>")

            # 禁用按钮
            self.delete_history_button.setEnabled(False)
            self.export_history_button.setEnabled(False)

            QMessageBox.information(
                self, i18n.translate("success"), i18n.translate("history_deleted")
            )

    def clear_all_history(self):
        """
        清空所有历史记录
        """
        if self.total_count == 0:
            QMessageBox.information(
                self, i18n.translate("info"), i18n.translate("history_empty")
            )
            return

        # 确认清空
        reply = QMessageBox.question(
            self,
            i18n.translate("confirm_clear"),
            i18n.translate("confirm_clear_msg"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 清空历史记录
            self.chat_history_manager.clear_history()
            self.history_cleared.emit()

            # 刷新列表，重置到第一页
            self.refresh_history_list(reset_page=True)

            # 清空详情
            self.history_detail_text.setHtml("<html><body style='margin: 15px;'><p>请选择一条历史记录查看详情</p></body></html>")

            # 禁用按钮
            self.delete_history_button.setEnabled(False)
            self.export_history_button.setEnabled(False)

            QMessageBox.information(
                self, i18n.translate("success"), i18n.translate("all_history_cleared")
            )

    def export_selected_history(self):
        """
        导出选中的历史记录
        """
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, i18n.translate("warning"), i18n.translate("please_select_history")
            )
            return

        # 打开文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, i18n.translate("export_history"), "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                # 获取选中的历史记录
                selected_histories = []
                for item in selected_items:
                    index = item.data(1)
                    selected_histories.append(self.all_chat_histories[index])

                # 写入文件
                with open(file_path, "w", encoding="utf-8") as f:
                    # 添加default=str参数，将不可序列化的对象转换为字符串
                    json.dump(selected_histories, f, ensure_ascii=False, indent=2, default=str)

                QMessageBox.information(
                    self,
                    i18n.translate("success"),
                    i18n.translate("history_exported").format(file_path=file_path),
                )
                logger.info(f"历史记录已导出到 {file_path}")
            except Exception as e:
                error_msg = f"导出历史记录失败: {str(e)}"
                logger.error(error_msg)
                QMessageBox.critical(self, i18n.translate("error"), error_msg)

    def export_all_history(self):
        """
        导出所有历史记录
        """
        if len(self.all_chat_histories) == 0:
            QMessageBox.information(
                self, i18n.translate("info"), i18n.translate("no_history_to_export")
            )
            return

        # 打开文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, i18n.translate("export_all_history"), "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                # 写入文件
                with open(file_path, "w", encoding="utf-8") as f:
                    # 添加default=str参数，将不可序列化的对象转换为字符串
                    json.dump(self.all_chat_histories, f, ensure_ascii=False, indent=2, default=str)

                QMessageBox.information(
                    self,
                    i18n.translate("success"),
                    i18n.translate("all_history_exported").format(file_path=file_path),
                )
                logger.info(f"所有历史记录已导出到 {file_path}")
            except Exception as e:
                error_msg = f"导出所有历史记录失败: {str(e)}"
                logger.error(error_msg)
                QMessageBox.critical(self, i18n.translate("error"), error_msg)

    def add_history(
        self,
        func_type,
        topic,
        model1_name,
        model2_name,
        api1,
        api2,
        rounds,
        chat_content,
    ):
        """
        添加新的历史记录

        Args:
            func_type: 功能类型，可选值："聊天"、"讨论"、"辩论"、"批量"
            topic: 聊天主题
            model1_name: 模型1名称
            model2_name: 模型2名称
            api1: 模型1 API类型
            api2: 模型2 API类型
            rounds: 聊天轮数
            chat_content: 聊天内容
        """
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 添加历史记录
        self.chat_history_manager.add_history(
            func_type,
            topic,
            model1_name,
            model2_name,
            api1,
            api2,
            rounds,
            chat_content,
            current_time,
            current_time,
        )

        # 刷新列表
        self.refresh_history_list()

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新组框标题
        self.history_list_group.setTitle(i18n.translate("history_list"))
        self.history_detail_group.setTitle(i18n.translate("history_detail"))
        
        # 更新统计信息
        stats_text = i18n.translate("history_count").format(
            count=self.chat_history_manager.get_history_count()
        )
        self.history_stats_label.setText(stats_text)

        # 更新控制按钮文本
        self.load_history_button.setText(i18n.translate("history_refresh"))
        self.delete_history_button.setText(i18n.translate("history_delete_selected"))
        self.clear_history_button.setText(i18n.translate("history_clear_all"))
        self.export_history_button.setText(i18n.translate("export_selected"))
        self.export_all_button.setText(i18n.translate("export_all"))

        # 刷新历史记录列表，确保列表项文本也得到更新
        self.refresh_history_list()
