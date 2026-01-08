# -*- coding: utf-8 -*-
"""
关于标签页组件
"""

import sys
import os
from utils.logger_config import get_logger
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QListWidgetItem,
)
from PyQt5.QtGui import QDesktopServices

# 导入国际化管理器
from utils.i18n_manager import i18n

# 获取日志记录器
logger = get_logger(__name__)


class AboutTabWidget(QWidget):
    """
    关于标签页组件，显示软件的关于信息
    """

    def __init__(self):
        """
        初始化关于标签页组件
        """
        super().__init__()
        self.init_ui()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """
        初始化关于标签页UI
        """
        # 创建主布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # 创建Logo标签
        def create_about_logo_label():
            """创建关于页面的Logo标签"""
            try:
                logo_label = QLabel()
                # 使用资源管理器加载并缩放logo
                from utils.resource_manager import ResourceManager
                pixmap = ResourceManager.load_pixmap("noneadLogo.png", 400, 400)
                if pixmap:
                    logo_label.setPixmap(pixmap)
                    logo_label.setAlignment(Qt.AlignCenter)
                else:
                    logger.warning("Logo文件不存在或无法加载")
                return logo_label
            except Exception as e:
                # 如果图片加载失败，创建空标签
                logger.error(f"Logo加载失败: {str(e)}")
                return QLabel()

        # 创建Logo标签
        self.logo_label = create_about_logo_label()
        layout.addWidget(self.logo_label)

        # 软件名称
        self.app_name_label = QLabel("AI Talking")
        self.app_name_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #2196F3;"
        )
        self.app_name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.app_name_label)

        # 软件版本 - 使用绝对导入获取版本号
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from src import __version__
            version_text = f"{i18n.translate('about_version')}{__version__}"
        except Exception as e:
            logger.error(f"获取版本号失败: {str(e)}")
            version_text = f"{i18n.translate('about_version')}1.0.0"
        
        self.version_label = QLabel(version_text)
        self.version_label.setStyleSheet("font-size: 16px; color: #666;")
        self.version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version_label)

        # 公司名称
        self.company_label = QLabel("NONEAD Corporation")
        self.company_label.setStyleSheet("font-size: 18px; color: #333;")
        self.company_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.company_label)

        # 版权信息
        self.copyright_label = QLabel("© 2025 NONEAD Corporation. All rights reserved.")
        self.copyright_label.setStyleSheet("font-size: 14px; color: #888;")
        self.copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.copyright_label)

        # 软件描述
        self.description_label = QLabel(i18n.translate("app_description"))
        self.description_label.setStyleSheet("font-size: 14px; color: #555;")
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setWordWrap(True)
        self.description_label.setMaximumWidth(500)
        layout.addWidget(self.description_label)

        # 分隔线
        self.separator = QWidget()
        self.separator.setFixedHeight(2)
        self.separator.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(self.separator)

        # 联系方式
        self.contact_label = QLabel(i18n.translate("contact_info"))
        self.contact_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #333;"
        )
        self.contact_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.contact_label)

        # 官方网站 - 可点击链接
        self.website_url = "https://www.nonead.com"
        self.website_label = QLabel()
        self.website_label.setText(
            f"{i18n.translate('official_website')}：<a href='{self.website_url}' style='color: #2196F3; text-decoration: underline;'>{self.website_url}</a>"
        )
        self.website_label.setStyleSheet("font-size: 14px; color: #2196F3;")
        self.website_label.setAlignment(Qt.AlignCenter)
        self.website_label.setOpenExternalLinks(True)  # 启用外部链接打开
        layout.addWidget(self.website_label)

        # 邮箱 - 可点击链接
        self.email_address = "service@nonead.com"
        self.email_label = QLabel()
        self.email_label.setText(
            f"{i18n.translate('email')}：<a href='mailto:{self.email_address}' style='color: #555; text-decoration: underline;'>{self.email_address}</a>"
        )
        self.email_label.setStyleSheet("font-size: 14px; color: #555;")
        self.email_label.setAlignment(Qt.AlignCenter)
        self.email_label.setOpenExternalLinks(True)  # 启用外部链接打开
        layout.addWidget(self.email_label)

        # 许可证信息
        self.license_label = QLabel(i18n.translate("license"))
        self.license_label.setStyleSheet("font-size: 14px; color: #888;")
        self.license_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.license_label)

        # 开源地址
        self.open_source_url = "https://gitcode.com/tonyke/AI_Talking"
        self.open_source_label = QLabel()
        self.open_source_label.setText(
            f"{i18n.translate('open_source')}：<a href='{self.open_source_url}' style='color: #2196F3; text-decoration: underline;'>{self.open_source_url}</a>"
        )
        self.open_source_label.setStyleSheet("font-size: 14px; color: #2196F3;")
        self.open_source_label.setAlignment(Qt.AlignCenter)
        self.open_source_label.setOpenExternalLinks(True)  # 启用外部链接打开
        layout.addWidget(self.open_source_label)

        # 下载地址
        self.download_url = "https://gitcode.com/tonyke/AI_Talking/releases/download/v1.1.1/AI_Talking_Setup.exe"
        self.download_label = QLabel()
        self.download_label.setText(
            f"{i18n.translate('download_url')}：<a href='{self.download_url}' style='color: #2196F3; text-decoration: underline;'>{self.download_url}</a>"
        )
        self.download_label.setStyleSheet("font-size: 14px; color: #2196F3;")
        self.download_label.setAlignment(Qt.AlignCenter)
        self.download_label.setOpenExternalLinks(True)  # 启用外部链接打开
        layout.addWidget(self.download_label)

        self.setLayout(layout)

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新界面文本，不重新创建UI
        # 更新软件描述
        if hasattr(self, "description_label"):
            self.description_label.setText(i18n.translate("app_description"))

        # 更新软件版本
        if hasattr(self, "version_label"):
            try:
                import sys
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from src import __version__
                version_text = f"{i18n.translate('about_version')}{__version__}"
            except Exception as e:
                logger.error(f"获取版本号失败: {str(e)}")
                version_text = f"{i18n.translate('about_version')}0.4.1"
            self.version_label.setText(version_text)

        # 更新联系方式标题
        if hasattr(self, "contact_label"):
            self.contact_label.setText(i18n.translate("contact_info"))

        # 更新官方网站链接文本
        if hasattr(self, "website_label") and hasattr(self, "website_url"):
            self.website_label.setText(
                f"{i18n.translate('official_website')}：<a href='{self.website_url}' style='color: #2196F3; text-decoration: underline;'>{self.website_url}</a>"
            )

        # 更新邮箱地址文本
        if hasattr(self, "email_label") and hasattr(self, "email_address"):
            self.email_label.setText(
                f"{i18n.translate('email')}：<a href='mailto:{self.email_address}' style='color: #555; text-decoration: underline;'>{self.email_address}</a>"
            )

        # 更新许可证信息
        if hasattr(self, "license_label"):
            self.license_label.setText(i18n.translate("license"))

        # 更新开源地址文本
        if hasattr(self, "open_source_label") and hasattr(self, "open_source_url"):
            self.open_source_label.setText(
                f"{i18n.translate('open_source')}：<a href='{self.open_source_url}' style='color: #2196F3; text-decoration: underline;'>{self.open_source_url}</a>"
            )

        # 更新下载地址文本
        if hasattr(self, "download_label") and hasattr(self, "download_url"):
            self.download_label.setText(
                f"{i18n.translate('download_url')}：<a href='{self.download_url}' style='color: #2196F3; text-decoration: underline;'>{self.download_url}</a>"
            )
