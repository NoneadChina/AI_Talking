# -*- coding: utf-8 -*-
"""
资源管理模块
集中处理资源路径的获取和加载，提高代码复用性和可维护性
"""

import os
import sys
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt


class ResourceManager:
    """
    资源管理器类，用于管理应用程序的资源文件
    """

    # 资源缓存，格式：{resource_name: {"pixmap": pixmap_obj, "icon": icon_obj}}
    _resource_cache = {}

    @staticmethod
    def get_resource_path(resource_name):
        """
        获取资源文件的绝对路径，支持不同操作系统

        Args:
            resource_name: 资源文件名，如 "icon.ico" 或 "noneadLogo.png"

        Returns:
            str: 资源文件的绝对路径
        """
        try:
            # 根据运行环境确定资源路径
            if getattr(sys, "frozen", False):
                # 打包后的可执行文件所在目录
                current_dir = os.path.dirname(sys.executable)
                # 对于打包后的应用，resources文件夹可能在不同位置
                # 尝试多种可能的资源目录位置
                possible_resource_dirs = [
                    os.path.join(current_dir, "resources"),
                    current_dir  # 有些打包工具会将资源文件直接放在可执行文件目录下
                ]
            else:
                # 开发环境下的项目根目录 - 需要向上三级目录才能到达项目根目录
                # __file__ 是 src/utils/resource_manager.py
                # 三级父目录才是 AI_Talking 项目根目录
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                possible_resource_dirs = [
                    os.path.join(project_root, "resources")
                ]

            # 尝试所有可能的资源目录，返回第一个存在的资源文件路径
            for resource_dir in possible_resource_dirs:
                resource_path = os.path.join(resource_dir, resource_name)
                if os.path.exists(resource_path):
                    return resource_path
            
            # 如果没有找到资源文件，返回最后尝试的路径
            return os.path.join(possible_resource_dirs[0], resource_name)
        except Exception as e:
            print(f"获取资源路径失败: {str(e)}")
            # 作为最后的 fallback，返回当前目录下的资源文件路径
            return os.path.join(os.getcwd(), "resources", resource_name)

    @staticmethod
    def load_pixmap(resource_name, width=None, height=None):
        """
        加载并返回QPixmap对象，使用缓存机制提高性能

        Args:
            resource_name: 资源文件名
            width: 图片宽度（可选）
            height: 图片高度（可选）

        Returns:
            QPixmap: 加载的QPixmap对象，如果加载失败则返回None
        """
        # 生成缓存键，包含宽度和高度信息
        cache_key = f"{resource_name}_{width}_{height}"

        # 检查缓存中是否已存在
        if cache_key in ResourceManager._resource_cache:
            return ResourceManager._resource_cache[cache_key]

        try:
            resource_path = ResourceManager.get_resource_path(resource_name)

            # 检查资源文件是否存在
            if not os.path.exists(resource_path):
                print(f"图片资源文件不存在: {resource_path}")
                return None

            pixmap = QPixmap(resource_path)

            # 检查是否成功加载
            if pixmap.isNull():
                print(f"图片资源加载失败（空图片）: {resource_path}")
                return None

            # 如果指定了宽度和高度，进行缩放
            if width and height:
                pixmap = pixmap.scaled(
                    width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

            # 将结果存入缓存
            ResourceManager._resource_cache[cache_key] = pixmap

            return pixmap
        except Exception as e:
            print(f"加载图片资源 {resource_name} 失败: {str(e)}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    def load_icon(resource_name):
        """
        加载并返回QIcon对象，使用缓存机制提高性能

        Args:
            resource_name: 资源文件名

        Returns:
            QIcon: 加载的QIcon对象，如果加载失败则返回None
        """
        # 生成缓存键
        cache_key = f"icon_{resource_name}"

        # 检查缓存中是否已存在
        if cache_key in ResourceManager._resource_cache:
            return ResourceManager._resource_cache[cache_key]

        try:
            resource_path = ResourceManager.get_resource_path(resource_name)
            print(f"尝试加载图标: {resource_path}")
            
            # 首先检查文件是否存在
            if not os.path.exists(resource_path):
                print(f"图标文件不存在: {resource_path}")
                return None
            
            # 尝试使用QPixmap加载，再转换为QIcon（更好的SVG支持）
            pixmap = QPixmap(resource_path)
            if pixmap.isNull():
                print(f"QPixmap加载失败: {resource_path}")
                # 如果QPixmap加载失败，尝试直接使用QIcon
                icon = QIcon(resource_path)
                # 检查QIcon是否有效
                if icon.isNull():
                    print(f"QIcon加载失败: {resource_path}")
                    return None
            else:
                # 从有效的QPixmap创建QIcon
                icon = QIcon(pixmap)

            # 将结果存入缓存
            ResourceManager._resource_cache[cache_key] = icon
            print(f"图标加载成功: {resource_path}")
            return icon
        except Exception as e:
            print(f"加载图标资源 {resource_name} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def clear_cache():
        """
        清空资源缓存
        """
        ResourceManager._resource_cache.clear()
        print("资源缓存已清空")

    @staticmethod
    def get_cache_size():
        """
        获取当前缓存大小

        Returns:
            int: 缓存中的资源数量
        """
        return len(ResourceManager._resource_cache)
