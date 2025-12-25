# -*- coding: utf-8 -*-"""AI辩论配置面板组件，负责AI模型和API设置"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget as QContainerWidget,
)
from ui.ui_utils import create_group_box, create_combo_box, get_default_styles
from utils.logger_config import get_logger
from utils.model_manager import model_manager
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class AIDebateConfigPanel(QWidget):
    """
    AI辩论配置面板组件

    属性:
        api1_combo: AI1的API选择下拉框
        model1_combo: AI1的模型选择下拉框
        api2_combo: AI2的API选择下拉框
        model2_combo: AI2的模型选择下拉框
        api3_combo: AI3的API选择下拉框
        model3_combo: AI3的模型选择下拉框
    """

    def __init__(self, api_settings_widget):
        """初始化AI辩论配置面板

        Args:
            api_settings_widget: API设置组件，用于获取API配置
        """
        super().__init__()
        self.api_settings_widget = api_settings_widget
        self.styles = get_default_styles()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # AI配置区域
        self.ai_config_group = create_group_box(
            i18n.translate("ai_config"), self.styles["group_box"]
        )
        ai_config_layout = QVBoxLayout()
        ai_config_layout.setContentsMargins(15, 10, 15, 15)
        ai_config_layout.setSpacing(10)

        # AI1配置（正方）
        content_bg1 = "#f8fff8"
        self.ai1_box = self._create_ai_config_box(
            i18n.translate("pro_ai1"),
            "ollama",
            content_bg1,
            "#e8f5e8",
            content_bg1,
            "ai1",
        )  # 边框色与背景色相同
        ai_config_layout.addWidget(self.ai1_box)

        # AI2配置（反方）
        content_bg2 = "#fff8f8"
        self.ai2_box = self._create_ai_config_box(
            i18n.translate("con_ai2"),
            "ollama",
            content_bg2,
            "#ffebee",
            content_bg2,
            "ai2",
        )  # 边框色与背景色相同
        ai_config_layout.addWidget(self.ai2_box)

        # AI3配置（裁判）
        content_bg3 = "#f7fbff"
        self.ai3_box = self._create_ai_config_box(
            i18n.translate("judge_ai3"),
            "ollama",
            content_bg3,
            "#e3f2fd",
            content_bg3,
            "ai3",
        )  # 边框色与背景色相同
        ai_config_layout.addWidget(self.ai3_box)

        self.ai_config_group.setLayout(ai_config_layout)
        layout.addWidget(self.ai_config_group)

        self.setLayout(layout)

        # 初始化模型列表
        self.update_model_list(self.api1_combo, self.model1_combo)
        self.update_model_list(self.api2_combo, self.model2_combo)
        self.update_model_list(self.api3_combo, self.model3_combo)

    def _create_ai_config_box(
        self,
        title: str,
        default_api: str,
        border_color: str,
        background_color: str,
        content_bg: str,
        ai_id: str,
    ) -> QContainerWidget:
        """创建AI配置框

        Args:
            title: AI名称
            default_api: 默认API类型
            border_color: 边框颜色
            background_color: 背景颜色
            content_bg: 内容背景色
            ai_id: AI标识符（ai1, ai2, ai3）

        Returns:
            QWidget: AI配置框
        """
        ai_box = QContainerWidget()
        ai_box.setStyleSheet(
            f"""QWidget {{
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 10px;
                background-color: {content_bg};
            }}
        """
        )

        ai_layout = QHBoxLayout(ai_box)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(10)

        # 保存AI标题标签
        ai_title_label = QLabel(title)
        ai_layout.addWidget(ai_title_label, alignment=Qt.AlignVCenter)

        # 保存AI标题标签作为实例变量
        setattr(self, f"{ai_id}_title_label", ai_title_label)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.setSpacing(5)
        model_label = QLabel(i18n.translate("model") + ":")
        model_layout.addWidget(model_label, alignment=Qt.AlignVCenter)

        # 保存模型标签作为实例变量
        setattr(self, f"{ai_id}_model_label", model_label)

        # 创建模型下拉框
        model_combo = create_combo_box(style_sheet=self.styles["combo_box"])
        model_combo.setFixedWidth(270)
        model_layout.addWidget(model_combo)

        # 保存模型下拉框作为实例变量
        setattr(self, f"model{ai_id[-1]}_combo", model_combo)

        ai_layout.addLayout(model_layout)

        # API选择
        api_layout = QHBoxLayout()
        api_layout.setSpacing(5)
        api_provider_label = QLabel(i18n.translate("model_provider") + ":")
        api_layout.addWidget(api_provider_label, alignment=Qt.AlignVCenter)

        # 保存API提供商标签作为实例变量
        setattr(self, f"{ai_id}_api_provider_label", api_provider_label)

        # 创建API下拉框并连接信号
        api_combo = create_combo_box(
            ["ollama", "openai", "deepseek"], default_api, self.styles["combo_box"]
        )
        api_combo.setFixedWidth(180)

        # 根据AI ID保存API下拉框和连接信号
        if ai_id == "ai1":
            self.api1_combo = api_combo
            self.api1_combo.currentTextChanged.connect(
                lambda text: self.update_model_list(self.api1_combo, self.model1_combo)
            )
        elif ai_id == "ai2":
            self.api2_combo = api_combo
            self.api2_combo.currentTextChanged.connect(
                lambda text: self.update_model_list(self.api2_combo, self.model2_combo)
            )
        elif ai_id == "ai3":
            self.api3_combo = api_combo
            self.api3_combo.currentTextChanged.connect(
                lambda text: self.update_model_list(self.api3_combo, self.model3_combo)
            )

        api_layout.addWidget(api_combo)
        ai_layout.addLayout(api_layout)

        ai_layout.addStretch()

        return ai_box

    def update_model_list(self, api_combo, model_combo):
        """
        根据当前选择的API从真实API获取并更新模型列表

        Args:
            api_combo: API选择下拉框
            model_combo: 模型选择下拉框
        """
        api = api_combo.currentText()
        logger.info(f"更新辩论模型列表，当前API: {api}")

        # 清空现有模型列表
        model_combo.clear()

        # 添加加载提示
        model_combo.addItem(i18n.translate("loading"))

        if api == "ollama":
            # 从ModelManager异步获取Ollama模型列表
            from ui.api_settings import APISettingsWidget

            api_settings = APISettingsWidget()
            base_url = api_settings.get_ollama_base_url()

            def on_models_loaded(models):
                """模型加载完成后的回调函数"""
                self._on_models_loaded(model_combo, api, models)

            def on_load_error(error):
                """模型加载失败后的回调函数"""
                logger.error(f"异步加载模型列表失败: {error}")
                self._on_models_loaded(model_combo, api, [])

            model_manager.async_load_ollama_models(
                base_url, on_models_loaded, on_load_error
            )
        else:
            # 非Ollama API，使用同步加载
            models = []
            try:
                if api == "openai":
                    # 这里可以添加从OpenAI API获取模型列表的逻辑
                    models = ["gpt-4", "gpt-4o", "gpt-3.5-turbo"]
                elif api == "deepseek":
                    # 这里可以添加从DeepSeek API获取模型列表的逻辑
                    models = ["deepseek-chat", "deepseek-coder"]
            except Exception as e:
                logger.error(f"获取{api}模型列表失败: {str(e)}")
                # 如果API调用失败，使用默认模型列表
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
        default_model = ""
        if model_combo is self.model1_combo:
            # 正方AI1默认模型
            default_model = "deepseek-v3.1:671b-cloud"
        elif model_combo is self.model2_combo:
            # 反方AI2默认模型
            default_model = "qwen3-vl:235b-instruct-cloud"
        elif model_combo is self.model3_combo:
            # 裁判AI3默认模型
            default_model = "gpt-oss:120b-cloud"

        # 查找并选择默认模型
        if default_model and default_model in models:
            model_combo.setCurrentText(default_model)
            logger.info(f"模型列表更新完成，当前模型: {default_model}")
        # 如果默认模型不存在，选择第一个模型
        elif model_combo.count() > 0:
            model_combo.setCurrentIndex(0)
            logger.info(f"模型列表更新完成，当前模型: {model_combo.currentText()}")
        else:
            logger.warning(f"模型列表更新后为空，API: {api}")

    def get_ai1_config(self) -> tuple:
        """获取AI1配置

        Returns:
            tuple: (api, model)
        """
        return self.api1_combo.currentText(), self.model1_combo.currentText()

    def get_ai2_config(self) -> tuple:
        """获取AI2配置

        Returns:
            tuple: (api, model)
        """
        return self.api2_combo.currentText(), self.model2_combo.currentText()

    def get_ai3_config(self) -> tuple:
        """获取AI3配置

        Returns:
            tuple: (api, model)
        """
        return self.api3_combo.currentText(), self.model3_combo.currentText()

    def reinit_ui(self):
        """重新初始化UI，用于语言切换时更新界面"""
        # 更新AI配置组标题
        self.ai_config_group.setTitle(i18n.translate("ai_config"))

        # 更新AI1配置
        self.ai1_title_label.setText(i18n.translate("pro_ai1"))
        self.ai1_model_label.setText(i18n.translate("model") + ":")
        self.ai1_api_provider_label.setText(i18n.translate("model_provider") + ":")

        # 更新AI2配置
        self.ai2_title_label.setText(i18n.translate("con_ai2"))
        self.ai2_model_label.setText(i18n.translate("model") + ":")
        self.ai2_api_provider_label.setText(i18n.translate("model_provider") + ":")

        # 更新AI3配置
        self.ai3_title_label.setText(i18n.translate("judge_ai3"))
        self.ai3_model_label.setText(i18n.translate("model") + ":")
        self.ai3_api_provider_label.setText(i18n.translate("model_provider") + ":")

        # 更新模型加载提示
        for i in range(1, 4):
            model_combo = getattr(self, f"model{i}_combo")
            if model_combo.count() > 0 and model_combo.itemText(0) == i18n.translate(
                "loading"
            ):
                model_combo.setItemText(0, i18n.translate("loading"))
