# -*- coding: utf-8 -*-
"""
AI Talking 主应用文件
整合所有UI组件，实现完整的应用功能
"""

# 首先将当前文件所在目录添加到Python路径中，确保在导入任何模块之前执行
import os
import sys
from pathlib import Path

# 获取当前文件所在目录
base_dir = Path(__file__).resolve().parent

# 将base_dir添加到Python路径中，确保能找到utils模块
sys.path.insert(0, str(base_dir))

# 也添加父目录，以防万一
sys.path.insert(0, str(base_dir.parent))



# 标准库导入

# 第三方库导入
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QStyle,
)

# 本地模块导入 - 只导入必要的基础模块
from utils.logger_config import get_logger
from utils.i18n_manager import i18n

# 获取日志记录器
logger = get_logger(__name__)


class AI_Talking_MainWindow(QMainWindow):
    """
    AI Talking 主窗口类，整合所有标签页组件
    """

    # 定义信号用于线程安全的UI更新
    update_chat_signal = pyqtSignal(str, str, str)  # 参数: 发送者, 内容, 模型名称
    update_status_signal = pyqtSignal(str)  # 参数: 状态消息

    def __init__(self, splash=None):
        """
        初始化主窗口

        Args:
            splash: 启动画面实例
        """
        super().__init__()

        # 保存启动画面引用
        self.splash = splash

        # 延迟导入ChatHistoryManager
        from utils.chat_history_manager import ChatHistoryManager

        # 初始化聊天历史管理器
        self.chat_history_manager = ChatHistoryManager()

        # 更新启动画面消息
        if self.splash:
            self.splash.update_progress("正在异步加载聊天历史...")
            QApplication.processEvents()

        # 异步加载历史记录
        self.chat_history_manager.async_load_history(
            callback=self._on_history_loaded, error_callback=self._on_history_load_error
        )

        # 更新启动画面消息
        if self.splash:
            self.splash.update_progress("正在初始化界面...")
            QApplication.processEvents()

        # 初始化UI
        self.init_ui()

        # 更新启动画面消息
        if self.splash:
            self.splash.update_progress("正在初始化更新服务...")
            QApplication.processEvents()

        # 延迟导入UpdateManager
        from utils.update_service import UpdateManager

        # 初始化更新管理器
        self.update_manager = UpdateManager(self)

        # 启动时检查更新
        self.update_manager.check_updates_on_startup()
        
        # 启动后自动初始化聊天标签页，而不是等到用户点击
        self._initialize_chat_tab()

    def init_ui(self):
        """
        初始化主窗口UI
        """
        self._setup_window_properties()
        self._create_main_layout()
        self._initialize_tabs()
        self._add_tabs()
        self._set_tab_icons()
        self._connect_signals()

    def _setup_window_properties(self):
        """
        设置窗口属性
        """
        # 延迟导入ResourceManager和config_manager
        from utils.resource_manager import ResourceManager
        from utils.config_manager import config_manager

        # 设置窗口标题
        self.setWindowTitle(i18n.translate("app_title"))

        # 设置窗口图标
        icon = ResourceManager.load_icon("icon.ico")
        if icon:
            self.setWindowIcon(icon)

        # 从配置中读取窗口大小和位置
        x = config_manager.get('app.window.x', 100)
        y = config_manager.get('app.window.y', 100)
        width = config_manager.get('app.window.width', 900)
        height = config_manager.get('app.window.height', 1000)
        self.setGeometry(x, y, width, height)

    def _create_main_layout(self):
        """
        创建主布局
        """
        # 创建中央部件（所有UI元素的容器）
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建标签页控件
        self.tabs = QTabWidget()

        # 将标签页控件添加到主布局
        main_layout.addWidget(self.tabs)

    def _initialize_tabs(self):
        """
        初始化标签页
        优化：将所有标签页改为延迟加载，只在需要时初始化，减少启动时间
        """
        # 初始化所有标签页为None，全部采用延迟加载
        self.api_settings_widget = None
        self.chat_tab = None
        self.discussion_tab = None
        self.debate_tab = None
        self.history_management_tab = None
        self.about_tab = None

    def _add_tabs(self):
        """
        添加标签页到标签页控件
        优化：所有标签页初始化为占位符，只有切换时才加载实际内容
        """
        # 添加所有标签页的占位符，只有在切换时才会加载实际内容
        self.tabs.addTab(QWidget(), i18n.translate("tab_chat"))
        self.tabs.addTab(QWidget(), i18n.translate("tab_discussion"))
        self.tabs.addTab(QWidget(), i18n.translate("tab_debate"))
        self.tabs.addTab(QWidget(), i18n.translate("tab_settings"))
        self.tabs.addTab(QWidget(), i18n.translate("tab_history"))
        self.tabs.addTab(QWidget(), i18n.translate("tab_about"))

    def _set_tab_icons(self):
        """
        为每个标签页设置图标
        """
        style = QApplication.style()

        # 聊天标签页图标
        self.tabs.setTabIcon(0, style.standardIcon(QStyle.SP_MessageBoxInformation))

        # 讨论标签页图标
        self.tabs.setTabIcon(1, style.standardIcon(QStyle.SP_FileDialogDetailedView))

        # 辩论标签页图标
        self.tabs.setTabIcon(2, style.standardIcon(QStyle.SP_MessageBoxQuestion))

        # 设置标签页图标
        self.tabs.setTabIcon(3, style.standardIcon(QStyle.SP_FileDialogListView))

        # 历史记录标签页图标（占位符）
        self.tabs.setTabIcon(4, style.standardIcon(QStyle.SP_FileDialogBack))

        # 关于标签页图标（占位符）
        self.tabs.setTabIcon(5, style.standardIcon(QStyle.SP_DialogHelpButton))

    def _connect_signals(self):
        """
        连接信号
        """
        # 连接标签页切换信号，用于延迟初始化
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # 连接语言变化信号，用于更新标签页标题
        i18n.language_changed.connect(self.update_tab_titles)

    def handle_settings_saved(self):
        """
        处理API设置保存事件
        当API设置保存后，刷新所有模块的模型列表和系统提示词
        优化：检查组件是否已初始化，避免因延迟加载导致的错误
        """
        logger.info("API设置已保存，刷新所有模块的模型列表和系统提示词")

        # 清除所有模型提供商对应的缓存模型列表
        from utils.model_manager import model_manager
        from utils.ai_service import AIServiceFactory
        
        logger.info("清除所有模型缓存")
        # 清除model_manager中的所有缓存
        model_manager.clear_cache()
        
        # 清除所有AI服务类型的缓存
        service_types = ["ollama", "openai", "deepseek", "ollama_cloud"]
        for service_type in service_types:
            try:
                # 为每种服务类型创建实例并清除缓存
                if service_type == "ollama":
                    # Ollama需要base_url参数
                    from ui.api_settings import APISettingsWidget
                    api_settings = APISettingsWidget()
                    base_url = api_settings.get_ollama_base_url()
                    service = AIServiceFactory.create_ai_service(service_type, base_url=base_url)
                else:
                    # 其他服务类型不需要特定参数
                    service = AIServiceFactory.create_ai_service(service_type)
                
                service.clear_cache()
                logger.info(f"已清除{service_type}服务的模型缓存")
            except Exception as e:
                logger.warning(f"清除{service_type}服务缓存时出错: {str(e)}")

        # 刷新聊天模块的模型列表和系统提示词（只有在已初始化的情况下）
        if self.chat_tab is not None:
            self.chat_tab.update_chat_model_list()

        # 刷新讨论模块的模型列表和系统提示词（只有在已初始化的情况下）
        if self.discussion_tab is not None:
            self._refresh_discussion_model_list()

        # 刷新辩论模块的模型列表和系统提示词（只有在已初始化的情况下）
        if self.debate_tab is not None:
            self._refresh_debate_model_list()

        # 刷新窗口标题和标签页标题
        self.update_tab_titles()

    def _refresh_discussion_model_list(self):
        """
        刷新讨论模块的模型列表
        """
        panel = self.discussion_tab.ai_config_panel
        panel.update_model_list(panel.api1_combo, panel.model1_combo)
        panel.update_model_list(panel.api2_combo, panel.model2_combo)
        panel.update_model_list(panel.api3_combo, panel.model3_combo)

    def _refresh_debate_model_list(self):
        """
        刷新辩论模块的模型列表
        """
        panel = self.debate_tab.ai_config_panel
        panel.update_model_list(panel.api1_combo, panel.model1_combo)
        panel.update_model_list(panel.api2_combo, panel.model2_combo)
        panel.update_model_list(panel.api3_combo, panel.model3_combo)

    def handle_chat_update(self, sender, content, model):
        """
        处理聊天更新信号
        更新聊天历史，显示AI回复内容

        Args:
            sender: 发送者（AI或用户）
            content: 消息内容
            model: 模型名称
        """
        logger.info(f"收到聊天更新信号: {sender}, {model}, {content}")
        # 更新聊天历史，移除"正在思考..."消息并添加实际回复
        self.chat_tab.append_to_standard_chat_history(sender, content, model)

    def on_tab_changed(self, index):
        """
        处理标签页切换事件，实现所有组件的延迟初始化

        Args:
            index: 切换到的标签页索引
        """
        logger.info(f"标签页切换到索引 {index}")
        
        # 获取当前标签页的文本，用于更可靠地识别标签页
        current_tab_text = self.tabs.tabText(index)
        
        # 获取应用风格，用于设置图标
        style = QApplication.style()
        
        # 聊天标签页
        if current_tab_text == i18n.translate("tab_chat") and self.chat_tab is None:
            logger.info("正在初始化聊天标签页...")
            # 延迟导入UI组件
            from ui.api_settings import APISettingsWidget
            from ui.chat_tab import ChatTabWidget
            
            # 确保API设置组件已初始化
            if self.api_settings_widget is None:
                self.api_settings_widget = APISettingsWidget()
                # 连接API设置保存信号
                self.api_settings_widget.settings_saved.connect(self.handle_settings_saved)
            self.chat_tab = ChatTabWidget(self.api_settings_widget)
            # 连接聊天标签页的更新信号
            self.chat_tab.update_signal.connect(self.handle_chat_update)
            # 替换占位符标签页
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, self.chat_tab, i18n.translate("tab_chat"))
            # 重新设置图标
            self.tabs.setTabIcon(index, style.standardIcon(QStyle.SP_MessageBoxInformation))
            # 切换到新添加的标签页
            self.tabs.setCurrentIndex(index)
            logger.info("聊天标签页初始化完成")
        
        # 讨论标签页
        elif current_tab_text == i18n.translate("tab_discussion") and self.discussion_tab is None:
            logger.info("正在初始化讨论标签页...")
            # 延迟导入UI组件
            from ui.api_settings import APISettingsWidget
            from ui.discussion_tab import DiscussionTabWidget
            
            # 确保API设置组件已初始化
            if self.api_settings_widget is None:
                self.api_settings_widget = APISettingsWidget()
                # 连接API设置保存信号
                self.api_settings_widget.settings_saved.connect(self.handle_settings_saved)
            self.discussion_tab = DiscussionTabWidget(self.api_settings_widget)
            # 替换占位符标签页
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, self.discussion_tab, i18n.translate("tab_discussion"))
            # 重新设置图标
            self.tabs.setTabIcon(index, style.standardIcon(QStyle.SP_FileDialogDetailedView))
            # 切换到新添加的标签页
            self.tabs.setCurrentIndex(index)
            logger.info("讨论标签页初始化完成")
        
        # 辩论标签页
        elif current_tab_text == i18n.translate("tab_debate") and self.debate_tab is None:
            logger.info("正在初始化辩论标签页...")
            # 延迟导入UI组件
            from ui.api_settings import APISettingsWidget
            from ui.debate_tab import DebateTabWidget
            
            # 确保API设置组件已初始化
            if self.api_settings_widget is None:
                self.api_settings_widget = APISettingsWidget()
                # 连接API设置保存信号
                self.api_settings_widget.settings_saved.connect(self.handle_settings_saved)
            self.debate_tab = DebateTabWidget(self.api_settings_widget)
            # 替换占位符标签页
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, self.debate_tab, i18n.translate("tab_debate"))
            # 重新设置图标
            self.tabs.setTabIcon(index, style.standardIcon(QStyle.SP_MessageBoxQuestion))
            # 切换到新添加的标签页
            self.tabs.setCurrentIndex(index)
            logger.info("辩论标签页初始化完成")
        
        # 设置标签页
        elif current_tab_text == i18n.translate("tab_settings"):
            logger.info("正在初始化设置标签页...")
            # 延迟导入UI组件
            from ui.api_settings import APISettingsWidget
            
            # 确保API设置组件已初始化
            if self.api_settings_widget is None:
                self.api_settings_widget = APISettingsWidget()
                # 连接API设置保存信号
                self.api_settings_widget.settings_saved.connect(self.handle_settings_saved)
            # 检查当前标签页是否为占位符（QWidget实例）
            current_widget = self.tabs.widget(index)
            if isinstance(current_widget, QWidget) and current_widget.layout() is None:
                # 替换占位符标签页
                self.tabs.removeTab(index)
                self.tabs.insertTab(index, self.api_settings_widget, i18n.translate("tab_settings"))
                # 重新设置图标
                self.tabs.setTabIcon(index, style.standardIcon(QStyle.SP_FileDialogListView))
                # 切换到新添加的标签页
                self.tabs.setCurrentIndex(index)
            logger.info("设置标签页初始化完成")
        
        # 历史管理标签页
        elif current_tab_text == i18n.translate("tab_history") and self.history_management_tab is None:
            logger.info("正在初始化历史管理标签页...")
            # 延迟导入UI组件
            from ui.history_management_tab import HistoryManagementTabWidget
            
            self.history_management_tab = HistoryManagementTabWidget()
            # 替换占位符标签页
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, self.history_management_tab, i18n.translate("tab_history"))
            # 重新设置图标
            self.tabs.setTabIcon(index, style.standardIcon(QStyle.SP_FileDialogBack))
            # 切换到新添加的标签页
            self.tabs.setCurrentIndex(index)
            logger.info("历史管理标签页初始化完成")

        # 关于标签页
        elif current_tab_text == i18n.translate("tab_about") and self.about_tab is None:
            logger.info("正在初始化关于标签页...")
            # 延迟导入UI组件
            from ui.about_tab import AboutTabWidget
            
            self.about_tab = AboutTabWidget()
            # 替换占位符标签页
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, self.about_tab, i18n.translate("tab_about"))
            # 重新设置图标
            self.tabs.setTabIcon(index, style.standardIcon(QStyle.SP_DialogHelpButton))
            # 切换到新添加的标签页
            self.tabs.setCurrentIndex(index)
            logger.info("关于标签页初始化完成")

    def update_tab_titles(self):
        """
        更新所有标签页的标题，用于语言切换时
        """
        # 更新窗口标题
        self.setWindowTitle(i18n.translate("app_title"))

        # 更新标签页标题
        tab_translations = {
            0: "tab_chat",
            1: "tab_discussion",
            2: "tab_debate",
            3: "tab_settings",
            4: "tab_history",
            5: "tab_about",
        }

        for index, translation_key in tab_translations.items():
            if index < self.tabs.count() and (index < 5 or self.tabs.tabText(index)):
                self.tabs.setTabText(index, i18n.translate(translation_key))

        # 调用所有标签页的reinit_ui方法更新界面文本
        tabs_to_update = [
            ("chat_tab", self.chat_tab),
            ("discussion_tab", self.discussion_tab),
            ("debate_tab", self.debate_tab),
            ("api_settings_widget", self.api_settings_widget),
            ("history_management_tab", self.history_management_tab),
            ("about_tab", self.about_tab),
        ]

        for tab_attr, tab_instance in tabs_to_update:
            if tab_instance is not None:
                tab_instance.reinit_ui()

    def _on_history_loaded(self, chat_histories):
        """
        聊天历史异步加载完成的回调函数

        Args:
            chat_histories: 加载的聊天历史列表
        """
        logger.info(f"聊天历史异步加载完成: 共 {len(chat_histories)} 条记录")

    def _on_history_load_error(self, error_message):
        """
        聊天历史异步加载错误的回调函数

        Args:
            error_message: 错误信息
        """
        logger.error(f"聊天历史异步加载失败: {error_message}")

    def _initialize_chat_tab(self):
        """
        初始化聊天标签页，在启动时自动调用
        """
        logger.info("启动时自动初始化聊天标签页...")
        
        # 延迟导入UI组件
        from ui.api_settings import APISettingsWidget
        from ui.chat_tab import ChatTabWidget
        
        # 确保API设置组件已初始化
        if self.api_settings_widget is None:
            self.api_settings_widget = APISettingsWidget()
            # 连接API设置保存信号
            self.api_settings_widget.settings_saved.connect(self.handle_settings_saved)
        self.chat_tab = ChatTabWidget(self.api_settings_widget)
        # 连接聊天标签页的更新信号
        self.chat_tab.update_signal.connect(self.handle_chat_update)
        # 替换占位符标签页
        self.tabs.removeTab(0)
        self.tabs.insertTab(0, self.chat_tab, i18n.translate("tab_chat"))
        # 重新设置图标
        style = QApplication.style()
        self.tabs.setTabIcon(0, style.standardIcon(QStyle.SP_MessageBoxInformation))
        # 切换到聊天标签页
        self.tabs.setCurrentIndex(0)
        logger.info("聊天标签页初始化完成")

    def resizeEvent(self, event):
        """
        窗口大小变化事件处理
        保存窗口大小和位置，以便下次启动时恢复
        """
        try:
            # 延迟导入config_manager
            from utils.config_manager import config_manager
            
            # 调用父类的resizeEvent方法
            super().resizeEvent(event)
            
            # 获取当前窗口的大小和位置
            x = self.x()
            y = self.y()
            width = self.width()
            height = self.height()
            
            # 保存到配置文件
            config_manager.set('app.window.x', x)
            config_manager.set('app.window.y', y)
            config_manager.set('app.window.width', width)
            config_manager.set('app.window.height', height)
            
            # 保存配置到文件
            config_manager.save_config()
        except Exception as e:
            logger.error(f"处理窗口大小变化事件时出错: {str(e)}")
    
    def moveEvent(self, event):
        """
        窗口移动事件处理
        保存窗口位置，以便下次启动时恢复
        """
        try:
            # 延迟导入config_manager
            from utils.config_manager import config_manager
            
            # 调用父类的moveEvent方法
            super().moveEvent(event)
            
            # 获取当前窗口的位置
            x = self.x()
            y = self.y()
            
            # 保存到配置文件
            config_manager.set('app.window.x', x)
            config_manager.set('app.window.y', y)
            
            # 保存配置到文件
            config_manager.save_config()
        except Exception as e:
            logger.error(f"处理窗口移动事件时出错: {str(e)}")
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        """
        logger.info("应用程序正在关闭")
        try:
            # 延迟导入config_manager
            from utils.config_manager import config_manager
            
            # 保存聊天历史
            self.chat_history_manager.save_history()
            
            # 保存当前窗口的大小和位置
            x = self.x()
            y = self.y()
            width = self.width()
            height = self.height()
            
            # 保存到配置文件
            config_manager.set('app.window.x', x)
            config_manager.set('app.window.y', y)
            config_manager.set('app.window.width', width)
            config_manager.set('app.window.height', height)
            
            # 保存配置到文件
            config_manager.save()
            
            event.accept()
        except Exception as e:
            logger.error(f"处理窗口关闭事件时出错: {str(e)}")
            # 即使出错也继续关闭窗口
            event.accept()


def main():
    """
    应用程序入口函数，负责初始化和启动整个应用程序
    """
    # 设置Qt属性，解决QtWebEngine初始化问题，确保OpenGL上下文共享
    from PyQt5.QtCore import QCoreApplication, Qt, QTimer
    from PyQt5.QtWidgets import QMessageBox
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    
    # 创建应用程序实例，这是PyQt应用的核心
    app = QApplication(sys.argv)

    # 延迟导入SplashScreen，避免启动时加载过多资源
    from ui.splash_screen import SplashScreen
    
    # 创建并显示启动画面
    splash = SplashScreen()
    splash.center()  # 将启动画面居中显示
    splash.show()

    # 立即刷新界面，确保启动画面能够及时显示
    app.processEvents()

    # 设置应用程序样式为Fusion，提供现代化的外观
    app.setStyle("Fusion")

    # 更新启动画面消息，告知用户当前进度
    splash.update_progress("正在初始化应用...")
    app.processEvents()

    # 记录应用程序启动日志
    logger.info("AI Talking 应用程序启动")
    
    # 检查Ollama API连接状态，这是应用的重要依赖
    logger.info("正在检查Ollama API连接...")
    splash.update_progress("正在检查Ollama API连接...")
    app.processEvents()
    
    # 导入必要的requests模块用于API检查
    import requests
    
    ollama_connected = True  # 默认假设连接成功
    ollama_url = "http://localhost:11434"  # Ollama默认API地址
    
    try:
        logger.info(f"正在测试Ollama API连接: {ollama_url}")
        # 使用2秒超时时间，避免检查过程过长影响启动
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        response.raise_for_status()  # 检查HTTP响应状态码
        logger.info("Ollama API连接成功")
    except requests.Timeout as e:
        logger.error(f"Ollama API连接超时: {str(e)}")
        ollama_connected = False
    except requests.ConnectionError as e:
        logger.error(f"Ollama API连接失败: {str(e)}")
        ollama_connected = False
    except requests.RequestException as e:
        logger.error(f"Ollama API连接错误: {str(e)}")
        ollama_connected = False
    except Exception as e:
        logger.error(f"检查Ollama API连接时发生意外错误: {str(e)}")
        ollama_connected = False
    
    logger.info(f"Ollama连接检查完成，结果: {ollama_connected}")
    
    # 如果Ollama API连接失败，显示提示对话框告知用户
    if not ollama_connected:
        splash.update_progress("Ollama API连接失败，正在显示提示...")
        app.processEvents()
        
        # 创建警告对话框，提示用户Ollama未运行
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(i18n.translate("ollama_not_running_title"))
        msg_box.setText(i18n.translate("ollama_not_running_message"))
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setDefaultButton(QMessageBox.Ok)
        msg_box.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)  # 确保对话框置顶显示
        msg_box.setModal(True)  # 模态对话框，阻止用户操作其他窗口
        
        # 显示对话框并等待用户点击确认
        msg_box.exec_()
        
        logger.info("用户确认了Ollama未运行的提示，继续启动应用")

    # 创建主窗口实例，传递启动画面引用以便后续控制
    window = AI_Talking_MainWindow(splash)

    # 显示主窗口
    window.show()

    # 主窗口显示完成后，隐藏启动画面
    splash.finish(window)

    # 启动应用程序线程池，用于处理异步任务
    from utils.thread_pool import thread_pool
    thread_pool.start()
    
    # 启动内存监控，每30秒检查一次内存使用情况
    from utils.memory_monitor import memory_monitor
    memory_monitor.start(interval=30)
    
    # 运行应用程序主循环，这是应用程序的核心事件循环
    try:
        sys.exit(app.exec_())  # 执行应用程序主循环，直到用户关闭窗口
    finally:
        # 应用程序关闭前的清理工作
        logger.info("应用程序正在关闭，执行清理操作...")
        thread_pool.stop(wait=False)  # 停止线程池，不等待所有任务完成
        memory_monitor.stop()  # 停止内存监控


if __name__ == "__main__":
    main()