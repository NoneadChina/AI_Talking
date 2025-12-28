# -*- coding: utf-8 -*-
"""
AI Talking 主应用文件
整合所有UI组件，实现完整的应用功能
"""

# 首先将当前文件所在目录添加到Python路径中，确保在导入任何模块之前执行
import os
import sys

# 获取当前文件所在目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 将base_dir添加到Python路径中，确保能找到utils模块
sys.path.insert(0, base_dir)

# 也添加父目录，以防万一
sys.path.insert(0, os.path.dirname(base_dir))

# 加载.env文件
from dotenv import load_dotenv

load_dotenv()

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

# 本地模块导入
from utils.chat_history_manager import ChatHistoryManager
from utils.logger_config import get_logger
from utils.resource_manager import ResourceManager
from utils.update_service import UpdateManager
from utils.i18n_manager import i18n
from utils.config_manager import config_manager  # 导入配置管理器

# UI组件导入
from ui.about_tab import AboutTabWidget
from ui.api_settings import APISettingsWidget
from ui.batch_processing_tab import BatchProcessingTabWidget
from ui.chat_tab import ChatTabWidget
from ui.debate_tab import DebateTabWidget
from ui.discussion_tab import DiscussionTabWidget
from ui.history_management_tab import HistoryManagementTabWidget
from ui.splash_screen import SplashScreen

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

        # 初始化更新管理器
        self.update_manager = UpdateManager(self)

        # 启动时检查更新
        self.update_manager.check_updates_on_startup()

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
        """
        # 创建API设置组件
        self.api_settings_widget = APISettingsWidget()

        # 创建聊天标签页（关键组件，立即初始化）
        self.chat_tab = ChatTabWidget(self.api_settings_widget)

        # 创建讨论标签页（关键组件，立即初始化）
        self.discussion_tab = DiscussionTabWidget(self.api_settings_widget)

        # 创建辩论标签页（关键组件，立即初始化）
        self.debate_tab = DebateTabWidget(self.api_settings_widget)

        # 创建批量处理标签页（关键组件，立即初始化）
        self.batch_processing_tab = BatchProcessingTabWidget(self.api_settings_widget)

        # 初始化非关键标签页为None（延迟初始化）
        self.history_management_tab = None
        self.about_tab = None

    def _add_tabs(self):
        """
        添加标签页到标签页控件
        """
        # 将关键标签页添加到标签页控件
        self.tabs.addTab(self.chat_tab, i18n.translate("tab_chat"))
        self.tabs.addTab(self.discussion_tab, i18n.translate("tab_discussion"))
        self.tabs.addTab(self.debate_tab, i18n.translate("tab_debate"))
        self.tabs.addTab(self.batch_processing_tab, i18n.translate("tab_batch"))
        self.tabs.addTab(self.api_settings_widget, i18n.translate("tab_settings"))

        # 添加占位符标签页，用于历史和关于标签页的延迟初始化
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

        # 批量处理标签页图标
        self.tabs.setTabIcon(3, style.standardIcon(QStyle.SP_DialogApplyButton))

        # 设置标签页图标
        self.tabs.setTabIcon(4, style.standardIcon(QStyle.SP_FileDialogListView))

        # 历史记录标签页图标（占位符）
        self.tabs.setTabIcon(5, style.standardIcon(QStyle.SP_FileDialogBack))

        # 关于标签页图标（占位符）
        self.tabs.setTabIcon(6, style.standardIcon(QStyle.SP_DialogHelpButton))

    def _connect_signals(self):
        """
        连接信号
        """
        # 连接API设置保存信号
        self.api_settings_widget.settings_saved.connect(self.handle_settings_saved)

        # 连接聊天标签页的更新信号
        self.chat_tab.update_signal.connect(self.handle_chat_update)

        # 连接标签页切换信号，用于延迟初始化
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # 连接语言变化信号，用于更新标签页标题
        i18n.language_changed.connect(self.update_tab_titles)

    def handle_settings_saved(self):
        """
        处理API设置保存事件
        当API设置保存后，刷新所有模块的模型列表和系统提示词
        """
        logger.info("API设置已保存，刷新所有模块的模型列表和系统提示词")

        # 刷新聊天模块的模型列表和系统提示词
        self.chat_tab.update_chat_model_list()

        # 刷新讨论模块的模型列表和系统提示词
        self._refresh_discussion_model_list()

        # 刷新辩论模块的模型列表和系统提示词
        self._refresh_debate_model_list()

        # 刷新批量处理模块的模型列表和系统提示词
        self._refresh_batch_model_list()

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

    def _refresh_batch_model_list(self):
        """
        刷新批量处理模块的模型列表
        """
        panel = self.batch_processing_tab.ai_config_panel
        panel.update_ai1_model_list()
        panel.update_ai2_model_list()
        panel.update_ai3_model_list()

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
        处理标签页切换事件，实现非关键组件的延迟初始化

        Args:
            index: 切换到的标签页索引
        """
        logger.info(f"标签页切换到索引 {index}")

        # 历史管理标签页（索引5）
        if index == 5 and self.history_management_tab is None:
            logger.info("正在初始化历史管理标签页...")
            self.history_management_tab = HistoryManagementTabWidget()
            # 替换占位符标签页
            self.tabs.removeTab(index)
            self.tabs.insertTab(
                index, self.history_management_tab, i18n.translate("tab_history")
            )
            # 重新设置图标
            style = QApplication.style()
            self.tabs.setTabIcon(index, style.standardIcon(QStyle.SP_FileDialogBack))
            # 切换到新添加的标签页
            self.tabs.setCurrentIndex(index)
            logger.info("历史管理标签页初始化完成")

        # 关于标签页（索引6）
        elif index == 6 and self.about_tab is None:
            logger.info("正在初始化关于标签页...")
            self.about_tab = AboutTabWidget()
            # 替换占位符标签页
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, self.about_tab, i18n.translate("tab_about"))
            # 重新设置图标
            style = QApplication.style()
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
            3: "tab_batch",
            4: "tab_settings",
            5: "tab_history",
            6: "tab_about",
        }

        for index, translation_key in tab_translations.items():
            if index < self.tabs.count() and (index < 5 or self.tabs.tabText(index)):
                self.tabs.setTabText(index, i18n.translate(translation_key))

        # 调用所有标签页的reinit_ui方法更新界面文本
        tabs_to_update = [
            ("chat_tab", self.chat_tab),
            ("discussion_tab", self.discussion_tab),
            ("debate_tab", self.debate_tab),
            ("batch_processing_tab", self.batch_processing_tab),
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

    def closeEvent(self, event):
        """
        窗口关闭事件处理
        """
        logger.info("应用程序正在关闭")
        # 保存聊天历史
        self.chat_history_manager.save_history()
        event.accept()


def main():
    """
    应用程序入口函数
    """
    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 创建并显示启动画面
    splash = SplashScreen()
    splash.center()
    splash.show()

    # 立即刷新界面，确保启动画面显示
    app.processEvents()

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 更新启动画面消息
    splash.update_progress("正在初始化应用...")
    app.processEvents()

    # 初始化日志
    logger.info("AI Talking 应用程序启动")

    # 创建主窗口（传递启动画面引用）
    window = AI_Talking_MainWindow(splash)

    # 显示主窗口
    window.show()

    # 隐藏启动画面
    splash.finish(window)

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()