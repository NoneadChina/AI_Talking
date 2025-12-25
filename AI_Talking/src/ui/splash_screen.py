# -*- coding: utf-8 -*-
"""
启动画面组件
"""

import os
import sys
from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

# 导入资源管理器
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from utils.resource_manager import ResourceManager

# 导入国际化管理器
from utils.i18n_manager import i18n


class SplashScreen(QSplashScreen):
    """
    启动画面类，显示应用程序加载过程
    """

    # 定义信号用于线程安全的UI更新
    update_progress_signal = pyqtSignal(str)  # 参数: 进度消息

    def __init__(self):
        """
        初始化启动画面
        """
        # 创建透明背景的QPixmap作为SplashScreen的基础
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.transparent)

        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # 设置布局
        self.setFixedSize(400, 300)

        # 创建主部件
        main_widget = QWidget(self)
        main_widget.setGeometry(0, 0, 400, 300)

        # 创建垂直布局
        layout = QVBoxLayout(main_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        # 加载logo
        logo_label = QLabel()
        try:
            pixmap_logo = ResourceManager.load_pixmap("noneadLogo.png", 200, 60)
            if pixmap_logo:
                logo_label.setPixmap(pixmap_logo)
                logo_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(logo_label)
            else:
                # logo加载失败，显示文本logo
                logo_label.setText("AI Talking")
                logo_label.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
                logo_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(logo_label)
        except Exception as e:
            print(f"加载Logo失败: {str(e)}")
            # 异常情况下显示文本logo
            logo_label.setText(i18n.translate("app_name"))
            logo_label.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)

        # 创建应用名称标签
        app_name_label = QLabel(i18n.translate("app_name"))
        app_name_font = QFont("Microsoft YaHei", 24, QFont.Bold)
        app_name_label.setFont(app_name_font)
        app_name_label.setAlignment(Qt.AlignCenter)
        app_name_label.setStyleSheet("color: #333333;")
        layout.addWidget(app_name_label)

        # 创建公司名称标签
        company_label = QLabel(i18n.translate("company_name"))
        company_font = QFont("Microsoft YaHei", 12)
        company_label.setFont(company_font)
        company_label.setAlignment(Qt.AlignCenter)
        company_label.setStyleSheet("color: #666666;")
        layout.addWidget(company_label)

        # 创建进度消息标签
        self.progress_label = QLabel(i18n.translate("loading_app"))
        progress_font = QFont("Microsoft YaHei", 10)
        self.progress_label.setFont(progress_font)
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #999999;")
        layout.addWidget(self.progress_label)

        # 创建版权信息标签
        copyright_label = QLabel(i18n.translate("copyright"))
        copyright_font = QFont("Microsoft YaHei", 8)
        copyright_label.setFont(copyright_font)
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(copyright_label)

        # 连接信号
        self.update_progress_signal.connect(self.update_progress)

    def update_progress(self, message):
        """
        更新进度消息

        Args:
            message: 进度消息内容
        """
        self.progress_label.setText(message)

    def center(self):
        """
        将启动画面居中显示
        """
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
