# -*- coding: utf-8 -*-
"""
辩论配置面板组件，负责辩论主题、轮数、时间限制和温度设置
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
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
)
from ui.ui_utils import create_group_box, get_default_styles
from utils.logger_config import get_logger

# 导入资源管理器
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from utils.resource_manager import ResourceManager
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class DebateConfigPanel(QWidget):
    """
    辩论配置面板组件

    属性:
        debate_topic_edit: 辩论主题输入框
        debate_rounds_spin: 辩论轮数选择器
        debate_time_limit_spin: 时间限制选择器
        debate_temp_spin: 温度选择器
    """

    def __init__(self):
        """初始化辩论配置面板"""
        super().__init__()
        self.styles = get_default_styles()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 辩论配置区域
        self.config_group = create_group_box(
            i18n.translate("debate_config"), self.styles["group_box"]
        )
        config_layout = QVBoxLayout()
        config_layout.setContentsMargins(15, 10, 15, 15)
        config_layout.setSpacing(12)

        # 主题输入
        topic_layout = QHBoxLayout()
        topic_layout.setSpacing(8)
        self.topic_label = QLabel(i18n.translate("debate_topic"))
        topic_layout.addWidget(self.topic_label, alignment=Qt.AlignVCenter)

        self.debate_topic_edit = QLineEdit()
        self.debate_topic_edit.setPlaceholderText(
            i18n.translate("debate_topic_placeholder")
        )
        self.debate_topic_edit.setStyleSheet(self.styles["line_edit"])
        topic_layout.addWidget(self.debate_topic_edit)
        config_layout.addLayout(topic_layout)

        # 辩论参数配置
        self.params_group = create_group_box(
            i18n.translate("debate_params"), self.styles["sub_group_box"]
        )
        params_layout = QHBoxLayout()
        params_layout.setContentsMargins(10, 5, 10, 10)
        params_layout.setSpacing(15)

        # 辩论轮数
        self.rounds_label = QLabel(i18n.translate("debate_rounds"))
        params_layout.addWidget(self.rounds_label, alignment=Qt.AlignVCenter)
        self.debate_rounds_spin = QSpinBox()
        self.debate_rounds_spin.setRange(1, 9999)
        self.debate_rounds_spin.setValue(5)
        self.debate_rounds_spin.setStyleSheet(self.styles["spin_box"])
        params_layout.addWidget(self.debate_rounds_spin)

        # 时间限制
        self.time_limit_label = QLabel(i18n.translate("debate_time_limit"))
        params_layout.addWidget(self.time_limit_label, alignment=Qt.AlignVCenter)
        self.debate_time_limit_spin = QSpinBox()
        self.debate_time_limit_spin.setRange(0, 999999)
        self.debate_time_limit_spin.setValue(0)
        self.debate_time_limit_spin.setSpecialValueText(
            i18n.translate("debate_unlimited")
        )
        self.debate_time_limit_spin.setStyleSheet(self.styles["spin_box"])
        params_layout.addWidget(self.debate_time_limit_spin)
        self.seconds_label = QLabel(i18n.translate("debate_seconds"))
        params_layout.addWidget(self.seconds_label, alignment=Qt.AlignVCenter)

        # 温度调节
        self.temperature_label = QLabel(i18n.translate("debate_temperature"))
        params_layout.addWidget(self.temperature_label, alignment=Qt.AlignVCenter)
        self.debate_temp_spin = QDoubleSpinBox()
        self.debate_temp_spin.setRange(0.0, 2.0)
        self.debate_temp_spin.setSingleStep(0.1)
        self.debate_temp_spin.setValue(0.8)
        self.debate_temp_spin.setStyleSheet(self.styles["spin_box"])
        params_layout.addWidget(self.debate_temp_spin)
        self.temperature_range_label = QLabel(
            i18n.translate("debate_temperature_range")
        )
        params_layout.addWidget(self.temperature_range_label, alignment=Qt.AlignVCenter)

        # 添加拉伸空间，将logo推到最右侧
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
        # 更新辩论配置组标题
        self.config_group.setTitle(i18n.translate("debate_config"))

        # 更新主题标签和占位符
        self.topic_label.setText(i18n.translate("debate_topic"))
        self.debate_topic_edit.setPlaceholderText(
            i18n.translate("debate_topic_placeholder")
        )

        # 更新参数组标题
        self.params_group.setTitle(i18n.translate("debate_params"))

        # 更新辩论轮数标签
        self.rounds_label.setText(i18n.translate("debate_rounds"))

        # 更新时间限制相关文本
        self.time_limit_label.setText(i18n.translate("debate_time_limit"))
        self.debate_time_limit_spin.setSpecialValueText(
            i18n.translate("debate_unlimited")
        )
        self.seconds_label.setText(i18n.translate("debate_seconds"))

        # 更新温度相关文本
        self.temperature_label.setText(i18n.translate("debate_temperature"))
        self.temperature_range_label.setText(i18n.translate("debate_temperature_range"))

    def get_topic(self) -> str:
        """获取辩论主题

        Returns:
            str: 辩论主题
        """
        return self.debate_topic_edit.text().strip()

    def get_rounds(self) -> int:
        """获取辩论轮数

        Returns:
            int: 辩论轮数
        """
        return self.debate_rounds_spin.value()

    def get_time_limit(self) -> int:
        """获取时间限制

        Returns:
            int: 时间限制（秒）
        """
        return self.debate_time_limit_spin.value()

    def get_temperature(self) -> float:
        """获取温度值

        Returns:
            float: 温度值
        """
        return self.debate_temp_spin.value()
