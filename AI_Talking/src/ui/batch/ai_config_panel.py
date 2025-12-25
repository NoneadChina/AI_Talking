# -*- coding: utf-8 -*-
"""
AI批量配置面板组件，负责AI模型和API设置
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget as QContainerWidget,
)
from ui.ui_utils import create_combo_box, get_default_styles
from utils.logger_config import get_logger
from utils.model_manager import model_manager
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class AIBatchConfigPanel(QWidget):
    """
    AI批量配置面板组件

    属性:
        api1_combo: AI1的API选择下拉框
        model1_combo: AI1的模型选择下拉框
        api2_combo: AI2的API选择下拉框
        model2_combo: AI2的模型选择下拉框
        api3_combo: AI3的API选择下拉框
        model3_combo: AI3的模型选择下拉框
    """

    def __init__(self, api_settings_widget):
        """初始化AI批量配置面板

        Args:
            api_settings_widget: API设置组件，用于获取API配置
        """
        super().__init__()
        self.api_settings_widget = api_settings_widget
        self.styles = get_default_styles()
        self.init_ui()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # AI配置区域
        ai_config_group = QWidget()
        ai_config_layout = QVBoxLayout(ai_config_group)
        ai_config_layout.setContentsMargins(0, 0, 0, 0)
        ai_config_layout.setSpacing(12)

        # AI1配置
        self.ai1_box = QWidget()
        self.ai1_box.setStyleSheet(
            "border: 1px solid #e3f2fd; border-radius: 4px; padding: 8px; background-color: #f7fbff;"
        )
        ai1_layout = QHBoxLayout(self.ai1_box)
        ai1_layout.setContentsMargins(0, 0, 0, 0)
        ai1_layout.setSpacing(15)

        # 将AI1标签存储为实例变量，以便后续修改
        self.ai1_label = QLabel(i18n.translate("scholar_ai1"))
        ai1_layout.addWidget(self.ai1_label, alignment=Qt.AlignVCenter)

        ai1_api_layout = QHBoxLayout()
        self.ai1_api_label = QLabel(i18n.translate("model_provider"))
        ai1_api_layout.addWidget(
            self.ai1_api_label, alignment=Qt.AlignVCenter
        )
        self.batch_ai1_api_combo = create_combo_box(
            ["ollama", "openai", "deepseek"], "ollama", self.styles["combo_box"]
        )
        self.batch_ai1_api_combo.setFixedWidth(180)
        self.batch_ai1_api_combo.currentTextChanged.connect(self.update_ai1_model_list)
        ai1_api_layout.addWidget(self.batch_ai1_api_combo)
        ai1_layout.addLayout(ai1_api_layout)

        ai1_model_layout = QHBoxLayout()
        self.ai1_model_label = QLabel(i18n.translate("model") + ":")
        ai1_model_layout.addWidget(
            self.ai1_model_label, alignment=Qt.AlignVCenter
        )
        self.batch_ai1_model_combo = create_combo_box(
            style_sheet=self.styles["combo_box"]
        )
        self.batch_ai1_model_combo.setFixedWidth(270)
        ai1_model_layout.addWidget(self.batch_ai1_model_combo)
        ai1_layout.addLayout(ai1_model_layout)
        ai1_layout.addStretch()
        ai_config_layout.addWidget(self.ai1_box)

        # AI2配置
        self.ai2_box = QWidget()
        self.ai2_box.setStyleSheet(
            "border: 1px solid #f3e5f5; border-radius: 4px; padding: 8px; background-color: #fcf8ff;"
        )
        ai2_layout = QHBoxLayout(self.ai2_box)
        ai2_layout.setContentsMargins(0, 0, 0, 0)
        ai2_layout.setSpacing(15)

        # 将AI2标签存储为实例变量，以便后续修改
        self.ai2_label = QLabel(i18n.translate("scholar_ai2"))
        ai2_layout.addWidget(self.ai2_label, alignment=Qt.AlignVCenter)

        ai2_api_layout = QHBoxLayout()
        self.ai2_api_label = QLabel(i18n.translate("model_provider"))
        ai2_api_layout.addWidget(
            self.ai2_api_label, alignment=Qt.AlignVCenter
        )
        self.batch_ai2_api_combo = create_combo_box(
            ["ollama", "openai", "deepseek"], "ollama", self.styles["combo_box"]
        )
        self.batch_ai2_api_combo.setFixedWidth(180)
        self.batch_ai2_api_combo.currentTextChanged.connect(self.update_ai2_model_list)
        ai2_api_layout.addWidget(self.batch_ai2_api_combo)
        ai2_layout.addLayout(ai2_api_layout)

        ai2_model_layout = QHBoxLayout()
        self.ai2_model_label = QLabel(i18n.translate("model") + ":")
        ai2_model_layout.addWidget(
            self.ai2_model_label, alignment=Qt.AlignVCenter
        )
        self.batch_ai2_model_combo = create_combo_box(
            style_sheet=self.styles["combo_box"]
        )
        self.batch_ai2_model_combo.setFixedWidth(270)
        ai2_model_layout.addWidget(self.batch_ai2_model_combo)
        ai2_layout.addLayout(ai2_model_layout)
        ai2_layout.addStretch()
        ai_config_layout.addWidget(self.ai2_box)

        # AI3配置
        self.ai3_box = QWidget()
        self.ai3_box.setStyleSheet(
            "border: 1px solid #e8f5e8; border-radius: 4px; padding: 8px; background-color: #f1f8e9;"
        )
        self.ai3_layout = QHBoxLayout(self.ai3_box)
        self.ai3_layout.setContentsMargins(0, 0, 0, 0)
        self.ai3_layout.setSpacing(15)

        # 根据批量类型动态显示不同的AI3标签
        self.ai3_label = QLabel(i18n.translate("expert_ai3"))
        self.ai3_layout.addWidget(self.ai3_label, alignment=Qt.AlignVCenter)

        self.ai3_api_layout = QHBoxLayout()
        self.ai3_api_label = QLabel(i18n.translate("model_provider"))
        self.ai3_api_layout.addWidget(
            self.ai3_api_label, alignment=Qt.AlignVCenter
        )
        self.batch_ai3_api_combo = create_combo_box(
            ["ollama", "openai", "deepseek"], "ollama", self.styles["combo_box"]
        )
        self.batch_ai3_api_combo.setFixedWidth(180)
        self.batch_ai3_api_combo.currentTextChanged.connect(self.update_ai3_model_list)
        self.ai3_api_layout.addWidget(self.batch_ai3_api_combo)
        self.ai3_layout.addLayout(self.ai3_api_layout)

        self.ai3_model_layout = QHBoxLayout()
        self.ai3_model_label = QLabel(i18n.translate("model") + ":")
        self.ai3_model_layout.addWidget(
            self.ai3_model_label, alignment=Qt.AlignVCenter
        )
        self.batch_ai3_model_combo = create_combo_box(
            style_sheet=self.styles["combo_box"]
        )
        self.batch_ai3_model_combo.setFixedWidth(270)
        self.ai3_model_layout.addWidget(self.batch_ai3_model_combo)
        self.ai3_layout.addLayout(self.ai3_model_layout)
        self.ai3_layout.addStretch()
        ai_config_layout.addWidget(self.ai3_box)

        layout.addWidget(ai_config_group)
        self.setLayout(layout)

        # 初始化模型列表
        self.update_ai1_model_list()  # 刷新AI1模型列表
        self.update_ai2_model_list()  # 刷新AI2模型列表
        self.update_ai3_model_list()  # 刷新AI3模型列表

    def update_ai1_model_list(self):
        """
        更新AI1模型列表
        """
        self._update_model_list(self.batch_ai1_api_combo, self.batch_ai1_model_combo)

    def update_ai2_model_list(self):
        """
        更新AI2模型列表
        """
        self._update_model_list(self.batch_ai2_api_combo, self.batch_ai2_model_combo)

    def update_ai3_model_list(self):
        """
        更新AI3模型列表
        """
        self._update_model_list(self.batch_ai3_api_combo, self.batch_ai3_model_combo)

    def _update_model_list(self, api_combo, model_combo):
        """
        更新模型列表的通用方法（异步版）

        Args:
            api_combo: API下拉框
            model_combo: 模型下拉框
        """
        api = api_combo.currentText()
        logger.info(f"更新批量模型列表，当前API: {api}")

        # 清空现有模型列表并显示加载提示
        model_combo.clear()
        model_combo.addItem("加载中...")

        if api == "ollama":
            # 异步加载Ollama模型
            base_url = self.api_settings_widget.get_ollama_base_url()

            def on_models_loaded(models):
                self._on_models_loaded(model_combo, api, models)

            def on_load_error(error):
                logger.error(f"批量模型加载失败: {error}")
                self._on_models_loaded(model_combo, api, [])

            model_manager.async_load_ollama_models(
                base_url, on_models_loaded, on_load_error
            )
        else:
            # 非Ollama API，使用同步加载
            models = []
            try:
                if api == "openai":
                    models = ["gpt-4", "gpt-4o", "gpt-3.5-turbo"]
                elif api == "deepseek":
                    models = ["deepseek-chat", "deepseek-coder"]
            except Exception as e:
                logger.error(f"获取{api}模型列表失败: {str(e)}")
                if api == "openai":
                    models = ["gpt-4", "gpt-4o", "gpt-3.5-turbo"]
                elif api == "deepseek":
                    models = ["deepseek-chat", "deepseek-coder"]

            self._on_models_loaded(model_combo, api, models)

    def _on_models_loaded(self, model_combo, api, models):
        """
        模型加载完成后的处理方法

        Args:
            model_combo: 模型下拉框
            api: API类型
            models: 加载的模型列表
        """
        # 清空模型列表（包括加载提示）
        model_combo.clear()

        # 检查模型列表是否为空
        if not models:
            logger.error(f"模型列表为空，API: {api}")
            # 如果API调用失败，使用默认模型列表
            if api == "ollama":
                models = [
                    "qwen3:14b",
                    "llama2:7b",
                    "mistral:7b",
                    "gemma:2b",
                    "deepseek-v2:16b",
                ]
            elif api == "openai":
                models = ["gpt-4", "gpt-4o", "gpt-3.5-turbo"]
            elif api == "deepseek":
                models = ["deepseek-chat", "deepseek-coder"]

        # 添加模型列表
        if models:
            model_combo.addItems(models)
            logger.info(f"添加{api}模型: {models}")

        # 设置默认模型
        if model_combo.count() > 0:
            model_combo.setCurrentIndex(0)
            logger.info(f"批量模型列表更新完成，当前模型: {model_combo.currentText()}")
        else:
            logger.warning(f"批量模型列表更新后为空，API: {api}")

    def update_model_list(self, ai_type):
        """
        根据AI类型更新模型列表

        Args:
            ai_type: AI类型，可选值："ai1", "ai2", "ai3"
        """
        if ai_type == "ai1":
            self.update_ai1_model_list()
        elif ai_type == "ai2":
            self.update_ai2_model_list()
        elif ai_type == "ai3":
            self.update_ai3_model_list()

    def on_batch_type_changed(self, batch_type):
        """
        批量类型变化时的处理
        更新AI1、AI2和AI3标签和配置

        Args:
            batch_type: 批量类型（"讨论"或"辩论"）
        """
        if batch_type == i18n.translate("discussion"):
            # 讨论模式
            self.ai1_label.setText(i18n.translate("scholar_ai1"))
            self.ai2_label.setText(i18n.translate("scholar_ai2"))
            self.ai3_label.setText(i18n.translate("expert_ai3"))
            self.ai3_box.setStyleSheet(
                "border: 1px solid #e8f5e8; border-radius: 4px; padding: 8px; background-color: #f1f8e9;"
            )
        elif batch_type == i18n.translate("debate"):
            # 辩论模式
            self.ai1_label.setText(i18n.translate("pro_ai1"))
            self.ai2_label.setText(i18n.translate("con_ai2"))
            self.ai3_label.setText(i18n.translate("referee_ai3"))
            self.ai3_box.setStyleSheet(
                "border: 1px solid #fff3e0; border-radius: 4px; padding: 8px; background-color: #f9fbe7;"
            )

    def get_ai1_config(self):
        """
        获取AI1配置

        Returns:
            tuple: (api, model)
        """
        return (
            self.batch_ai1_api_combo.currentText(),
            self.batch_ai1_model_combo.currentText(),
        )

    def get_ai2_config(self):
        """
        获取AI2配置

        Returns:
            tuple: (api, model)
        """
        return (
            self.batch_ai2_api_combo.currentText(),
            self.batch_ai2_model_combo.currentText(),
        )

    def get_ai3_config(self):
        """
        获取AI3配置

        Returns:
            tuple: (api, model)
        """
        return (
            self.batch_ai3_api_combo.currentText(),
            self.batch_ai3_model_combo.currentText(),
        )

    def reinit_ui(self):
        """
        重新初始化UI文本，用于语言切换
        """
        # 由于无法直接获取批量类型，我们保持当前标签不变，但更新其他UI元素
        
        # 更新AI标签
        if hasattr(self, 'ai1_label'):
            self.ai1_label.setText(i18n.translate("scholar_ai1"))
        if hasattr(self, 'ai2_label'):
            self.ai2_label.setText(i18n.translate("scholar_ai2"))
        if hasattr(self, 'ai3_label'):
            self.ai3_label.setText(i18n.translate("expert_ai3"))

        # 更新AI1配置
        if hasattr(self, 'ai1_api_label'):
            self.ai1_api_label.setText(i18n.translate("model_provider"))
        if hasattr(self, 'ai1_model_label'):
            self.ai1_model_label.setText(i18n.translate("model") + ":")

        # 更新AI2配置
        if hasattr(self, 'ai2_api_label'):
            self.ai2_api_label.setText(i18n.translate("model_provider"))
        if hasattr(self, 'ai2_model_label'):
            self.ai2_model_label.setText(i18n.translate("model") + ":")

        # 更新AI3配置
        if hasattr(self, 'ai3_api_label'):
            self.ai3_api_label.setText(i18n.translate("model_provider"))
        if hasattr(self, 'ai3_model_label'):
            self.ai3_model_label.setText(i18n.translate("model") + ":")
