# -*- coding: utf-8 -*-
"""
讨论配置面板组件，负责主题输入和轮次设置
"""
import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
)
from ui.ui_utils import create_group_box, create_line_edit, get_default_styles
from utils.logger_config import get_logger

# 导入资源管理器
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from utils.resource_manager import ResourceManager
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class ConfigPanel(QWidget):
    """
    讨论配置面板组件

    信号:
        config_changed: 配置变更信号，当配置发生变化时触发
    """

    def __init__(self):
        """初始化配置面板"""
        super().__init__()
        self.styles = get_default_styles()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 配置区域
        self.config_group = create_group_box(
            i18n.translate("discussion_config"), self.styles["group_box"]
        )
        config_layout = QVBoxLayout()
        config_layout.setContentsMargins(10, 5, 10, 10)
        config_layout.setSpacing(12)

        # 主题输入，模仿聊天输入框设计
        topic_layout = QVBoxLayout()
        topic_layout.setSpacing(8)
        self.topic_label = QLabel(i18n.translate("discussion_topic"))
        topic_layout.addWidget(self.topic_label, alignment=Qt.AlignVCenter)
        
        # 使用QTextEdit实现多行输入，完全模仿聊天输入框
        self.topic_edit = QTextEdit()
        self.topic_edit.setPlaceholderText(i18n.translate("discussion_topic_placeholder"))
        
        # 设置样式，与聊天输入框保持一致
        self.topic_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-size: 10pt;
                background-color: #ffffff;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                transition: all 0.2s ease;
            }
            QTextEdit:focus {
                border-color: #4caf50;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
                outline: none;
            }
        """)
        
        # 设置最大高度（约5行）
        self.topic_edit.setMaximumHeight(100)
        # 设置初始高度（约1行）
        self.topic_edit.setFixedHeight(30)
        # 设置垂直滚动条策略
        self.topic_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 连接文本变化信号，自动调整高度
        self.topic_edit.textChanged.connect(self._adjust_topic_height)
        
        # 添加到布局
        topic_layout.addWidget(self.topic_edit)
        config_layout.addLayout(topic_layout)

        # 参数配置
        self.params_group = create_group_box(
            i18n.translate("discussion_params"), self.styles["sub_group_box"]
        )
        params_layout = QHBoxLayout()
        params_layout.setContentsMargins(10, 5, 10, 10)
        params_layout.setSpacing(15)

        # 讨论轮数
        self.rounds_label = QLabel(i18n.translate("discussion_rounds"))
        params_layout.addWidget(self.rounds_label, alignment=Qt.AlignVCenter)
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 9999)
        self.rounds_spin.setValue(5)
        self.rounds_spin.setStyleSheet(self.styles["spin_box"])
        params_layout.addWidget(self.rounds_spin)

        # 时间限制
        self.time_limit_label = QLabel(i18n.translate("discussion_time_limit"))
        params_layout.addWidget(self.time_limit_label, alignment=Qt.AlignVCenter)
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(0, 999999)
        self.time_limit_spin.setValue(0)
        self.time_limit_spin.setSpecialValueText(i18n.translate("discussion_unlimited"))
        self.time_limit_spin.setStyleSheet(self.styles["spin_box"])
        params_layout.addWidget(self.time_limit_spin)
        self.seconds_label = QLabel(i18n.translate("discussion_seconds"))
        params_layout.addWidget(self.seconds_label, alignment=Qt.AlignVCenter)

        # 温度
        self.temp_label = QLabel(i18n.translate("discussion_temperature"))
        params_layout.addWidget(self.temp_label, alignment=Qt.AlignVCenter)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.8)
        self.temp_spin.setStyleSheet(self.styles["spin_box"])
        params_layout.addWidget(self.temp_spin)
        self.temp_range_label = QLabel(i18n.translate("discussion_temperature_range"))
        params_layout.addWidget(self.temp_range_label, alignment=Qt.AlignVCenter)

        # 添加拉伸空间
        params_layout.addStretch(1)

        # 添加NONEAD Logo
        try:
            # 创建Logo标签
            logo_label = QLabel()
            # 使用资源管理器加载并缩放logo
            pixmap = ResourceManager.load_pixmap("noneadLogo.png", 200, 60)
            if pixmap:
                logo_label.setPixmap(pixmap)
                logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                # 添加logo到布局
                params_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)
            else:
                # logo加载失败，显示文本标识
                logo_label.setText("NONEAD")
                logo_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
                logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                logo_label.setStyleSheet("color: #333;")
                params_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)
        except Exception as e:
            logger.error(f"加载Logo失败: {str(e)}")
            # 异常情况下显示文本标识
            logo_label = QLabel()
            logo_label.setText("NONEAD")
            logo_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            logo_label.setStyleSheet("color: #333;")
            params_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)

        self.params_group.setLayout(params_layout)
        config_layout.addWidget(self.params_group)

        self.config_group.setLayout(config_layout)
        layout.addWidget(self.config_group)

        self.setLayout(layout)

    def reinit_ui(self):
        """重新初始化UI，用于语言切换时更新界面"""
        # 更新配置组标题
        self.config_group.setTitle(i18n.translate("discussion_config"))

        # 更新主题标签和占位符
        self.topic_label.setText(i18n.translate("discussion_topic"))
        self.topic_edit.setPlaceholderText(
            i18n.translate("discussion_topic_placeholder")
        )

        # 更新参数组标题
        self.params_group.setTitle(i18n.translate("discussion_params"))

        # 更新讨论轮数标签
        self.rounds_label.setText(i18n.translate("discussion_rounds"))

        # 更新时间限制相关文本
        self.time_limit_label.setText(i18n.translate("discussion_time_limit"))
        self.time_limit_spin.setSpecialValueText(i18n.translate("discussion_unlimited"))
        self.seconds_label.setText(i18n.translate("discussion_seconds"))

        # 更新温度相关文本
        self.temp_label.setText(i18n.translate("discussion_temperature"))
        self.temp_range_label.setText(i18n.translate("discussion_temperature_range"))

    def get_topic(self) -> str:
        """获取讨论主题

        Returns:
            str: 讨论主题
        """
        # 获取所有文本内容，包括换行符，确保控件内所有字符都属于讨论主题
        return self.topic_edit.toPlainText().strip()
    
    def _adjust_topic_height(self) -> None:
        """
        自动调整主题输入框的高度，默认显示1行，最多显示5行
        完全模仿聊天输入框的设计
        """
        # 禁用固定高度限制，允许自动调整
        self.topic_edit.setFixedHeight(0)
        
        # 获取内容高度
        content_height = self.topic_edit.document().size().height()
        
        # 设置固定高度范围
        max_height = 100  # 最大高度（约5行）
        min_height = 30  # 最小高度（约1行）
        
        # 计算合适的高度，添加20px的内边距
        new_height = int(content_height + 20)
        
        # 限制在最小和最大高度之间
        if new_height < min_height:
            new_height = min_height
        elif new_height > max_height:
            new_height = max_height
        
        # 使用setFixedHeight来设置精确的高度
        self.topic_edit.setFixedHeight(new_height)

    def get_rounds(self) -> int:
        """获取讨论轮数

        Returns:
            int: 讨论轮数
        """
        return self.rounds_spin.value()

    def get_time_limit(self) -> int:
        """获取时间限制

        Returns:
            int: 时间限制（秒）
        """
        return self.time_limit_spin.value()

    def get_temperature(self) -> float:
        """获取温度值

        Returns:
            float: 温度值
        """
        return self.temp_spin.value()

    def set_topic(self, topic: str) -> None:
        """设置讨论主题

        Args:
            topic: 讨论主题
        """
        self.topic_edit.setPlainText(topic)
        # 调整高度以适应内容
        self._adjust_topic_height()

    def set_rounds(self, rounds: int) -> None:
        """设置讨论轮数

        Args:
            rounds: 讨论轮数
        """
        self.rounds_spin.setValue(rounds)

    def set_time_limit(self, time_limit: int) -> None:
        """设置时间限制

        Args:
            time_limit: 时间限制（秒）
        """
        self.time_limit_spin.setValue(time_limit)

    def set_temperature(self, temperature: float) -> None:
        """设置温度值

        Args:
            temperature: 温度值
        """
        self.temp_spin.setValue(temperature)
