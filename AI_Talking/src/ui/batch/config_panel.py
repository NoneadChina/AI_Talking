# -*- coding: utf-8 -*-
"""
批量配置面板组件，负责批量类型选择和任务输入
"""

import os
import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QTextEdit,
    QPushButton,
    QRadioButton,
    QFileDialog,
)
from utils.logger_config import get_logger

# 导入资源管理器
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from utils.resource_manager import ResourceManager
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class BatchConfigPanel(QWidget):
    """
    批量配置面板组件

    信号:
        batch_type_changed: 批量类型变化信号
        task_count_changed: 任务数量变化信号
    """

    # 定义信号
    batch_type_changed = pyqtSignal(str)  # 批量类型变化信号，参数为类型名称
    task_count_changed = pyqtSignal(int)  # 任务数量变化信号，参数为任务数量

    def __init__(self):
        """初始化批量配置面板"""
        super().__init__()
        self.init_ui()
        self.update_task_count()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 批量类型选择
        batch_type_group = QGroupBox(i18n.translate("batch_type_selection"))
        batch_type_group.setStyleSheet(
            """
            QGroupBox {
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
                font-size: 9pt;
            }
        """
        )
        batch_type_layout = QHBoxLayout()
        batch_type_layout.setContentsMargins(10, 5, 10, 10)

        self.discussion_radio = QRadioButton(i18n.translate("batch_discussion"))
        self.debate_radio = QRadioButton(i18n.translate("batch_debate"))
        self.discussion_radio.setChecked(True)  # 默认选择讨论
        self.discussion_radio.setStyleSheet("font-size: 10pt;")
        self.debate_radio.setStyleSheet("font-size: 10pt;")

        # 添加单选按钮信号连接
        self.discussion_radio.toggled.connect(self.on_batch_type_changed)
        self.debate_radio.toggled.connect(self.on_batch_type_changed)

        batch_type_layout.addWidget(self.discussion_radio)
        batch_type_layout.addWidget(self.debate_radio)
        batch_type_layout.addStretch()

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
                batch_type_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)
            else:
                # logo加载失败，显示文本标识
                logo_label.setText("NONEAD")
                logo_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
                logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                logo_label.setStyleSheet("color: #333;")
                batch_type_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)
        except Exception as e:
            logger.error(f"加载Logo失败: {str(e)}")
            # 异常情况下显示文本标识
            logo_label = QLabel()
            logo_label.setText("NONEAD")
            logo_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            logo_label.setStyleSheet("color: #333;")
            batch_type_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)

        batch_type_group.setLayout(batch_type_layout)
        layout.addWidget(batch_type_group)

        # 任务输入区域
        self.task_group = QGroupBox(i18n.translate("batch_task_input"))
        self.task_group.setStyleSheet(
            """
            QGroupBox {
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
                font-size: 9pt;
            }
        """
        )
        task_layout = QVBoxLayout()
        task_layout.setContentsMargins(10, 5, 10, 10)
        task_layout.setSpacing(10)

        # Task input with clear button
        task_edit_layout = QHBoxLayout()
        self.task_edit = QTextEdit()
        self.task_edit.setPlaceholderText(i18n.translate("batch_task_placeholder"))
        # 设置为8行高度，每行约20px，加上内边距
        self.task_edit.setMinimumHeight(160)
        self.task_edit.setMaximumHeight(160)
        self.task_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
                line-height: 20px;
            }
        """
        )
        task_edit_layout.addWidget(self.task_edit)

        # Add task controls
        task_controls_layout = QVBoxLayout()
        task_controls_layout.setSpacing(8)

        self.clear_tasks_button = QPushButton(i18n.translate("batch_clear_tasks"))
        self.clear_tasks_button.clicked.connect(self.clear_tasks)
        self.clear_tasks_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )
        task_controls_layout.addWidget(self.clear_tasks_button)

        self.task_count_label = QLabel(f"{i18n.translate('batch_task_count')}: 0")
        self.task_count_label.setStyleSheet("font-size: 9pt; color: #666;")
        task_controls_layout.addWidget(self.task_count_label)

        task_edit_layout.addLayout(task_controls_layout)
        task_layout.addLayout(task_edit_layout)

        # Task input event to update count
        self.task_edit.textChanged.connect(self.update_task_count)

        self.task_group.setLayout(task_layout)
        layout.addWidget(self.task_group)

        # 处理参数
        self.params_group = QGroupBox(i18n.translate("batch_processing_params"))
        self.params_group.setStyleSheet(
            """
            QGroupBox {
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
                font-size: 9pt;
            }
        """
        )
        params_layout = QVBoxLayout()
        params_layout.setContentsMargins(10, 5, 10, 10)

        # 参数网格布局
        self.params_grid = QWidget()
        params_grid_layout = QHBoxLayout(self.params_grid)
        params_grid_layout.setContentsMargins(0, 0, 0, 0)
        params_grid_layout.setSpacing(15)

        # Rounds (轮数)
        self.batch_rounds_label = QLabel(i18n.translate("batch_rounds"))
        params_grid_layout.addWidget(
            self.batch_rounds_label,
            alignment=Qt.AlignRight | Qt.AlignVCenter,
        )
        from PyQt5.QtWidgets import QSpinBox

        self.batch_rounds_spin = QSpinBox()
        self.batch_rounds_spin.setRange(1, 20)
        self.batch_rounds_spin.setValue(5)
        self.batch_rounds_spin.setStyleSheet("font-size: 9pt; padding: 4px;")
        params_grid_layout.addWidget(self.batch_rounds_spin)

        # Time Limit (时间限制)
        self.batch_time_limit_label = QLabel(i18n.translate("batch_time_limit"))
        params_grid_layout.addWidget(
            self.batch_time_limit_label,
            alignment=Qt.AlignRight | Qt.AlignVCenter,
        )
        self.batch_time_limit_spin = QSpinBox()
        self.batch_time_limit_spin.setRange(0, 3600)
        self.batch_time_limit_spin.setSingleStep(30)
        self.batch_time_limit_spin.setValue(0)
        self.batch_time_limit_spin.setSpecialValueText(
            i18n.translate("batch_unlimited")
        )
        self.batch_time_limit_spin.setStyleSheet("font-size: 9pt; padding: 4px;")
        params_grid_layout.addWidget(self.batch_time_limit_spin)
        self.batch_seconds_label = QLabel(f"({i18n.translate('batch_seconds')})")
        params_grid_layout.addWidget(
            self.batch_seconds_label,
            alignment=Qt.AlignLeft | Qt.AlignVCenter,
        )

        # Temperature (温度)
        self.batch_temperature_label = QLabel(i18n.translate("batch_temperature"))
        params_grid_layout.addWidget(
            self.batch_temperature_label,
            alignment=Qt.AlignRight | Qt.AlignVCenter,
        )
        from PyQt5.QtWidgets import QDoubleSpinBox

        self.batch_temp_spin = QDoubleSpinBox()
        self.batch_temp_spin.setRange(0.0, 2.0)
        self.batch_temp_spin.setSingleStep(0.1)
        self.batch_temp_spin.setValue(0.8)
        self.batch_temp_spin.setStyleSheet("font-size: 9pt; padding: 4px;")
        params_grid_layout.addWidget(self.batch_temp_spin)
        self.batch_temperature_range_label = QLabel(i18n.translate("batch_temperature_range"))
        params_grid_layout.addWidget(
            self.batch_temperature_range_label,
            alignment=Qt.AlignLeft | Qt.AlignVCenter,
        )

        params_layout.addWidget(self.params_grid)
        self.params_group.setLayout(params_layout)
        layout.addWidget(self.params_group)

        self.setLayout(layout)

    def on_batch_type_changed(self):
        """
        批量类型选择变化时的处理
        """
        batch_type = (
            i18n.translate("batch_discussion")
            if self.discussion_radio.isChecked()
            else i18n.translate("batch_debate")
        )
        self.batch_type_changed.emit(batch_type)

    def get_batch_type(self):
        """
        获取当前选择的批量类型

        Returns:
            str: 批量类型（"讨论"或"辩论"）
        """
        return (
            i18n.translate("batch_discussion")
            if self.discussion_radio.isChecked()
            else i18n.translate("batch_debate")
        )

    def clear_tasks(self):
        """
        清空任务输入
        """
        self.task_edit.clear()
        self.update_task_count()

    def update_task_count(self):
        """
        更新任务数量显示
        """
        tasks = self.task_edit.toPlainText().strip()
        task_list = [task.strip() for task in tasks.split("\n") if task.strip()]
        self.task_count_label.setText(
            f"{i18n.translate('batch_task_count')}: {len(task_list)}"
        )
        self.task_count_changed.emit(len(task_list))

    def get_tasks(self):
        """
        获取任务列表

        Returns:
            list: 任务列表
        """
        tasks = self.task_edit.toPlainText().strip()
        return [task.strip() for task in tasks.split("\n") if task.strip()]

    def get_rounds(self):
        """
        获取轮数

        Returns:
            int: 轮数
        """
        return self.batch_rounds_spin.value()

    def get_time_limit(self):
        """
        获取时间限制

        Returns:
            int: 时间限制（秒）
        """
        return self.batch_time_limit_spin.value()

    def get_temperature(self):
        """
        获取温度

        Returns:
            float: 温度
        """
        return self.batch_temp_spin.value()

    def reinit_ui(self):
        """
        重新初始化UI文本，用于语言切换
        """
        # 更新批量类型选择组
        batch_type_group = self.discussion_radio.parent()
        if isinstance(batch_type_group, QGroupBox):
            batch_type_group.setTitle(i18n.translate("batch_type_selection"))

        # 更新单选按钮文本
        self.discussion_radio.setText(i18n.translate("batch_discussion"))
        self.debate_radio.setText(i18n.translate("batch_debate"))

        # 更新任务输入组
        if hasattr(self, 'task_group'):
            self.task_group.setTitle(i18n.translate("batch_task_input"))

        # 更新任务编辑框占位符
        self.task_edit.setPlaceholderText(i18n.translate("batch_task_placeholder"))

        # 更新按钮文本
        self.clear_tasks_button.setText(i18n.translate("batch_clear_tasks"))

        # 更新处理参数组
        if hasattr(self, 'params_group'):
            self.params_group.setTitle(i18n.translate("batch_processing_params"))

        # 更新参数标签
        self.batch_rounds_label.setText(i18n.translate("batch_rounds"))
        self.batch_time_limit_label.setText(i18n.translate("batch_time_limit"))
        self.batch_seconds_label.setText(f"({i18n.translate('batch_seconds')})")
        self.batch_temperature_label.setText(i18n.translate("batch_temperature"))
        self.batch_temperature_range_label.setText(i18n.translate("batch_temperature_range"))
        
        # 更新时间限制的无限制文本
        self.batch_time_limit_spin.setSpecialValueText(i18n.translate("batch_unlimited"))

        # 更新任务数量显示
        self.update_task_count()
