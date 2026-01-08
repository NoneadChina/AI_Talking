# -*- coding: utf-8 -*-
"""
聊天标签页组件，用于实现AI聊天功能
"""

import sys
import os
import time
import threading
import markdown
from utils.logger_config import get_logger
from utils.config_manager import config_manager
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
    QDoubleSpinBox,
    QGroupBox,
    QMessageBox,
    QFileDialog,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 获取日志记录器
logger = get_logger(__name__)

# 导入国际化管理器
from utils.i18n_manager import i18n

# 从chat子包导入组件
from .chat import (
    ChatInputWidget,
    ChatMessageWidget,
    ChatListWidget,
    ConfigPanel,
    ControlsPanel,
    AIConfigPanel,
)


class ChatTabWidget(QWidget):
    """
    聊天标签页组件，用于实现AI聊天功能

    信号:
        update_signal: 更新聊天历史信号，参数为(发送者, 内容, 模型名称)
    """

    # 定义信号
    update_signal = pyqtSignal(str, str, str)

    def __init__(self, api_settings_widget):
        """
        初始化聊天标签页组件

        Args:
            api_settings_widget: API设置组件，用于获取API配置
        """
        super().__init__()

        self.api_settings_widget = api_settings_widget

        # 聊天历史内存优化设置
        self.max_standard_chat_history = 30  # 设置标准聊天历史的最大消息数量

        # 标准聊天历史存储（用于API调用）
        self.standard_chat_history_messages = (
            []
        )  # 存储完整的聊天历史消息，包含系统提示词

        # 聊天状态管理
        self.is_ai_responding = False  # 标记AI是否正在回复
        self.pending_messages = []  # 存储待发送的消息队列
        self.just_cleared_history = False  # 标记是否刚刚清空了历史

        # 初始化UI
        self.init_ui()

        # 连接语言变化信号
        from utils.i18n_manager import i18n

        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """
        初始化聊天标签页UI
        """
        # 创建主布局
        layout = QVBoxLayout()

        # 聊天配置区域
        self.chat_config_group = QGroupBox(i18n.translate("chat_config"))
        self.chat_config_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
        chat_config_layout = QHBoxLayout()
        chat_config_layout.setContentsMargins(10, 5, 10, 10)
        chat_config_layout.setSpacing(15)

        # API和模型配置行
        api_model_layout = QHBoxLayout()
        api_model_layout.setSpacing(8)

        # API选择
        api_layout = QHBoxLayout()
        api_layout.setSpacing(5)
        self.api_provider_label = QLabel(i18n.translate("chat_model_provider"))
        api_layout.addWidget(self.api_provider_label, alignment=Qt.AlignVCenter)
        self.chat_api_combo = QComboBox()
        self.chat_api_combo.addItems(["Ollama", "OpenAI", "DeepSeek", "Ollama Cloud"])
        self.chat_api_combo.setCurrentText("Ollama")  # 默认选择Ollama API
        self.chat_api_combo.setStyleSheet(
            "font-size: 9pt; padding: 4px; border: 1px solid #ddd; border-radius: 6px;"
        )
        # 连接API变化信号到模型更新方法
        self.chat_api_combo.currentIndexChanged.connect(self.on_chat_api_changed)
        api_layout.addWidget(self.chat_api_combo)
        api_model_layout.addLayout(api_layout)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.setSpacing(5)
        self.model_label = QLabel(i18n.translate("chat_model"))
        model_layout.addWidget(self.model_label, alignment=Qt.AlignVCenter)
        self.chat_model_combo = QComboBox()
        self.chat_model_combo.setFixedWidth(250)
        self.chat_model_combo.setStyleSheet(
            "font-size: 9pt; padding: 4px; border: 1px solid #ddd; border-radius: 6px;"
        )
        self.update_chat_model_list()  # 初始化模型列表
        model_layout.addWidget(self.chat_model_combo)
        api_model_layout.addLayout(model_layout)

        # 温度调节功能
        temp_layout = QHBoxLayout()
        temp_layout.setSpacing(5)
        self.temperature_label = QLabel(i18n.translate("chat_temperature"))
        temp_layout.addWidget(self.temperature_label, alignment=Qt.AlignVCenter)
        self.chat_temperature_spin = QDoubleSpinBox()
        self.chat_temperature_spin.setRange(0.0, 2.0)
        self.chat_temperature_spin.setSingleStep(0.1)
        self.chat_temperature_spin.setValue(0.8)  # 默认温度设置
        self.chat_temperature_spin.setToolTip(
            i18n.translate("chat_temperature_tooltip")
        )
        self.chat_temperature_spin.setStyleSheet(
            "font-size: 9pt; padding: 4px; border: 1px solid #ddd; border-radius: 6px;"
        )
        temp_layout.addWidget(self.chat_temperature_spin)
        self.temperature_range_label = QLabel(i18n.translate("chat_temperature_range"))
        temp_layout.addWidget(self.temperature_range_label, alignment=Qt.AlignVCenter)

        # 添加拉伸空间，将logo推到最右侧
        temp_layout.addStretch(1)

        # 添加NONEAD Logo
        import os
        import sys
        from PyQt5.QtGui import QPixmap

        # 获取当前目录
        if getattr(sys, "frozen", False):
            # 打包后的可执行文件所在目录
            current_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境下的当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            current_dir = os.path.dirname(current_dir)  # 向上一级目录
            current_dir = os.path.dirname(current_dir)  # 再向上一级目录

        # 创建Logo标签
        logo_label = QLabel()
        # 使用资源管理器加载并缩放logo
        from utils.resource_manager import ResourceManager
        pixmap = ResourceManager.load_pixmap("noneadLogo.png", 200, 60)
        if pixmap:
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            # logo加载失败，显示文本标识
            logo_label.setText("NONEAD")
            logo_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            logo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            logo_label.setStyleSheet("color: #333;")
        # 添加logo到布局
        temp_layout.addWidget(logo_label, alignment=Qt.AlignVCenter)

        api_model_layout.addLayout(temp_layout)

        chat_config_layout.addLayout(api_model_layout)

        self.chat_config_group.setLayout(chat_config_layout)
        layout.addWidget(self.chat_config_group)

        # 聊天历史区域
        self.chat_list_widget = ChatListWidget()
        layout.addWidget(self.chat_list_widget, 1)  # 设置权重为1，占据剩余空间

        # 聊天输入区域
        self.chat_input_widget = ChatInputWidget()
        self.chat_input_widget.send_message.connect(self.send_chat_message)
        layout.addWidget(self.chat_input_widget)

        # 聊天控制区域
        self.chat_control_group = QGroupBox(i18n.translate("chat_control"))
        self.chat_control_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
        chat_control_layout = QHBoxLayout()
        chat_control_layout.setContentsMargins(10, 5, 10, 10)
        chat_control_layout.setSpacing(10)

        # 控制按钮样式
        button_style = """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:focus {
                outline: none;
                border-color: #4caf50;
            }
        """

        # 保存历史按钮
        self.save_standard_history_button = QPushButton(
            i18n.translate("chat_save_history")
        )
        self.save_standard_history_button.clicked.connect(
            self.save_standard_chat_history
        )
        self.save_standard_history_button.setStyleSheet(button_style)
        chat_control_layout.addWidget(self.save_standard_history_button)

        # 加载历史按钮
        self.load_standard_history_button = QPushButton(
            i18n.translate("chat_load_history")
        )
        self.load_standard_history_button.clicked.connect(
            self.load_standard_chat_history
        )
        self.load_standard_history_button.setStyleSheet(button_style)
        chat_control_layout.addWidget(self.load_standard_history_button)

        # 导出PDF按钮
        self.export_chat_pdf_button = QPushButton(i18n.translate("chat_export_pdf"))
        self.export_chat_pdf_button.clicked.connect(self.export_chat_history_to_pdf)
        self.export_chat_pdf_button.setStyleSheet(button_style)
        chat_control_layout.addWidget(self.export_chat_pdf_button)

        # 清除历史按钮
        self.clear_history_button = QPushButton(i18n.translate("chat_clear_history"))
        self.clear_history_button.clicked.connect(self.clear_chat_history)
        self.clear_history_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #ffebee;
                font-size: 9pt;
                color: #c62828;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
            QPushButton:focus {
                outline: none;
                border-color: #f44336;
            }
        """
        )
        chat_control_layout.addWidget(self.clear_history_button)

        chat_control_layout.addStretch(1)  # 添加拉伸空间，将按钮推到左侧
        self.chat_control_group.setLayout(chat_control_layout)
        layout.addWidget(self.chat_control_group)

        self.setLayout(layout)

    def on_chat_api_changed(self, index):
        """
        API选择变化时的处理方法

        Args:
            index: 新选择的API索引
        """
        api = self.chat_api_combo.currentText()
        logger.info(f"API选择变化，索引: {index}，API: {api}")
        self.update_chat_model_list()

    def update_chat_model_list(self):
        """
        根据当前选择的API从真实API获取并更新模型列表
        """
        from utils.model_manager import model_manager

        api = self.chat_api_combo.currentText()
        logger.info(f"更新聊天模型列表，当前API: {api}")

        # 清空现有模型列表
        self.chat_model_combo.clear()

        # 添加加载提示
        self.chat_model_combo.addItem("加载中...")

        if api == "Ollama":
            # 异步加载Ollama模型
            base_url = self.api_settings_widget.get_ollama_base_url()

            def on_models_loaded(models):
                self._on_chat_models_loaded(api, models)

            def on_load_error(error):
                logger.error(f"聊天Ollama模型加载失败: {error}")
                self._on_chat_models_loaded(api, [])

            model_manager.async_load_ollama_models(
                base_url, on_models_loaded, on_load_error
            )
        elif api == "Ollama Cloud":
            # 异步加载Ollama Cloud模型
            def on_models_loaded(models):
                self._on_chat_models_loaded(api, models)

            def on_load_error(error):
                logger.error(f"聊天Ollama Cloud模型加载失败: {error}")
                self._on_chat_models_loaded(api, [])

            model_manager.async_load_ollama_cloud_models(
                on_models_loaded, on_load_error
            )
        else:
            # 非Ollama API，使用同步加载
            models = []
            try:
                from utils.ai_service import AIServiceFactory
                
                if api == "OpenAI":
                    api_key = self.api_settings_widget.get_openai_api_key()
                    ai_service = AIServiceFactory.create_ai_service("openai", api_key=api_key)
                    models = ai_service.get_models()
                elif api == "DeepSeek":
                    api_key = self.api_settings_widget.get_deepseek_api_key()
                    ai_service = AIServiceFactory.create_ai_service("deepseek", api_key=api_key)
                    models = ai_service.get_models()
            except Exception as e:
                logger.error(f"获取{api}模型列表失败: {str(e)}")
                if api == "OpenAI":
                    models = ["gpt-4", "gpt-4o", "gpt-3.5-turbo"]
                elif api == "DeepSeek":
                    models = ["deepseek-chat", "deepseek-coder"]

            self._on_chat_models_loaded(api, models)

    def _on_chat_models_loaded(self, api, models):
        """
        聊天模型加载完成后的处理方法
        """
        # 清空模型列表（包括加载提示）
        self.chat_model_combo.clear()

        # 检查模型列表是否为空
        if not models:
            logger.error(f"聊天模型列表为空，API: {api}")
            # 如果API调用失败，使用默认模型列表
            if api == "Ollama":
                models = [
                    "qwen3:14b",
                    "llama2:7b",
                    "mistral:7b",
                    "gemma:2b",
                    "deepseek-v2:16b",
                ]
            elif api == "OpenAI":
                models = ["gpt-4", "gpt-4o", "gpt-3.5-turbo"]
            elif api == "DeepSeek":
                models = ["deepseek-chat", "deepseek-coder"]
            elif api == "Ollama Cloud":
                models = ["llama3:70b", "llama3:8b", "gemma:7b", "mistral:7b"]

        # 分类模型：云端模型（包含'cloud'）在上，本地模型在下
        if models:
            # 分离云端模型和本地模型
            cloud_models = [model for model in models if 'cloud' in model.lower()]
            local_models = [model for model in models if 'cloud' not in model.lower()]
            
            # 合并分类后的模型列表（云端模型在前，本地模型在后）
            sorted_models = cloud_models + local_models
            
            # 添加分类后的模型列表
            self.chat_model_combo.addItems(sorted_models)
            logger.info(f"添加{api}分类模型: 云端{len(cloud_models)}个，本地{len(local_models)}个")

        # 设置默认模型为gpt-oss:120b-cloud
        if self.chat_model_combo.count() > 0:
            target_model = "gpt-oss:120b-cloud"
            if target_model in models:
                self.chat_model_combo.setCurrentText(target_model)
                logger.info(f"模型列表更新完成，当前模型: {target_model}")
            else:
                # 如果目标模型不存在，使用第一个模型
                self.chat_model_combo.setCurrentIndex(0)
                logger.info(
                    f"模型列表更新完成，当前模型: {self.chat_model_combo.currentText()}"
                )
        else:
            logger.warning(f"模型列表更新后为空，API: {api}")

    def send_chat_message(self, original_message, full_message):
        """
        发送聊天消息到AI并显示回复
        如果AI正在回复，则将消息加入队列，等待AI回复完成后再发送
        
        参数:
            original_message: 原始消息（用于显示在聊天历史中）
            full_message: 完整消息（用于发送给模型，包含文件解析内容）
        """
        if not original_message:
            return

        # 显示用户消息（只显示原始消息，不包含文件解析内容）
        from utils.i18n_manager import i18n
        user_text = i18n.translate('user')
        thinking_text = i18n.translate('thinking')
        self.chat_list_widget.append_message(user_text, original_message)

        # 如果AI正在回复，将消息加入队列（需要存储两个参数）
        if self.is_ai_responding:
            self.pending_messages.append((original_message, full_message))
            logger.info(
                f"AI正在回复，消息已加入队列，当前队列长度: {len(self.pending_messages)}"
            )
            return

        # 显示"正在思考..."状态
        self.chat_list_widget.append_message("AI", thinking_text)

        # 标记AI正在回复
        self.is_ai_responding = True

        # 使用threading.Thread创建线程发送消息，避免阻塞UI
        thread = threading.Thread(
            target=self._send_chat_message_thread, args=(full_message,)
        )
        thread.daemon = True  # 设置为守护线程，程序退出时自动结束
        thread.start()

    def _send_chat_message_thread(self, message):
        """
        在后台线程发送聊天消息
        """
        from utils.ai_service import AIServiceFactory

        try:
            # 获取API和模型信息
            api = self.chat_api_combo.currentText()
            model = self.chat_model_combo.currentText()
            temperature = self.chat_temperature_spin.value()

            # 记录聊天历史的长度
            logger.info(
                f"发送消息时的聊天历史长度: {len(self.standard_chat_history_messages)}"
            )
            logger.info(f"当前发送的消息: {message}")

            # 获取聊天系统提示词（从配置文件读取，确保使用最新的设置）
            chat_system_prompt = config_manager.get(
                "chat.system_prompt", "请使用简体中文回答"
            ).strip()

            # 检查聊天历史是否为空，如果为空则添加系统提示词
            if not self.standard_chat_history_messages:
                if chat_system_prompt:
                    self.standard_chat_history_messages.append(
                        {"role": "system", "content": chat_system_prompt}
                    )

            # 将用户消息添加到聊天历史
            self.standard_chat_history_messages.append(
                {"role": "user", "content": message}
            )

            # 严格按照用户选择的API类型来决定使用哪个服务
            # 不管模型名称是什么，只要用户选择了Ollama，就使用Ollama服务
            # 不管模型名称是什么，只要用户选择了Ollama Cloud，就使用Ollama Cloud服务
            if api == "Ollama":
                base_url = self.api_settings_widget.get_ollama_base_url()
                ai_service = AIServiceFactory.create_ai_service(
                    "ollama", base_url=base_url
                )
            elif api == "OpenAI":
                api_key = self.api_settings_widget.get_openai_api_key()
                ai_service = AIServiceFactory.create_ai_service(
                    "openai", api_key=api_key
                )
            elif api == "DeepSeek":
                api_key = self.api_settings_widget.get_deepseek_api_key()
                ai_service = AIServiceFactory.create_ai_service(
                    "deepseek", api_key=api_key
                )
            elif api == "Ollama Cloud":
                api_key = self.api_settings_widget.ollama_cloud_key_edit.text().strip()
                # 使用 Ollama Cloud 服务 URL
                base_url = self.api_settings_widget.get_ollama_cloud_base_url()
                ai_service = AIServiceFactory.create_ai_service(
                    "ollama_cloud", api_key=api_key, base_url=base_url
                )
            else:
                raise ValueError(f"不支持的API类型: {api}")

            # 发送消息并处理响应
            ai_response = ""

            # 使用流式响应
            stream_generator = ai_service.chat_completion(
                messages=self.standard_chat_history_messages,
                model=model,
                temperature=temperature,
                stream=True,
            )

            # 处理流式响应
            for partial_response in stream_generator:
                ai_response = partial_response
                # 使用信号更新UI，实现流式输出
                self.update_signal.emit("AI", ai_response, model)
                self.chat_list_widget.append_message("AI", ai_response, model)

            # 将完整的AI回复添加到聊天历史
            self.standard_chat_history_messages.append(
                {"role": "assistant", "content": ai_response}
            )

            # 优化内存使用：如果历史记录超过限制，只保留最近的消息
            self._optimize_chat_history()

            # 保存聊天历史到历史管理器
            self._save_standard_chat_history(model)

        except Exception as e:
            error_msg = f"发送消息失败: {str(e)}"
            # 替换特定错误信息为更友好的提示
            if "QMetaObject.invokeMethod() call failed" in error_msg:
                error_msg = "发送消息失败: Ollama Cloud API 认证失败：无效的 API 密钥"
            # 使用信号安全地更新UI
            self.update_signal.emit("AI", error_msg, model)
        finally:
            # 标记AI回复完成
            self.is_ai_responding = False

            # 处理待发送的消息队列
            if self.pending_messages:
                # 从队列中获取元组(original_message, full_message)
                original_message, full_message = self.pending_messages.pop(0)
                logger.info(
                    f"处理待发送消息，剩余队列长度: {len(self.pending_messages)}"
                )
                
                # 显示用户消息（只显示原始消息，不包含文件解析内容）
                from utils.i18n_manager import i18n
                user_text = i18n.translate('user')
                thinking_text = i18n.translate('thinking')
                self.chat_list_widget.append_message(user_text, original_message)

                # 显示"正在思考..."状态
                self.chat_list_widget.append_message("AI", thinking_text)

                # 标记AI正在回复
                self.is_ai_responding = True

                # 使用线程池发送下一条消息，只传递full_message给模型
                from concurrent.futures import ThreadPoolExecutor

                with ThreadPoolExecutor(max_workers=3) as executor:
                    executor.submit(self._send_chat_message_thread, full_message)

    def append_to_standard_chat_history(self, sender, content, model=""):
        """
        将消息添加到标准聊天历史中（兼容旧方法）

        Args:
            sender: 发送者（AI或用户）
            content: 消息内容
            model: 模型名称
        """
        # 使用新的ChatListWidget组件来添加消息
        self.chat_list_widget.append_message(sender, content, model)

    def _render_markdown_content(self, content):
        """
        将Markdown内容渲染为HTML

        Args:
            content: Markdown格式的内容

        Returns:
            str: HTML格式的内容
        """
        try:
            return markdown.markdown(content)
        except Exception as e:
            logger.error(f"Markdown渲染失败: {str(e)}")
            return content

    def _optimize_chat_history(self):
        """
        优化聊天历史，限制历史记录数量
        """
        if len(self.standard_chat_history_messages) > self.max_standard_chat_history:
            # 保留系统提示词，只移除旧的用户和助手消息
            system_messages = [
                msg
                for msg in self.standard_chat_history_messages
                if msg["role"] == "system"
            ]
            recent_messages = self.standard_chat_history_messages[
                -(self.max_standard_chat_history - len(system_messages)) :
            ]
            self.standard_chat_history_messages = system_messages + recent_messages

    def save_standard_chat_history(self):
        """
        保存标准聊天功能的聊天历史到文件
        """
        try:
            # 生成默认文件名：Nonead-Chat-yyyyMMdd-HHmmss.json
            import datetime

            current_time = datetime.datetime.now()
            default_filename = (
                f"Nonead-Chat-{current_time.strftime('%Y%m%d-%H%M%S')}.json"
            )

            # 打开文件对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                i18n.translate("save_chat_history"),
                default_filename,
                "JSON Files (*.json)",
            )

            if file_path:
                # 收集聊天历史数据
                chat_history = {
                    "type": "standard",
                    "model": self.chat_model_combo.currentText(),
                    "api": self.chat_api_combo.currentText(),
                    "temperature": self.chat_temperature_spin.value(),
                    "messages": self.standard_chat_history_messages.copy(),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                # 保存到JSON文件
                with open(file_path, "w", encoding="utf-8") as f:
                    import json

                    json.dump(chat_history, f, ensure_ascii=False, indent=2)

                QMessageBox.information(
                    self,
                    i18n.translate("success"),
                    i18n.translate("chat_history_saved", path=file_path),
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                i18n.translate("error"),
                i18n.translate("chat_history_save_failed", error=str(e)),
            )

    def load_standard_chat_history(self):
        """
        从文件加载标准聊天功能的聊天历史
        """
        import json
        import traceback

        try:
            logger.info("开始执行load_standard_chat_history方法")
            
            # 打开文件对话框，让用户选择加载文件
            load_chat_history_text = i18n.translate("load_chat_history")
            file_path, _ = QFileDialog.getOpenFileName(
                self, load_chat_history_text, "", "JSON Files (*.json)"
            )

            if not file_path:
                logger.info("用户取消了文件选择")
                return

            logger.info(f"开始加载聊天历史文件: {file_path}")
            
            # 从JSON文件加载聊天历史
            with open(file_path, "r", encoding="utf-8") as f:
                chat_history = json.load(f)

            logger.info(f"成功加载文件，内容类型: {type(chat_history)}")
            
            # 处理两种情况：1. 直接是聊天历史对象；2. 是历史记录列表（从历史管理导出的）
            actual_chat_history = chat_history
            
            # 如果是列表，取第一个元素
            if isinstance(chat_history, list):
                logger.info(f"加载的是列表，长度: {len(chat_history)}")
                if len(chat_history) > 0:
                    actual_chat_history = chat_history[0]
                    logger.info(f"取列表第一个元素，类型: {type(actual_chat_history)}")
                else:
                    logger.info("列表为空，使用空消息列表")
                    self.standard_chat_history_messages = []
                    return
            
            # 直接重置聊天消息历史
            if isinstance(actual_chat_history, dict):
                logger.info(f"加载的是字典，包含键: {list(actual_chat_history.keys())}")
                if "messages" in actual_chat_history and isinstance(
                    actual_chat_history["messages"], list
                ):
                    messages = actual_chat_history["messages"]
                    
                    # 检测是否是导出选中导出的格式（messages只有一条，且内容包含HTML标签）
                    if len(messages) == 1 and isinstance(messages[0], dict):
                        content = messages[0].get("content", "")
                        role = messages[0].get("role", "")
                        
                        # 检查内容是否包含HTML标签（导出选中格式的特征）
                        if content and ("<div" in content or "<p" in content or "<span" in content or "<table" in content or "<br" in content):
                            logger.info("检测到导出选中格式的聊天历史，直接设置HTML内容")
                            # 直接使用HTML内容，不进行消息渲染
                            all_messages_html = content
                            
                            # 构建JavaScript代码设置HTML
                            escaped_html = json.dumps(all_messages_html)
                            js = (
                                "document.getElementById('chat-body').innerHTML = "
                                + escaped_html
                                + ";\n"
                            )
                            js += "window.scrollTo(0, document.body.scrollHeight);\n"
                            js += "// 重新渲染MathJax公式\n"
                            js += "if (window.MathJax) {\n"
                            js += "    MathJax.typesetPromise();\n"
                            js += "}\n"
                            
                            # 执行JavaScript
                            if hasattr(self, 'chat_list_widget') and self.chat_list_widget is not None:
                                if hasattr(self.chat_list_widget, 'chat_history_view') and self.chat_list_widget.chat_history_view is not None:
                                    if hasattr(self.chat_list_widget.chat_history_view, 'page') and self.chat_list_widget.chat_history_view.page() is not None:
                                        self.chat_list_widget.chat_history_view.page().runJavaScript(js)
                                        logger.info("成功执行JavaScript代码（导出选中格式）")
                                    
                                    # 设置空消息列表，避免后续处理
                                    self.standard_chat_history_messages = []
                                    
                                    # 跳过常规消息渲染流程
                                    self._finish_load_chat_history(actual_chat_history, file_path)
                                    return
                    
                    # 常规messages格式
                    self.standard_chat_history_messages = messages
                    logger.info(f"成功加载messages字段，数量: {len(self.standard_chat_history_messages)}")
                else:
                    # 尝试从历史记录中提取聊天内容
                    chat_content = actual_chat_history.get("chat_content", "")
                    if chat_content:
                        logger.info("从chat_content字段提取聊天内容")
                        # 创建一个简单的消息结构
                        self.standard_chat_history_messages = [
                            {
                                "role": "assistant",
                                "content": chat_content
                            }
                        ]
                    else:
                        logger.info("没有找到聊天内容，使用空消息列表")
                        self.standard_chat_history_messages = []
            else:
                logger.warning(f"未知的聊天历史格式: {type(actual_chat_history)}")
                self.standard_chat_history_messages = []

            # 构建完整的消息HTML内容
            all_messages_html = ""
            for msg in self.standard_chat_history_messages:
                try:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        user_text = i18n.translate('user')
                        system_text = i18n.translate('system')
                        sender = (
                            user_text
                            if msg["role"] == "user"
                            else "AI" if msg["role"] == "assistant" else system_text
                        )
                        model = actual_chat_history.get("model", "")
                        # 渲染单条消息HTML
                        message_html = ChatMessageWidget.render_message(
                            sender, msg["content"], model
                        )
                        all_messages_html += message_html
                except Exception as e:
                    logger.error(f"加载消息失败: {str(e)}")
                    continue

            logger.info(f"成功构建消息HTML，长度: {len(all_messages_html)}")
            
            # 使用JavaScript一次性设置所有聊天内容，避免异步冲突
            # 将HTML内容转换为JSON字符串，避免转义问题
            escaped_html = json.dumps(all_messages_html)

            js = (
                "document.getElementById('chat-body').innerHTML = "
                + escaped_html
                + ";\n"
            )
            js += "window.scrollTo(0, document.body.scrollHeight);\n"
            js += "// 重新渲染MathJax公式\n"
            js += "if (window.MathJax) {\n"
            js += "    MathJax.typesetPromise();\n"
            js += "}\n"

            logger.info("准备执行JavaScript代码")
            
            # 检查聊天列表控件是否存在
            if hasattr(self, 'chat_list_widget') and self.chat_list_widget is not None:
                if hasattr(self.chat_list_widget, 'chat_history_view') and self.chat_list_widget.chat_history_view is not None:
                    if hasattr(self.chat_list_widget.chat_history_view, 'page') and self.chat_list_widget.chat_history_view.page() is not None:
                        # 只传递JavaScript代码，不传递第二个参数
                        self.chat_list_widget.chat_history_view.page().runJavaScript(js)
                        logger.info("成功执行JavaScript代码")
                    else:
                        logger.error("chat_history_view.page() 不存在")
                else:
                    logger.error("chat_list_widget.chat_history_view 不存在")
            else:
                logger.error("self.chat_list_widget 不存在")

            # 辅助函数：设置组合框值并防止信号触发
            def set_combobox_value(combobox, value):
                if combobox and value:
                    combobox.blockSignals(True)
                    if isinstance(value, str):
                        combobox.setCurrentText(value)
                    elif isinstance(value, int):
                        combobox.setCurrentIndex(value)
                    combobox.blockSignals(False)

            # 最后更新API和模型设置，使用直接设置，不触发任何信号
            if "api" in actual_chat_history:
                # 直接设置API，不触发信号
                if hasattr(self, 'chat_api_combo') and self.chat_api_combo is not None:
                    index = self.chat_api_combo.findText(actual_chat_history["api"])
                    if index != -1:
                        set_combobox_value(self.chat_api_combo, index)
                        logger.info(f"成功设置API: {actual_chat_history['api']}")
                else:
                    logger.error("self.chat_api_combo 不存在")

            if "model" in actual_chat_history:
                # 直接设置模型，不触发信号
                if hasattr(self, 'chat_model_combo') and self.chat_model_combo is not None:
                    set_combobox_value(self.chat_model_combo, actual_chat_history["model"])
                    logger.info(f"成功设置模型: {actual_chat_history['model']}")
                else:
                    logger.error("self.chat_model_combo 不存在")

            if "temperature" in actual_chat_history:
                if hasattr(self, 'chat_temperature_spin') and self.chat_temperature_spin is not None:
                    self.chat_temperature_spin.setValue(actual_chat_history["temperature"])
                    logger.info(f"成功设置温度: {actual_chat_history['temperature']}")
                else:
                    logger.error("self.chat_temperature_spin 不存在")

            # 显示成功消息
            success_text = i18n.translate("success")
            chat_history_loaded_text = i18n.translate("chat_history_loaded")
            chat_history_loaded_text = chat_history_loaded_text.format(path=file_path)
            QMessageBox.information(
                self,
                success_text,
                chat_history_loaded_text,
            )
            logger.info("聊天历史加载完成")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            error_text = i18n.translate("error")
            json_parse_failed_text = i18n.translate("json_parse_failed")
            QMessageBox.critical(
                self,
                error_text,
                json_parse_failed_text.format(error=str(e)),
            )
        except FileNotFoundError:
            logger.error(f"文件未找到: {file_path}")
            error_text = i18n.translate("error")
            QMessageBox.critical(
                self,
                error_text,
                f"文件未找到: {file_path}",
            )
        except Exception as e:
            logger.error(f"加载聊天历史时发生未知错误: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            error_text = i18n.translate("error")
            QMessageBox.critical(
                self,
                error_text,
                f"加载聊天历史失败: {str(e)}",
            )

    def _finish_load_chat_history(self, actual_chat_history: dict, file_path: str):
        """
        完成聊天历史加载后的处理工作（设置API、模型、温度等）

        Args:
            actual_chat_history: 加载的聊天历史数据
            file_path: 加载的文件路径
        """
        # 辅助函数：设置组合框值并防止信号触发
        def set_combobox_value(combobox, value):
            if combobox and value:
                combobox.blockSignals(True)
                if isinstance(value, str):
                    combobox.setCurrentText(value)
                elif isinstance(value, int):
                    combobox.setCurrentIndex(value)
                combobox.blockSignals(False)

        # 更新API和模型设置，使用直接设置，不触发任何信号
        if "api" in actual_chat_history:
            if hasattr(self, 'chat_api_combo') and self.chat_api_combo is not None:
                index = self.chat_api_combo.findText(actual_chat_history["api"])
                if index != -1:
                    set_combobox_value(self.chat_api_combo, index)
                    logger.info(f"成功设置API: {actual_chat_history['api']}")

        if "model" in actual_chat_history:
            if hasattr(self, 'chat_model_combo') and self.chat_model_combo is not None:
                set_combobox_value(self.chat_model_combo, actual_chat_history["model"])
                logger.info(f"成功设置模型: {actual_chat_history['model']}")

        if "temperature" in actual_chat_history:
            if hasattr(self, 'chat_temperature_spin') and self.chat_temperature_spin is not None:
                self.chat_temperature_spin.setValue(actual_chat_history["temperature"])
                logger.info(f"成功设置温度: {actual_chat_history['temperature']}")

        # 显示成功消息
        success_text = i18n.translate("success")
        chat_history_loaded_text = i18n.translate("chat_history_loaded")
        chat_history_loaded_text = chat_history_loaded_text.format(path=file_path)
        QMessageBox.information(
            self,
            success_text,
            chat_history_loaded_text,
        )
        logger.info("聊天历史加载完成")

    def export_chat_history_to_pdf(self):
        """
        将聊天历史导出为PDF文件
        """
        try:
            # 生成默认文件名：Nonead-Chat-yyyyMMdd-HHmmss.pdf
            import datetime

            current_time = datetime.datetime.now()
            default_filename = (
                f"Nonead-Chat-{current_time.strftime('%Y%m%d-%H%M%S')}.pdf"
            )

            # 打开文件对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                i18n.translate("export_pdf"),
                default_filename,
                "PDF Files (*.pdf)",
            )

            if file_path:
                # 保存原始HTML内容
                original_html = None

                # 获取当前HTML内容
                def get_html_finished(html):
                    nonlocal original_html
                    original_html = html

                    # 在body标签后添加头部信息
                    body_start_idx = html.find("<body")
                    if body_start_idx != -1:
                        # 找到body标签的结束位置
                        body_end_idx = html.find(">", body_start_idx) + 1

                        # 获取当前目录
                        import os
                        import sys

                        if getattr(sys, "frozen", False):
                            # 打包后的可执行文件所在目录
                            current_dir = os.path.dirname(sys.executable)
                        else:
                            # 开发环境下的当前文件所在目录
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            current_dir = os.path.dirname(current_dir)  # 向上一级目录
                            current_dir = os.path.dirname(current_dir)  # 再向上一级目录

                        # 使用本地logo图片，转换为Base64编码嵌入HTML
                        import base64

                        # 使用资源管理器获取logo路径
                        from utils.resource_manager import ResourceManager
                        logo_path = ResourceManager.get_resource_path("noneadLogo.png")

                        # 将图片转换为Base64编码
                        try:
                            with open(logo_path, "rb") as f:
                                logo_data = f.read()
                            logo_base64 = base64.b64encode(logo_data).decode("utf-8")
                            # 构建Data URL
                            logo_url = f"data:image/png;base64,{logo_base64}"
                        except Exception as e:
                            # 如果读取失败，使用空的logo
                            logo_url = ""

                        # 创建头部HTML
                        header_html = f"""
                        <div style="text-align: center; margin-bottom: 20px; padding: 15px; border-bottom: 2px solid #ddd;">
                            <img src="{logo_url}" alt="NONEAD Logo" style="height: 60px; margin-bottom: 10px;">
                        </div>
                        """

                        # 构建新的HTML
                        new_html = (
                            html[:body_end_idx] + header_html + html[body_end_idx:]
                        )

                        # 直接设置web view的HTML内容
                        self.chat_list_widget.chat_history_view.setHtml(new_html)

                        # 使用QTimer延迟导出，确保HTML渲染完成
                        from PyQt5.QtCore import QTimer
                        from PyQt5.QtWidgets import QProgressDialog

                        def export_pdf():
                            # 创建进度对话框
                            progress_dialog = QProgressDialog(
                                "正在生成PDF文件...", "取消", 0, 100, self
                            )
                            progress_dialog.setWindowModality(Qt.WindowModal)
                            progress_dialog.setMinimumDuration(500)  # 500ms后显示进度条
                            progress_dialog.setValue(0)
                            progress_dialog.show()

                            # 定义PDF生成完成后的回调函数
                            def pdf_exported(success):
                                # 确保进度条达到100%
                                progress_dialog.setValue(100)  # 设置进度为100%

                                # 使用QTimer延迟关闭进度条，确保用户看到100%的状态
                                from PyQt5.QtCore import QTimer

                                def close_and_show_result():
                                    # 关闭进度条
                                    progress_dialog.close()

                                    if success:
                                        # 进度窗口关闭后，才显示成功对话框
                                        QMessageBox.information(
                                            self,
                                            i18n.translate("success"),
                                            i18n.translate("pdf_exported", path=file_path),
                                        )
                                    else:
                                        QMessageBox.critical(
                                            self, i18n.translate("error"), i18n.translate("pdf_export_failed")
                                        )

                                    # 恢复原始HTML内容
                                    if original_html:
                                        self.chat_list_widget.chat_history_view.setHtml(
                                            original_html
                                        )

                                # 延迟500ms后关闭进度条并显示结果
                                QTimer.singleShot(500, close_and_show_result)

                            # 更新进度条
                            def update_progress(value):
                                progress_dialog.setValue(value)

                            # 设置初始进度为50%，表示正在生成PDF
                            update_progress(50)

                            # 在PyQt5中，printToPdf方法不支持直接传递回调，而是通过信号通知
                            def handle_pdf_printing_finished(success):
                                # 断开信号连接，避免多次调用
                                self.chat_list_widget.chat_history_view.page().pdfPrintingFinished.disconnect(
                                    handle_pdf_printing_finished
                                )
                                pdf_exported(success)

                            # 连接信号
                            self.chat_list_widget.chat_history_view.page().pdfPrintingFinished.connect(
                                handle_pdf_printing_finished
                            )

                            # 调用PDF导出方法，仅传入文件路径
                            self.chat_list_widget.chat_history_view.page().printToPdf(
                                file_path
                            )

                        # 延迟1000毫秒确保HTML渲染完成
                        QTimer.singleShot(1000, export_pdf)

                # 获取当前HTML内容
                self.chat_list_widget.chat_history_view.page().toHtml(get_html_finished)
        except Exception as e:
            QMessageBox.critical(
                self,
                i18n.translate("error"),
                i18n.translate("pdf_export_failed", error=str(e)),
            )

    def _save_standard_chat_history(self, model, is_clearing=False):
        """
        保存标准聊天历史到历史管理器

        Args:
            model: 模型名称
            is_clearing: 是否是在清空历史时保存
        """
        try:
            # 只有当聊天历史中有至少一条消息时，才保存到历史列表中
            if len(self.standard_chat_history_messages) > 0:
                from utils.chat_history_manager import ChatHistoryManager

                history_manager = ChatHistoryManager()

                # 获取当前时间
                from datetime import datetime

                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 保存当前的just_cleared_history值，避免异步回调时被修改
                current_just_cleared = self.just_cleared_history

                # 获取当前HTML内容
                def get_html_finished(html):
                    # 保存历史记录，传递是否是新聊天的标记
                    # 如果是清空历史时保存，不创建新记录，只更新现有记录
                    history_manager.add_history(
                        func_type="聊天",
                        topic="",
                        model1_name=model,
                        model2_name="",
                        api1=self.chat_api_combo.currentText(),
                        api2="",
                        rounds=len(self.standard_chat_history_messages),
                        chat_content=html,
                        start_time=current_time,
                        end_time=current_time,
                        is_new_chat=current_just_cleared and not is_clearing
                    )
                    
                    # 只有在非清空历史时才重置标记
                    if not is_clearing:
                        self.just_cleared_history = False

                self.chat_list_widget.chat_history_view.page().toHtml(get_html_finished)

                logger.info(f"聊天历史已保存到历史管理器")
            else:
                logger.info(f"聊天历史为空，不保存到历史管理器")
        except Exception as e:
            logger.error(f"保存聊天历史到历史管理器失败: {str(e)}")

    def clear_chat_history(self):
        """
        清除聊天历史
        """
        # 重置AI响应状态
        self.is_ai_responding = False
        self.pending_messages = []
        
        # 清空历史前，先保存当前的聊天历史，结束一条聊天历史记录
        if len(self.standard_chat_history_messages) > 0:
            # 获取当前模型信息
            model = self.chat_model_combo.currentText()
            # 保存当前聊天历史，传递is_clearing=True参数
            self._save_standard_chat_history(model, is_clearing=True)
        
        # 清除聊天历史
        self.chat_list_widget.clear()
        self.standard_chat_history_messages = []
        QMessageBox.information(
            self, i18n.translate("success"), i18n.translate("chat_history_cleared")
        )
        
        # 设置标记，表示刚刚清空了历史，下次输入需要创建新记录
        self.just_cleared_history = True
        logger.info("聊天历史已清空，当前聊天历史记录已结束，下次输入将创建新记录")

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新聊天配置组标题
        self.chat_config_group.setTitle(i18n.translate("chat_config"))

        # 更新聊天控制组标题
        self.chat_control_group.setTitle(i18n.translate("chat_control"))

        # 更新配置区域标签文本
        if hasattr(self, "api_provider_label"):
            self.api_provider_label.setText(i18n.translate("chat_model_provider"))
        if hasattr(self, "model_label"):
            self.model_label.setText(i18n.translate("chat_model"))
        if hasattr(self, "temperature_label"):
            self.temperature_label.setText(i18n.translate("chat_temperature"))
        if hasattr(self, "temperature_range_label"):
            self.temperature_range_label.setText(
                i18n.translate("chat_temperature_range")
            )
        if hasattr(self, "chat_temperature_spin"):
            self.chat_temperature_spin.setToolTip(
                i18n.translate("chat_temperature_tooltip")
            )

        # 更新按钮文本
        self.save_standard_history_button.setText(i18n.translate("chat_save_history"))
        self.load_standard_history_button.setText(i18n.translate("chat_load_history"))
        self.export_chat_pdf_button.setText(i18n.translate("chat_export_pdf"))
        self.clear_history_button.setText(i18n.translate("chat_clear_history"))

        # 更新子组件的UI
        if hasattr(self, "chat_input_widget"):
            self.chat_input_widget.reinit_ui()
        if hasattr(self, "chat_list_widget"):
            self.chat_list_widget.reinit_ui()

    def show_api_key_warning(self, api_name):
        """
        显示API密钥未设置的警告对话框

        Args:
            api_name: API提供商名称
        """
        QMessageBox.warning(
            self,
            i18n.translate("warning"),
            f"{api_name} API密钥未设置，请在设置中配置API密钥后重试。",
            QMessageBox.Ok
        )
