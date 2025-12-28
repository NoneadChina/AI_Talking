# -*- coding: utf-8 -*-
"""
自动更新服务模块
负责应用的版本检查、下载和安装
"""

import os
import sys
import json
import shutil
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from threading import Thread
from typing import Dict, Optional
import requests
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QLabel, QPushButton, QHBoxLayout, QWidget
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, QTimer

# 获取日志记录器
logger = logging.getLogger(__name__)


class UpdateService(QObject):
    """
    自动更新服务类
    负责检查更新、下载更新和安装更新
    """

    # 定义信号
    update_available = pyqtSignal(dict)  # 发现新版本信号，传递版本信息
    update_downloaded = pyqtSignal(str)  # 更新下载完成信号，传递安装包路径
    update_progress = pyqtSignal(int)  # 更新下载进度信号，传递百分比
    update_error = pyqtSignal(str)  # 更新错误信号，传递错误信息

    def __init__(self):
        """
        初始化更新服务
        """
        super().__init__()

        # 配置信息
        self.update_server_url = (
            "https://www.nonead.com/download/app/AI_Talking"  # 更新服务器URL
        )
        self.current_version = self.get_current_version()  # 当前版本
        self.platform = self.get_platform()  # 平台信息
        self.update_info = None  # 更新信息

        # 初始化版本历史记录
        self.init_version_history()

    def get_current_version(self) -> str:
        """
        获取当前应用版本
        """
        try:
            from src import __version__

            return __version__
        except ImportError:
            logger.error("无法获取当前版本号")
            return "0.1.6"

    def get_platform(self) -> str:
        """
        获取当前平台
        """
        if sys.platform.startswith("win"):
            return "win32"
        elif sys.platform.startswith("darwin"):
            return "darwin"
        elif sys.platform.startswith("linux"):
            return "linux"
        else:
            return "unknown"

    def init_version_history(self) -> None:
        """
        初始化版本历史记录
        """
        try:
            # 创建日志目录
            log_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs"
            )
            os.makedirs(log_dir, exist_ok=True)

            # 版本日志文件路径
            self.version_log_path = os.path.join(log_dir, "version.log")

            # 记录当前版本启动信息
            with open(self.version_log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"{datetime.now().isoformat()}|{self.current_version}|{self.platform}|{sys.platform}|{os.name}|{getattr(sys, 'frozen', False)}\n"
                )
        except Exception as e:
            logger.error(f"初始化版本历史记录失败: {e}")

    def check_for_updates(self) -> None:
        """
        检查是否有新版本
        在独立线程中执行，避免阻塞主线程
        """

        def _check_update():
            try:
                logger.info(f"检查更新，当前版本: {self.current_version}")

                # 构建更新检查URL
                update_url = f"{self.update_server_url}/latest.json"

                # 发送请求获取最新版本信息
                response = requests.get(update_url, timeout=10)
                response.raise_for_status()

                # 解析更新信息
                latest_version_info = response.json()
                logger.info(f"获取到最新版本信息: {latest_version_info}")

                # 比较版本号
                if self.is_newer_version(
                    latest_version_info["version"], self.current_version
                ):
                    logger.info(f"发现新版本: {latest_version_info['version']}")
                    self.update_info = latest_version_info
                    self.update_available.emit(latest_version_info)
                else:
                    logger.info("当前已是最新版本")
            except Exception as e:
                logger.error(f"检查更新失败: {e}")
                self.update_error.emit(str(e))

        # 在独立线程中执行检查
        thread = Thread(target=_check_update, daemon=True)
        thread.start()

    def is_newer_version(self, new_version: str, current_version: str) -> bool:
        """
        比较版本号，判断是否为新版本

        Args:
            new_version: 新版本号
            current_version: 当前版本号

        Returns:
            bool: 是否为新版本
        """
        try:
            # 将版本号拆分为数字列表
            new_parts = list(map(int, new_version.split(".")))
            current_parts = list(map(int, current_version.split(".")))

            # 比较版本号
            for new, current in zip(new_parts, current_parts):
                if new > current:
                    return True
                elif new < current:
                    return False

            # 如果前面的版本号相同，检查长度
            return len(new_parts) > len(current_parts)
        except Exception as e:
            logger.error(f"版本号比较失败: {e}")
            return False

    def download_update(self, version_info: Dict) -> None:
        """
        下载更新包

        Args:
            version_info: 版本信息字典
        """

        def _download():
            try:
                logger.info(f"开始下载更新包: {version_info['version']}")

                # 获取适合当前平台的更新包URL
                if self.platform == "win32":
                    update_file_url = version_info.get("win32", {}).get("url")
                elif self.platform == "darwin":
                    update_file_url = version_info.get("darwin", {}).get("url")
                elif self.platform == "linux":
                    update_file_url = version_info.get("linux", {}).get("url")
                else:
                    raise Exception(f"不支持的平台: {self.platform}")

                if not update_file_url:
                    raise Exception(f"没有找到适合当前平台的更新包: {self.platform}")

                # 构建完整的下载URL
                if not update_file_url.startswith("http"):
                    update_file_url = f"{self.update_server_url}/{update_file_url}"

                # 创建临时文件保存更新包
                temp_dir = tempfile.gettempdir()
                update_file_name = os.path.basename(update_file_url)
                update_file_path = os.path.join(temp_dir, update_file_name)

                # 下载更新包
                response = requests.get(update_file_url, stream=True, timeout=30)
                response.raise_for_status()

                # 获取文件大小
                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0

                # 写入文件
                with open(update_file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # 计算进度百分比
                            if total_size > 0:
                                progress = int((downloaded_size / total_size) * 100)
                                self.update_progress.emit(progress)

                logger.info(f"更新包下载完成: {update_file_path}")
                self.update_downloaded.emit(update_file_path)
            except Exception as e:
                logger.error(f"下载更新失败: {e}")
                self.update_error.emit(str(e))

        # 在独立线程中执行下载
        thread = Thread(target=_download, daemon=True)
        thread.start()

    def install_update(self, update_file_path: str) -> None:
        """
        安装更新
        在应用关闭后执行

        Args:
            update_file_path: 更新包路径
        """
        try:
            logger.info(f"准备安装更新: {update_file_path}")

            # 对于Windows平台，我们可以使用内置的msiexec或自定义安装脚本
            if self.platform == "win32":
                # 这里假设更新包是一个可执行文件
                if update_file_path.endswith(".exe"):
                    logger.info(f"启动安装程序: {update_file_path}")
                    # 使用os.startfile启动安装程序
                    os.startfile(update_file_path)
                else:
                    logger.error(f"不支持的更新包格式: {update_file_path}")
            else:
                logger.error(f"不支持的平台安装: {self.platform}")
        except Exception as e:
            logger.error(f"安装更新失败: {e}")


class UpdateNotificationWidget(QWidget):
    """
    更新通知组件
    在窗口标题栏右侧显示更新提示
    """

    update_clicked = pyqtSignal()  # 更新按钮点击信号

    def __init__(self, parent=None):
        """
        初始化更新通知组件

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2196F3;
                border-radius: 4px;
            }
            QLabel {
                color: white;
                font-size: 12px;
                padding: 0 5px;
            }
            QPushButton {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """
        )

        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        # 创建通知标签
        self.notify_label = QLabel("发现新版本")
        layout.addWidget(self.notify_label)

        # 创建更新按钮
        self.update_button = QPushButton("更新")
        self.update_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_button.clicked.connect(self.update_clicked.emit)
        layout.addWidget(self.update_button)

        # 初始隐藏
        self.hide()


class UpdateManager(QObject):
    """
    更新管理器
    协调更新服务和UI组件
    """

    def __init__(self, main_window):
        """
        初始化更新管理器

        Args:
            main_window: 主窗口实例
        """
        super().__init__()

        self.main_window = main_window
        self.update_service = UpdateService()

        # 创建更新通知组件
        self.update_notification = UpdateNotificationWidget()

        # 连接信号
        self.update_service.update_available.connect(self.on_update_available)
        self.update_service.update_downloaded.connect(self.on_update_downloaded)
        self.update_service.update_error.connect(self.on_update_error)
        self.update_notification.update_clicked.connect(self.on_update_clicked)

        # 应用关闭时检查是否需要安装更新
        self.main_window.closeEvent = self.on_close_event

        # 待安装的更新包路径
        self.pending_update_path = None

    def check_updates_on_startup(self):
        """
        应用启动时检查更新
        """
        # 延迟检查，避免影响应用启动速度
        QTimer.singleShot(5000, self.update_service.check_for_updates)

    def on_update_available(self, version_info):
        """
        发现新版本时的处理

        Args:
            version_info: 版本信息字典
        """
        logger.info(f"显示更新通知: {version_info['version']}")

        # 在标题栏右侧显示更新通知
        # 这里需要根据主窗口的布局进行调整，可能需要修改主窗口的UI结构
        # 为了简化实现，我们这里直接显示一个消息框
        from utils.i18n_manager import i18n
        reply = QMessageBox.question(
            self.main_window,
            i18n.translate("update_available"),
            i18n.translate("update_available_message", version=version_info['version'], release_notes=version_info.get('releaseNotes', '无')),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply == QMessageBox.Yes:
            # 开始下载更新
            self.update_service.download_update(version_info)

    def on_update_downloaded(self, update_file_path):
        """
        更新下载完成时的处理

        Args:
            update_file_path: 更新包路径
        """
        logger.info(f"更新下载完成: {update_file_path}")

        # 保存更新包路径，等待应用关闭后安装
        self.pending_update_path = update_file_path

        # 显示提示
        from utils.i18n_manager import i18n
        QMessageBox.information(
            self.main_window,
            i18n.translate("update_downloaded"),
            i18n.translate("update_downloaded_message"),
            QMessageBox.Ok,
        )

    def on_update_error(self, error_message):
        """
        更新错误时的处理

        Args:
            error_message: 错误信息
        """
        logger.error(f"更新错误: {error_message}")

        # 可以选择显示错误信息，或者静默处理
        # QMessageBox.warning(
        #     self.main_window,
        #     "更新错误",
        #     f"更新过程中发生错误：{error_message}",
        #     QMessageBox.Ok
        # )

    def on_update_clicked(self):
        """
        更新按钮点击时的处理
        """
        if self.update_service.update_info:
            self.update_service.download_update(self.update_service.update_info)

    def on_close_event(self, event):
        """
        应用关闭时的处理
        检查是否有待安装的更新包，如果有则安装
        """
        # 调用原始的closeEvent
        # self.main_window.closeEvent(event)

        if self.pending_update_path and os.path.exists(self.pending_update_path):
            logger.info(f"应用关闭，开始安装更新: {self.pending_update_path}")

            # 启动安装程序
            self.update_service.install_update(self.pending_update_path)

        # 接受关闭事件
        event.accept()
