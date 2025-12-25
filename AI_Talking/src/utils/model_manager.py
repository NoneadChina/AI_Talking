# -*- coding: utf-8 -*-
"""
模型管理工具类，用于缓存和共享Ollama模型列表
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class ModelManager:
    """
    模型管理类，负责获取和缓存Ollama模型列表
    """

    def __init__(self):
        """
        初始化模型管理器
        """
        self.model_cache = {}
        self.cache_expiry = timedelta(minutes=30)
        self.ollama_api_url = "http://ai.corp.nonead.com:11434"
        self.running_workers = []  # 维护运行中线程的引用

    def get_ollama_models(self, api_url: str = None) -> List[str]:
        """
        获取Ollama模型列表，优先使用缓存

        Args:
            api_url: Ollama API URL，可选

        Returns:
            List[str]: 模型列表
        """
        if api_url is None:
            api_url = self.ollama_api_url

        # 检查缓存是否存在且未过期
        if api_url in self.model_cache:
            cached_data = self.model_cache[api_url]
            if datetime.now() < cached_data["expiry"]:
                logger.info(f"使用缓存的Ollama模型列表，URL: {api_url}")
                return cached_data["models"]

        # 缓存不存在或已过期，从API获取
        logger.info(f"从Ollama API获取模型列表，URL: {api_url}")
        models = self._fetch_ollama_models_from_api(api_url)

        # 更新缓存
        self.model_cache[api_url] = {
            "models": models,
            "expiry": datetime.now() + self.cache_expiry,
        }

        return models

    def _fetch_ollama_models_from_api(self, api_url: str) -> List[str]:
        """
        从Ollama API获取模型列表

        Args:
            api_url: Ollama API URL

        Returns:
            List[str]: 模型列表
        """
        try:
            response = requests.get(f"{api_url}/api/tags", timeout=10)
            response.raise_for_status()

            data = response.json()
            models = [model["name"] for model in data["models"]]

            logger.info(f"获取到Ollama模型: {models}")
            return models
        except requests.RequestException as e:
            logger.error(f"从Ollama API获取模型失败: {str(e)}")
            return []

    def clear_cache(self, api_url: str = None) -> None:
        """
        清除缓存

        Args:
            api_url: 要清除的API URL缓存，None表示清除所有缓存
        """
        if api_url is None:
            self.model_cache.clear()
            logger.info("已清除所有模型缓存")
        elif api_url in self.model_cache:
            del self.model_cache[api_url]
            logger.info(f"已清除API {api_url} 的模型缓存")

    def refresh_models(self, api_url: str = None) -> List[str]:
        """
        强制刷新模型列表

        Args:
            api_url: Ollama API URL，可选

        Returns:
            List[str]: 更新后的模型列表
        """
        if api_url:
            self.clear_cache(api_url)
        else:
            self.clear_cache()

        return self.get_ollama_models(api_url)

    def async_load_ollama_models(
        self,
        api_url: str,
        callback: Callable[[List[str]], None],
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        异步加载Ollama模型列表

        Args:
            api_url: Ollama API URL
            callback: 加载完成后的回调函数
            error_callback: 加载失败后的回调函数，可选
        """
        # 检查缓存是否存在且未过期
        if api_url in self.model_cache:
            cached_data = self.model_cache[api_url]
            if datetime.now() < cached_data["expiry"]:
                logger.info(f"使用缓存的Ollama模型列表，URL: {api_url}")
                callback(cached_data["models"])
                return

        # 创建工作线程
        worker = ModelLoadWorker(api_url)

        # 连接信号
        worker.finished.connect(
            lambda models: self._on_async_load_finished(api_url, models, callback)
        )
        if error_callback:
            worker.error.connect(error_callback)

        # 连接线程完成信号，用于清理引用
        worker.finished.connect(
            lambda: (
                self.running_workers.remove(worker)
                if worker in self.running_workers
                else None
            )
        )
        worker.error.connect(
            lambda: (
                self.running_workers.remove(worker)
                if worker in self.running_workers
                else None
            )
        )

        # 添加到运行中线程列表
        self.running_workers.append(worker)

        # 启动线程
        worker.start()

    def _on_async_load_finished(
        self, api_url: str, models: List[str], callback: Callable[[List[str]], None]
    ) -> None:
        """
        异步加载完成的处理方法

        Args:
            api_url: Ollama API URL
            models: 加载的模型列表
            callback: 回调函数
        """
        # 更新缓存
        self.model_cache[api_url] = {
            "models": models,
            "expiry": datetime.now() + self.cache_expiry,
        }

        logger.info(
            f"异步加载完成Ollama模型列表，URL: {api_url}, 模型数量: {len(models)}"
        )

        # 调用回调函数
        callback(models)


class ModelLoadWorker(QThread):
    """
    异步加载模型列表的工作线程
    """

    # 定义信号
    finished = pyqtSignal(list)  # 加载完成信号，传递加载的模型列表
    error = pyqtSignal(str)  # 错误信号，传递错误信息

    def __init__(self, api_url: str):
        super().__init__()
        self.api_url = api_url

    def run(self):
        """
        线程运行函数，执行异步加载
        """
        try:
            logger.info(f"异步从Ollama API获取模型列表，URL: {self.api_url}")
            response = requests.get(f"{self.api_url}/api/tags", timeout=10)
            response.raise_for_status()

            data = response.json()
            models = [model["name"] for model in data["models"]]

            logger.info(f"异步获取到Ollama模型: {models}")
            self.finished.emit(models)
        except requests.RequestException as e:
            logger.error(f"异步从Ollama API获取模型失败: {str(e)}")
            self.error.emit(f"加载失败: {str(e)}")
            self.finished.emit([])


# 创建全局模型管理器实例
model_manager = ModelManager()
