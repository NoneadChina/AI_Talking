# -*- coding: utf-8 -*-
"""
AI 服务接口模块
提供统一的 AI 服务调用接口，支持多种 AI 服务提供商
"""

import abc
import requests
import json
from typing import List, Dict, Any, Optional, Generator
from .logger_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class AIServiceInterface(metaclass=abc.ABCMeta):
    """
    AI 服务接口抽象类，定义统一的 AI 服务调用接口
    """

    @abc.abstractmethod
    def get_models(self) -> List[str]:
        """
        获取可用的模型列表

        Returns:
            List[str]: 模型名称列表
        """
        pass

    @abc.abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        生成聊天完成响应

        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 生成文本的随机性
            stream: 是否启用流式响应
            **kwargs: 其他参数

        Returns:
            str or Generator[str, None, None]: 完整响应或流式响应生成器
        """
        pass

    def _process_stream_response(
        self, response: requests.Response, response_format: str = "openai"
    ) -> Generator[str, None, None]:
        """
        处理流式响应，支持多种格式

        Args:
            response: 响应对象
            response_format: 响应格式，可选值：'openai', 'ollama'

        Yields:
            str: 流式响应内容
        """
        full_response: str = ""
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                try:
                    if response_format == "openai":
                        # OpenAI 和 DeepSeek 格式
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            json_data = json.loads(data)
                            if "choices" in json_data and len(json_data["choices"]) > 0:
                                delta = json_data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content: str = delta["content"]
                                    full_response += content
                                    yield full_response
                    elif response_format == "ollama":
                        # Ollama 格式
                        json_data = json.loads(line)
                        if "message" in json_data and "content" in json_data["message"]:
                            content: str = json_data["message"]["content"]
                            full_response += content
                            yield full_response
                        if "done" in json_data and json_data["done"]:
                            break
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析失败: {str(e)}")
        return full_response


class OllamaAIService(AIServiceInterface):
    """
    Ollama AI 服务实现
    """

    def __init__(self, base_url: str):
        """
        初始化 Ollama AI 服务

        Args:
            base_url: Ollama API 基础 URL
        """
        self.base_url: str = base_url.rstrip("/")

    def get_models(self) -> List[str]:
        """
        从 Ollama API 获取模型列表

        Returns:
            List[str]: 模型名称列表
        """
        models: List[str] = []
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            if "models" in data:
                models = [model["name"] for model in data["models"]]
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API 调用失败: {str(e)}")
        return models

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        调用 Ollama API 生成聊天完成响应

        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 生成文本的随机性
            stream: 是否启用流式响应
            **kwargs: 其他参数

        Returns:
            str or Generator[str, None, None]: 完整响应或流式响应生成器
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "options": {"temperature": temperature},
            }

            response = requests.post(
                f"{self.base_url}/api/chat", json=payload, stream=stream, timeout=300
            )
            response.raise_for_status()

            if stream:
                return self._process_stream_response(response, response_format="ollama")
            else:
                data = response.json()
                return data.get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama 聊天完成调用失败: {str(e)}")
            raise


class OpenAIAIService(AIServiceInterface):
    """
    OpenAI AI 服务实现
    """

    def __init__(self, api_key: str):
        """
        初始化 OpenAI AI 服务

        Args:
            api_key: OpenAI API 密钥
        """
        self.api_key: str = api_key
        self.base_url: str = "https://api.openai.com/v1"

    def get_models(self) -> List[str]:
        """
        从 OpenAI API 获取模型列表

        Returns:
            List[str]: 模型名称列表
        """
        models: List[str] = []
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            if "data" in data:
                models = [
                    model["id"]
                    for model in data["data"]
                    if model["id"].startswith("gpt-")
                ]
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API 调用失败: {str(e)}")
        return models

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        调用 OpenAI API 生成聊天完成响应

        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 生成文本的随机性
            stream: 是否启用流式响应
            **kwargs: 其他参数

        Returns:
            str or Generator[str, None, None]: 完整响应或流式响应生成器
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "temperature": temperature,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                stream=stream,
                timeout=300,
            )
            response.raise_for_status()

            if stream:
                return self._process_stream_response(response, response_format="openai")
            else:
                data = response.json()
                return (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI 聊天完成调用失败: {str(e)}")
            raise


class DeepSeekAIService(AIServiceInterface):
    """
    DeepSeek AI 服务实现
    """

    def __init__(self, api_key: str):
        """
        初始化 DeepSeek AI 服务

        Args:
            api_key: DeepSeek API 密钥
        """
        self.api_key: str = api_key
        self.base_url: str = "https://api.deepseek.com/v1"

    def get_models(self) -> List[str]:
        """
        从 DeepSeek API 获取模型列表

        Returns:
            List[str]: 模型名称列表
        """
        models: List[str] = []
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            if "data" in data:
                models = [model["id"] for model in data["data"]]
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API 调用失败: {str(e)}")
        return models

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        调用 DeepSeek API 生成聊天完成响应

        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 生成文本的随机性
            stream: 是否启用流式响应
            **kwargs: 其他参数

        Returns:
            str or Generator[str, None, None]: 完整响应或流式响应生成器
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "temperature": temperature,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                stream=stream,
                timeout=300,
            )
            response.raise_for_status()

            if stream:
                return self._process_stream_response(response, response_format="openai")
            else:
                data = response.json()
                return (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek 聊天完成调用失败: {str(e)}")
            raise


class AIServiceFactory:
    """
    AI 服务工厂类，用于创建不同类型的 AI 服务实例
    """

    @staticmethod
    def create_ai_service(service_type: str, **kwargs) -> AIServiceInterface:
        """
        创建 AI 服务实例

        Args:
            service_type: 服务类型，可选值："ollama", "openai", "deepseek"
            **kwargs: 服务配置参数

        Returns:
            AIServiceInterface: AI 服务实例
        """
        if service_type == "ollama":
            return OllamaAIService(**kwargs)
        elif service_type == "openai":
            return OpenAIAIService(**kwargs)
        elif service_type == "deepseek":
            return DeepSeekAIService(**kwargs)
        else:
            raise ValueError(f"不支持的 AI 服务类型: {service_type}")
