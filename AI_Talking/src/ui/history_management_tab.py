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
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QFileDialog,
    QSplitter,
    QListWidgetItem,
)

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

        # 加载历史记录
        self.all_chat_histories = self.chat_history_manager.load_history()

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
                font-size: 12pt;
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
        self.history_list.setMaximumHeight(
            200
        )  # 设置更合适的最大高度，确保列表有足够空间显示多条记录
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
                padding: 8px 12px;
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
                border-radius: 4px;
            }
        """)
        history_list_layout.addWidget(self.history_list)

        # 上方控制按钮
        top_control_layout = QHBoxLayout()
        top_control_layout.setSpacing(8)

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

        self.load_history_button = QPushButton(i18n.translate("history_refresh"))
        self.load_history_button.setStyleSheet(button_style)
        self.load_history_button.clicked.connect(self.refresh_history_list)
        top_control_layout.addWidget(self.load_history_button)

        self.delete_history_button = QPushButton(
            i18n.translate("history_delete_selected")
        )
        self.delete_history_button.setStyleSheet(button_style)
        self.delete_history_button.clicked.connect(self.delete_selected_history)
        self.delete_history_button.setEnabled(False)
        top_control_layout.addWidget(self.delete_history_button)

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

        top_control_layout.addStretch()
        history_list_layout.addLayout(top_control_layout)

        self.history_list_group.setLayout(history_list_layout)
        top_layout.addWidget(self.history_list_group)

        # 历史统计信息
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
        top_layout.addWidget(self.history_stats_label)

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
                font-size: 12pt;
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

        # 历史详情文本框
        self.history_detail_text = QTextEdit()
        self.history_detail_text.setReadOnly(True)
        self.history_detail_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.history_detail_text.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 10pt;
                background-color: white;
                padding: 10px;
            }
            QTextEdit:focus {
                border-color: #4285f4;
                box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.1);
            }
        """)
        history_detail_layout.addWidget(self.history_detail_text)

        self.history_detail_group.setLayout(history_detail_layout)
        bottom_layout.addWidget(self.history_detail_group)

        # 下方控制按钮
        bottom_control_layout = QHBoxLayout()
        bottom_control_layout.setSpacing(8)

        self.export_history_button = QPushButton(i18n.translate("export_selected"))
        self.export_history_button.setStyleSheet(button_style)
        self.export_history_button.clicked.connect(self.export_selected_history)
        self.export_history_button.setEnabled(False)
        bottom_control_layout.addWidget(self.export_history_button)

        self.export_all_button = QPushButton(i18n.translate("export_all"))
        self.export_all_button.setStyleSheet(button_style)
        self.export_all_button.clicked.connect(self.export_all_history)
        bottom_control_layout.addWidget(self.export_all_button)

        bottom_control_layout.addStretch()
        bottom_layout.addLayout(bottom_control_layout)

        bottom_widget.setLayout(bottom_layout)
        splitter.addWidget(bottom_widget)

        # 设置分栏比例
        splitter.setSizes([250, 450])

        layout.addWidget(splitter)

        # 更新历史列表
        self.refresh_history_list()

        self.setLayout(layout)

    def refresh_history_list(self):
        """
        刷新历史记录列表
        """
        logger.info("正在刷新历史记录列表...")

        # 清空列表
        self.history_list.clear()

        # 重新加载历史记录
        self.all_chat_histories = self.chat_history_manager.load_history()

        # 更新统计信息
        stats_text = i18n.translate("history_count").format(
            count=len(self.all_chat_histories)
        )
        self.history_stats_label.setText(stats_text)

        # 添加历史记录到列表
        for i, history in enumerate(self.all_chat_histories):
            topic = history.get("topic", "无主题")
            model1_name = history.get("model1", "未知模型")  # 修复变量名
            model2_name = history.get("model2", "未知模型")  # 修复变量名
            start_time = history.get("start_time", "未知时间")
            end_time = history.get("end_time", "未知时间")

            # 创建列表项
            item_text = (
                f"{i+1}. {topic} - {model1_name} vs {model2_name} ({start_time})"
            )
            item = QListWidgetItem(item_text)
            item.setData(1, i)  # 存储索引
            item.setToolTip(
                f"开始时间: {start_time}\n结束时间: {end_time}\n模型: {model1_name} vs {model2_name}"
            )

            self.history_list.addItem(item)

        logger.info(f"历史记录列表刷新完成，共 {len(self.all_chat_histories)} 条记录")

    def on_history_item_clicked(self, item):
        """
        历史记录项点击事件处理

        Args:
            item: 被点击的列表项
        """
        # 获取选中的历史记录索引
        index = item.data(1)

        # 显示历史记录详情
        self.show_history_detail(index)

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
        index = item.data(1)

        # 发出历史记录选中信号
        self.history_selected.emit(self.all_chat_histories[index])

    def show_history_detail(self, index):
        """
        显示历史记录详情

        Args:
            index: 历史记录索引
        """
        if 0 <= index < len(self.all_chat_histories):
            history = self.all_chat_histories[index]

            # 构建历史详情文本
            detail_text = "# 聊天历史详情\n\n"
            detail_text += f"**主题**: {history.get('topic', '无主题')}\n\n"
            detail_text += f"**模型1**: {history.get('model1', '未知模型')} ({history.get('api1', '未知API')})\n"
            detail_text += f"**模型2**: {history.get('model2', '未知模型')} ({history.get('api2', '未知API')})\n\n"
            detail_text += f"**轮数**: {history.get('rounds', '未知')}\n"
            detail_text += f"**开始时间**: {history.get('start_time', '未知')}\n"
            detail_text += f"**结束时间**: {history.get('end_time', '未知')}\n\n"
            detail_text += "## 聊天内容\n\n"
            detail_text += history.get("chat_content", "无聊天内容")

            # 显示详情
            self.history_detail_text.setMarkdown(detail_text)

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
            for item in selected_items:
                index = item.data(1)

                # 删除历史记录
                self.chat_history_manager.delete_history(index)
                self.history_deleted.emit(index)

            # 刷新列表
            self.refresh_history_list()

            # 清空详情
            self.history_detail_text.clear()

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
        if len(self.all_chat_histories) == 0:
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

            # 刷新列表
            self.refresh_history_list()

            # 清空详情
            self.history_detail_text.clear()

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
                    json.dump(selected_histories, f, ensure_ascii=False, indent=2)

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
                    json.dump(self.all_chat_histories, f, ensure_ascii=False, indent=2)

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
            count=len(self.all_chat_histories)
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
