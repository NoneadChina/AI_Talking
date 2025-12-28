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
    模型管理类，负责获取和缓存Ollama和Ollama Cloud模型列表
    """

    def __init__(self):
        """
        初始化模型管理器
        """
        self.model_cache = {
            "ollama": {},  # Ollama模型缓存，以API URL为键
            "ollama_cloud": {}  # Ollama Cloud模型缓存，独立管理
        }
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

        # 检查Ollama缓存是否存在且未过期
        if api_url in self.model_cache["ollama"]:
            cached_data = self.model_cache["ollama"][api_url]
            if datetime.now() < cached_data["expiry"]:
                logger.info(f"使用缓存的Ollama模型列表，URL: {api_url}")
                return cached_data["models"]

        # 缓存不存在或已过期，从API获取
        logger.info(f"从Ollama API获取模型列表，URL: {api_url}")
        models = self._fetch_ollama_models_from_api(api_url)

        # 只有当模型列表不为空时才更新缓存，否则后续请求会重新尝试从API获取
        if models:
            # 更新Ollama缓存
            self.model_cache["ollama"][api_url] = {
                "models": models,
                "expiry": datetime.now() + self.cache_expiry,
            }
            logger.info(f"已更新Ollama模型列表缓存，URL: {api_url}, 模型数量: {len(models)}")
        else:
            logger.info(f"Ollama模型列表为空，不更新缓存，URL: {api_url}")
            # 返回默认模型列表，确保用户有模型可用
            default_models = ["qwen3:14b", "llama2:7b", "mistral:7b", "gemma:2b", "deepseek-v2:16b"]
            logger.info(f"使用默认Ollama模型列表: {default_models}")
            return default_models

        return models

    def get_ollama_cloud_models(self) -> List[str]:
        """
        获取Ollama Cloud模型列表，优先使用缓存

        Returns:
            List[str]: 模型列表
        """
        # 检查Ollama Cloud缓存是否存在且未过期
        if "default" in self.model_cache["ollama_cloud"]:
            cached_data = self.model_cache["ollama_cloud"]["default"]
            if datetime.now() < cached_data["expiry"]:
                logger.info("使用缓存的Ollama Cloud模型列表")
                return cached_data["models"]

        # 缓存不存在或已过期，获取Ollama Cloud模型
        logger.info("获取Ollama Cloud模型列表")
        models = self._fetch_ollama_cloud_models()

        # 更新Ollama Cloud缓存
        self.model_cache["ollama_cloud"]["default"] = {
            "models": models,
            "expiry": datetime.now() + self.cache_expiry,
        }

        return models

    @staticmethod
    def _fetch_ollama_models_from_api(api_url: str) -> List[str]:
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

    def _fetch_ollama_cloud_models(self) -> List[str]:
        """
        获取Ollama Cloud模型列表

        Returns:
            List[str]: 模型列表
        """
        try:
            # 导入AI服务工厂，获取Ollama Cloud模型列表
            from utils.ai_service import AIServiceFactory
            
            # 创建Ollama Cloud AI服务实例
            ai_service = AIServiceFactory.create_ai_service("ollama_cloud")
            models = ai_service.get_models()
            
            logger.info(f"获取到Ollama Cloud模型: {models}")
            return models
        except Exception as e:
            logger.error(f"获取Ollama Cloud模型失败: {str(e)}")
            # 返回默认模型列表
            return [
                "minimax-m2:cloud", "kimi-k2-thinking:cloud", "gemini-3-pro-preview:latest", 
                "deepseek-v3.1:671b-cloud", "gemma3:27b-cloud", "kimi-k2:1t-cloud", 
                "qwen3-vl:235b-cloud", "gpt-oss:120b-cloud", "qwen3-coder:30b", 
                "qwen3-vl:8b", "qwen3-vl:4b", "qwen3-vl:2b", 
                "deepseek-r1:8b", "llava:7b", "llava:13b", "llava:34b", 
                "phi4:14b", "llama4:16x17b", "gemma3:4b", 
                "qwen3:8b", "llama4:latest", "gemma3:12b", 
                "qwen3:4b", "gemma3:1b", "qwen3:32b", 
                "qwen3:30b", "qwen3:14b", "qwen3:1.7b", 
                "qwen3:0.6b", "qwen3:30b-a3b", "gemma3:27b", 
                "deepseek-r1:70b", "deepseek-r1:1.5b", "deepseek-r1:32b", 
                "phi4:latest", "llama3.3:latest", "deepseek-r1:7b", 
                "deepseek-r1:14b"
            ]

    def clear_cache(self, api_type: str = None, api_url: str = None) -> None:
        """
        清除缓存

        Args:
            api_type: API类型，可选（"ollama" 或 "ollama_cloud"）
            api_url: 要清除的API URL缓存，仅对Ollama有效
        """
        if api_type is None:
            # 清除所有缓存
            self.model_cache = {
                "ollama": {},
                "ollama_cloud": {}
            }
            logger.info("已清除所有模型缓存")
        elif api_type == "ollama":
            if api_url is None:
                # 清除所有Ollama缓存
                self.model_cache["ollama"] = {}
                logger.info("已清除所有Ollama模型缓存")
            elif api_url in self.model_cache["ollama"]:
                # 清除指定URL的Ollama缓存
                del self.model_cache["ollama"][api_url]
                logger.info(f"已清除Ollama API {api_url} 的模型缓存")
        elif api_type == "ollama_cloud":
            # 清除Ollama Cloud缓存
            self.model_cache["ollama_cloud"] = {}
            logger.info("已清除所有Ollama Cloud模型缓存")

    def refresh_models(self, api_type: str = None, api_url: str = None) -> List[str]:
        """
        强制刷新模型列表

        Args:
            api_type: API类型，可选（"ollama" 或 "ollama_cloud"）
            api_url: Ollama API URL，仅对Ollama有效

        Returns:
            List[str]: 更新后的模型列表
        """
        if api_type == "ollama_cloud":
            self.clear_cache("ollama_cloud")
            return self.get_ollama_cloud_models()
        else:
            if api_url:
                self.clear_cache("ollama", api_url)
            else:
                self.clear_cache("ollama")
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
        if api_url in self.model_cache["ollama"]:
            cached_data = self.model_cache["ollama"][api_url]
            if datetime.now() < cached_data["expiry"]:
                logger.info(f"使用缓存的Ollama模型列表，URL: {api_url}")
                callback(cached_data["models"])
                return

        # 创建工作线程
        worker = ModelLoadWorker(api_url, "ollama")

        # 连接信号
        worker.finished.connect(
            lambda models: self._on_async_load_finished("ollama", api_url, models, callback)
        )
        if error_callback:
            worker.error.connect(error_callback)

        # 连接线程完成信号，用于清理引用
        worker.finished.connect(
            lambda: (self.running_workers.remove(worker) if worker in self.running_workers else None)
        )
        worker.error.connect(
            lambda: (self.running_workers.remove(worker) if worker in self.running_workers else None)
        )

        # 添加到运行中线程列表
        self.running_workers.append(worker)

        # 启动线程
        worker.start()

    def async_load_ollama_cloud_models(
        self,
        callback: Callable[[List[str]], None],
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        异步加载Ollama Cloud模型列表

        Args:
            callback: 加载完成后的回调函数
            error_callback: 加载失败后的回调函数，可选
        """
        # 检查缓存是否存在且未过期
        if "default" in self.model_cache["ollama_cloud"]:
            cached_data = self.model_cache["ollama_cloud"]["default"]
            if datetime.now() < cached_data["expiry"]:
                logger.info("使用缓存的Ollama Cloud模型列表")
                callback(cached_data["models"])
                return

        # 创建工作线程
        worker = ModelLoadWorker(None, "ollama_cloud")

        # 连接信号
        worker.finished.connect(
            lambda models: self._on_async_load_finished("ollama_cloud", "default", models, callback)
        )
        if error_callback:
            worker.error.connect(error_callback)

        # 连接线程完成信号，用于清理引用
        worker.finished.connect(
            lambda: (self.running_workers.remove(worker) if worker in self.running_workers else None)
        )
        worker.error.connect(
            lambda: (self.running_workers.remove(worker) if worker in self.running_workers else None)
        )

        # 添加到运行中线程列表
        self.running_workers.append(worker)

        # 启动线程
        worker.start()

    def _on_async_load_finished(
        self, api_type: str, api_url: str, models: List[str], callback: Callable[[List[str]], None]
    ) -> None:
        """
        异步加载完成的处理方法

        Args:
            api_type: API类型（"ollama" 或 "ollama_cloud"）
            api_url: API URL，对于Ollama Cloud使用"default"
            models: 加载的模型列表
            callback: 回调函数
        """
        # 只有当模型列表不为空时才更新缓存，否则后续请求会重新尝试从API获取
        if models:
            # 更新对应类型的缓存
            if api_type == "ollama":
                self.model_cache["ollama"][api_url] = {
                    "models": models,
                    "expiry": datetime.now() + self.cache_expiry,
                }
                logger.info(f"异步加载完成Ollama模型列表，URL: {api_url}, 模型数量: {len(models)}")
            elif api_type == "ollama_cloud":
                self.model_cache["ollama_cloud"][api_url] = {
                    "models": models,
                    "expiry": datetime.now() + self.cache_expiry,
                }
                logger.info(f"异步加载完成Ollama Cloud模型列表，模型数量: {len(models)}")
        else:
            logger.info(f"模型列表为空，不更新缓存，API类型: {api_type}, URL: {api_url}")

        # 调用回调函数
        callback(models)


class ModelLoadWorker(QThread):
    """
    异步加载模型列表的工作线程
    """

    # 定义信号
    finished = pyqtSignal(list)  # 加载完成信号，传递加载的模型列表
    error = pyqtSignal(str)  # 错误信号，传递错误信息

    def __init__(self, api_url: str, api_type: str):
        super().__init__()
        self.api_url = api_url
        self.api_type = api_type

    def run(self):
        """
        线程运行函数，执行异步加载
        """
        try:
            if self.api_type == "ollama":
                logger.info(f"异步从Ollama API获取模型列表，URL: {self.api_url}")
                # 使用ModelManager的静态方法_fetch_ollama_models_from_api，它有更好的错误处理
                models = ModelManager._fetch_ollama_models_from_api(self.api_url)
                
                # 当模型列表为空时，使用默认模型列表
                if not models:
                    default_models = ["qwen3:14b", "llama2:7b", "mistral:7b", "gemma:2b", "deepseek-v2:16b"]
                    logger.info(f"Ollama API返回空列表，使用默认模型列表: {default_models}")
                    models = default_models
                
                logger.info(f"异步获取到Ollama模型: {models}")
                self.finished.emit(models)
            elif self.api_type == "ollama_cloud":
                logger.info("异步获取Ollama Cloud模型列表")
                # 从AI服务获取Ollama Cloud模型列表
                from utils.ai_service import AIServiceFactory
                
                ai_service = AIServiceFactory.create_ai_service("ollama_cloud")
                models = ai_service.get_models()
                
                logger.info(f"异步获取到Ollama Cloud模型: {models}")
                self.finished.emit(models)
        except Exception as e:
            logger.error(f"异步获取模型失败: {str(e)}")
            self.error.emit(f"加载失败: {str(e)}")
            # 当获取失败时，返回默认模型列表，而不是空列表
            if self.api_type == "ollama":
                default_models = ["qwen3:14b", "llama2:7b", "mistral:7b", "gemma:2b", "deepseek-v2:16b"]
                logger.info(f"使用默认Ollama模型列表: {default_models}")
                self.finished.emit(default_models)
            else:
                self.finished.emit([])


# 创建全局模型管理器实例
model_manager = ModelManager()
