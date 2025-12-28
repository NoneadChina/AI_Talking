# -*- coding: utf-8 -*-
"""
AI 服务接口模块
提供统一的 AI 服务调用接口，支持多种 AI 服务提供商
"""

import abc
import requests
import json
import time
from typing import List, Dict, Any, Optional, Generator, Callable, Tuple
from collections import defaultdict
from .logger_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retry_exceptions: tuple = (Exception,),
) -> Callable:
    """
    重试装饰器，带有指数退避机制

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        retry_exceptions: 重试的异常类型，默认为所有Exception

    Returns:
        Callable: 装饰后的函数
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    if retries == max_retries:
                        logger.error(
                            f"达到最大重试次数 {max_retries}，请求失败: {str(e)}"
                        )
                        raise

                    # 指数退避算法
                    delay = min(
                        base_delay * (2**retries) + (time.time() % 1), max_delay
                    )
                    logger.warning(
                        f"请求失败，{delay:.2f}秒后重试 ({retries+1}/{max_retries}): {str(e)}"
                    )
                    time.sleep(delay)
                    retries += 1

        return wrapper

    return decorator


class RateLimiter:
    """
    请求速率限制器，使用令牌桶算法实现
    """
    
    def __init__(self, max_calls: int, period: float):
        """
        初始化速率限制器
        
        Args:
            max_calls: 时间段内允许的最大调用次数
            period: 时间段长度（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = defaultdict(list)  # 存储每个服务类型的调用时间
    
    def __call__(self, func: Callable) -> Callable:
        """
        装饰器入口
        
        Args:
            func: 要装饰的函数
            
        Returns:
            Callable: 装饰后的函数
        """
        def wrapper(*args, **kwargs):
            # 确定服务类型
            service_type = "default"
            # 检查是否是类方法调用（有self参数）
            if args and hasattr(args[0], "__class__"):
                service_type = args[0].__class__.__name__.lower()
            
            # 获取当前时间
            now = time.time()
            
            # 清除过期的调用记录
            self.calls[service_type] = [
                call_time for call_time in self.calls[service_type] 
                if now - call_time < self.period
            ]
            
            # 检查是否超过速率限制
            if len(self.calls[service_type]) >= self.max_calls:
                # 计算需要等待的时间
                wait_time = self.period - (now - self.calls[service_type][0])
                if wait_time > 0:
                    logger.warning(
                        f"请求速率限制触发，服务类型: {service_type}, "
                        f"等待 {wait_time:.2f} 秒后重试"
                    )
                    time.sleep(wait_time)
            
            # 记录本次调用时间
            self.calls[service_type].append(time.time())
            
            # 执行原始函数
            return func(*args, **kwargs)
        
        return wrapper


# 创建全局速率限制器实例
# 不同服务类型的速率限制配置
# 可根据实际API提供商的限制进行调整
rate_limiter = {
    "openai": RateLimiter(max_calls=30, period=60),  # OpenAI: 30次/分钟
    "deepseek": RateLimiter(max_calls=30, period=60),  # DeepSeek: 30次/分钟
    "ollama": RateLimiter(max_calls=60, period=60),  # Ollama: 60次/分钟
    "ollamacloud": RateLimiter(max_calls=30, period=60),  # Ollama Cloud: 30次/分钟
    "default": RateLimiter(max_calls=20, period=60),  # 默认: 20次/分钟
}


class AIServiceInterface(metaclass=abc.ABCMeta):
    """
    AI 服务接口抽象类，定义统一的 AI 服务调用接口
    """

    def __init__(self):
        """
        初始化 AI 服务接口，设置模型列表缓存
        """
        self._model_cache = None
        self._cache_timestamp = 0
        self._cache_duration = 1800  # 30分钟

    def get_models(self) -> List[str]:
        """
        获取可用的模型列表，使用缓存机制

        Returns:
            List[str]: 模型名称列表
        """
        import time

        # 检查缓存是否有效
        if (
            self._model_cache
            and (time.time() - self._cache_timestamp) < self._cache_duration
        ):
            logger.info(f"使用缓存的模型列表，缓存时间: {self._cache_timestamp}")
            return self._model_cache

        # 重新获取模型列表
        logger.info("缓存已过期或不存在，重新获取模型列表")
        models = self._fetch_models()

        # 更新缓存
        self._model_cache = models
        self._cache_timestamp = time.time()
        logger.info(f"已更新模型列表缓存，共 {len(models)} 个模型")
        return models

    @abc.abstractmethod
    def _fetch_models(self) -> List[str]:
        """
        实际调用API获取模型列表的抽象方法

        Returns:
            List[str]: 模型名称列表
        """
        pass

    def clear_cache(self):
        """
        清除模型列表缓存
        """
        logger.info("清除模型列表缓存")
        self._model_cache = None
        self._cache_timestamp = 0

    def refresh_cache(self):
        """
        刷新模型列表缓存

        Returns:
            List[str]: 更新后的模型列表
        """
        logger.info("刷新模型列表缓存")
        self.clear_cache()
        return self.get_models()

    @abc.abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        yield_full_response: bool = True,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        生成聊天完成响应

        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 生成文本的随机性
            stream: 是否启用流式响应
            yield_full_response: 是否返回完整响应，False 时仅返回新增内容
            **kwargs: 其他参数

        Returns:
            str or Generator[str, None, None]: 完整响应或流式响应生成器
        """
        pass

    def _process_stream_response(
        self,
        response: requests.Response,
        response_format: str = "openai",
        yield_full_response: bool = True,
    ) -> Generator[str, None, None]:
        """
        处理流式响应，支持多种格式

        该方法处理来自不同AI服务提供商的流式响应，将原始响应转换为用户友好的文本流

        Args:
            response: 响应对象，包含服务器返回的原始流数据
            response_format: 响应格式，可选值：'openai', 'ollama'
                - 'openai': 适用于OpenAI、DeepSeek等遵循OpenAI流式响应格式的服务
                - 'ollama': 适用于Ollama服务的流式响应格式
            yield_full_response: 是否返回完整响应
                - True: 每次返回截至当前的完整响应文本
                - False: 仅返回当前增量文本

        Yields:
            str: 根据yield_full_response参数返回完整响应或新增内容

        Returns:
            str: 最终的完整响应文本
        """
        full_response: str = ""  # 存储完整的响应文本

        # 遍历响应流中的每一行数据
        for line in response.iter_lines():
            if line:  # 跳过空行
                line = line.decode("utf-8")  # 将字节数据转换为UTF-8字符串

                try:
                    if response_format == "openai":
                        # 处理OpenAI/DeepSeek格式的流式响应
                        if line.startswith("data: "):  # 检查是否为数据行
                            data = line[6:]  # 提取数据部分

                            if data == "[DONE]":  # 检查是否为结束标记
                                break  # 结束流式处理

                            # 解析JSON数据
                            json_data = json.loads(data)

                            # 检查是否包含choices字段且不为空
                            if "choices" in json_data and len(json_data["choices"]) > 0:
                                # 获取当前增量内容
                                delta = json_data["choices"][0].get("delta", {})

                                # 检查是否包含content字段且不为None
                                if "content" in delta and delta["content"] is not None:
                                    content: str = delta["content"]
                                    full_response += content  # 更新完整响应

                                    # 根据参数返回完整响应或仅增量内容
                                    if yield_full_response:
                                        yield full_response
                                    else:
                                        yield content

                    elif response_format == "ollama":
                        # 处理Ollama格式的流式响应
                        # Ollama格式的每一行都是完整的JSON对象
                        json_data = json.loads(line)

                        # 检查是否包含message.content字段且不为None
                        if (
                            "message" in json_data
                            and "content" in json_data["message"]
                            and json_data["message"]["content"] is not None
                        ):

                            content: str = json_data["message"]["content"]
                            full_response += content  # 更新完整响应

                            # 根据参数返回完整响应或仅增量内容
                            if yield_full_response:
                                yield full_response
                            else:
                                yield content

                        # 检查是否为结束标记
                        if "done" in json_data and json_data["done"]:
                            break  # 结束流式处理

                except json.JSONDecodeError as e:
                    # 处理JSON解析错误，记录日志并继续处理后续数据
                    logger.error(f"JSON 解析失败: {str(e)}")

        # 返回最终的完整响应文本
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
        super().__init__()
        self.base_url: str = base_url.rstrip("/")

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @rate_limiter["ollama"]
    def _fetch_models(self) -> List[str]:
        """
        从 Ollama API 获取模型列表

        该方法从Ollama服务器获取可用的模型列表，并进行适当的错误处理
        使用retry_with_backoff装饰器自动处理临时网络错误和API限流

        Returns:
            List[str]: 模型名称列表，如 ["llama2:7b", "deepseek-r1:8b"]

        Raises:
            ConnectionError: 无法连接到Ollama服务器时抛出
            TimeoutError: 请求超时超过5秒时抛出
            ValueError: API返回错误状态码或无效格式时抛出
            RuntimeError: 其他请求异常时抛出
        """
        models: List[str] = []
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            if "models" in data:
                models = [model["name"] for model in data["models"]]
            return models
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ollama API 连接失败: {str(e)}")
            logger.error(f"请检查 Ollama 服务是否正在运行，URL: {self.base_url}")
            raise ConnectionError(
                f"Ollama API 连接失败: {str(e)}. 请检查 Ollama 服务是否正在运行"
            ) from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama API 请求超时: {str(e)}")
            raise TimeoutError(f"Ollama API 请求超时: {str(e)}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Ollama API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            )
            logger.error(f"响应内容: {e.response.text}")
            raise ValueError(
                f"Ollama API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            ) from e
        except json.JSONDecodeError as e:
            logger.error(f"Ollama API 响应解析失败: {str(e)}")
            raise ValueError(f"Ollama API 响应格式错误") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API 请求失败: {str(e)}")
            raise RuntimeError(f"Ollama API 请求失败: {str(e)}") from e

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @rate_limiter["ollama"]
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        yield_full_response: bool = True,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        调用 Ollama API 生成聊天完成响应

        该方法封装了对Ollama聊天API的调用，支持同步和流式响应两种模式
        使用retry_with_backoff装饰器自动处理临时网络错误和API限流

        Args:
            messages: 聊天消息列表，包含角色(role)和内容(content)字段
                格式: [{"role": "user", "content": "你好"}, ...]
            model: 模型名称，如"llama2:7b", "deepseek-r1:8b"等
            temperature: 生成文本的随机性，范围0.0-1.0
                - 0.0: 生成结果更确定，适合需要精确回答的场景
                - 1.0: 生成结果更随机，适合创造性生成
            stream: 是否启用流式响应
                - True: 返回生成器，逐块返回响应内容
                - False: 等待完整响应后一次性返回
            yield_full_response: 仅在stream=True时有效
                - True: 每次返回截至当前的完整响应文本
                - False: 仅返回当前增量文本
            **kwargs: 其他参数，可传递给Ollama API的额外参数

        Returns:
            str or Generator[str, None, None]:
                - 非流式模式: 返回完整的响应文本字符串
                - 流式模式: 返回生成器，逐块生成响应文本

        Raises:
            ConnectionError: 网络连接失败时抛出
            TimeoutError: 请求超时超过300秒时抛出
            ValueError: 参数错误或API返回错误状态码时抛出
            RuntimeError: 其他请求异常时抛出
        """
        try:
            # 验证输入参数
            if not messages:
                raise ValueError("消息列表不能为空")
            if not model:
                raise ValueError("模型名称不能为空")
            if not (0.0 <= temperature <= 1.0):
                raise ValueError("温度值必须在0.0到1.0之间")

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
                try:
                    return self._process_stream_response(
                        response,
                        response_format="ollama",
                        yield_full_response=yield_full_response,
                    )
                except Exception as stream_e:
                    logger.error(f"Ollama 流式响应处理失败: {str(stream_e)}")
                    raise RuntimeError(f"Ollama 流式响应处理失败: {str(stream_e)}") from stream_e
            else:
                try:
                    data = response.json()
                    return data.get("message", {}).get("content", "")
                except json.JSONDecodeError as e:
                    logger.error(f"Ollama 聊天 API 响应解析失败: {str(e)}")
                    logger.error(f"响应内容: {response.text}")
                    raise ValueError(f"Ollama 聊天 API 响应格式错误") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ollama 聊天 API 连接失败: {str(e)}")
            logger.error(f"请检查 Ollama 服务是否正在运行，URL: {self.base_url}")
            raise ConnectionError(
                f"Ollama 聊天 API 连接失败: {str(e)}. 请检查 Ollama 服务是否正在运行"
            ) from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama 聊天 API 请求超时: {str(e)}")
            raise TimeoutError(f"Ollama 聊天 API 请求超时: {str(e)}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Ollama 聊天 API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            )
            logger.error(f"模型: {model}, 温度: {temperature}")
            logger.error(f"响应内容: {e.response.text}")
            raise ValueError(
                f"Ollama 聊天 API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama 聊天完成调用失败: {str(e)}")
            raise RuntimeError(f"Ollama 聊天完成调用失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"Ollama 聊天 API 未知错误: {str(e)}")
            raise RuntimeError(f"Ollama 聊天 API 未知错误: {str(e)}") from e


class OpenAIAIService(AIServiceInterface):
    """
    OpenAI AI 服务实现
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        """
        初始化 OpenAI AI 服务

        Args:
            api_key: OpenAI API 密钥
            base_url: API 基础 URL，默认为 OpenAI 官方地址
        """
        super().__init__()
        self.api_key: str = api_key
        self.base_url: str = base_url

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @rate_limiter["openai"]
    def _fetch_models(self) -> List[str]:
        """
        从 OpenAI API 获取模型列表

        该方法从OpenAI服务器获取可用的GPT模型列表，并进行适当的错误处理
        使用retry_with_backoff装饰器自动处理临时网络错误和API限流

        Returns:
            List[str]: GPT模型名称列表，如 ["gpt-3.5-turbo", "gpt-4"]

        Raises:
            ConnectionError: 无法连接到OpenAI服务器时抛出
            TimeoutError: 请求超时超过5秒时抛出
            ValueError: API返回错误状态码或无效格式时抛出
            RuntimeError: 其他请求异常时抛出
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
            return models
        except requests.exceptions.ConnectionError as e:
            logger.error(f"OpenAI API 连接失败: {str(e)}")
            logger.error(f"请检查网络连接和 API URL: {self.base_url}")
            raise ConnectionError(
                f"OpenAI API 连接失败: {str(e)}. 请检查网络连接"
            ) from e
        except requests.exceptions.Timeout as e:
            logger.error(f"OpenAI API 请求超时: {str(e)}")
            raise TimeoutError(f"OpenAI API 请求超时: {str(e)}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"OpenAI API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            )
            logger.error(f"响应内容: {e.response.text}")
            if e.response.status_code == 401:
                raise ValueError(f"OpenAI API 认证失败: 无效的 API 密钥") from e
            elif e.response.status_code == 403:
                raise ValueError(f"OpenAI API 访问被拒绝: 权限不足") from e
            else:
                raise ValueError(
                    f"OpenAI API HTTP 错误: {e.response.status_code} - {e.response.reason}"
                ) from e
        except json.JSONDecodeError as e:
            logger.error(f"OpenAI API 响应解析失败: {str(e)}")
            raise ValueError(f"OpenAI API 响应格式错误") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API 调用失败: {str(e)}")
            raise RuntimeError(f"OpenAI API 调用失败: {str(e)}") from e

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @rate_limiter["openai"]
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        yield_full_response: bool = True,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        调用 OpenAI API 生成聊天完成响应

        该方法封装了对OpenAI聊天API的调用，支持同步和流式响应两种模式
        使用retry_with_backoff装饰器自动处理临时网络错误和API限流

        Args:
            messages: 聊天消息列表，包含角色(role)和内容(content)字段
                格式: [{"role": "user", "content": "你好"}, ...]
            model: 模型名称，如"gpt-3.5-turbo", "gpt-4"等
            temperature: 生成文本的随机性，范围0.0-2.0
                - 0.0: 生成结果更确定，适合需要精确回答的场景
                - 1.0: 生成结果更随机，适合创造性生成
            stream: 是否启用流式响应
                - True: 返回生成器，逐块返回响应内容
                - False: 等待完整响应后一次性返回
            yield_full_response: 仅在stream=True时有效
                - True: 每次返回截至当前的完整响应文本
                - False: 仅返回当前增量文本
            **kwargs: 其他参数，可传递给OpenAI API的额外参数

        Returns:
            str or Generator[str, None, None]:
                - 非流式模式: 返回完整的响应文本字符串
                - 流式模式: 返回生成器，逐块生成响应文本

        Raises:
            ConnectionError: 网络连接失败时抛出
            TimeoutError: 请求超时超过300秒时抛出
            ValueError: 参数错误或API返回错误状态码时抛出
            RuntimeError: 其他请求异常时抛出
        """
        try:
            # 验证输入参数
            if not messages:
                raise ValueError("消息列表不能为空")
            if not model:
                raise ValueError("模型名称不能为空")
            if not (0.0 <= temperature <= 2.0):
                raise ValueError("温度值必须在0.0到2.0之间")

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
                try:
                    return self._process_stream_response(
                        response,
                        response_format="openai",
                        yield_full_response=yield_full_response,
                    )
                except Exception as stream_e:
                    logger.error(f"OpenAI 流式响应处理失败: {str(stream_e)}")
                    raise RuntimeError(f"OpenAI 流式响应处理失败: {str(stream_e)}") from stream_e
            else:
                try:
                    data = response.json()
                    return (
                        data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"OpenAI 聊天 API 响应解析失败: {str(e)}")
                    logger.error(f"响应内容: {response.text}")
                    raise ValueError(f"OpenAI 聊天 API 响应格式错误") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"OpenAI 聊天 API 连接失败: {str(e)}")
            logger.error(f"请检查网络连接和 API URL: {self.base_url}")
            raise ConnectionError(
                f"OpenAI 聊天 API 连接失败: {str(e)}. 请检查网络连接"
            ) from e
        except requests.exceptions.Timeout as e:
            logger.error(f"OpenAI 聊天 API 请求超时: {str(e)}")
            raise TimeoutError(f"OpenAI 聊天 API 请求超时: {str(e)}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"OpenAI 聊天 API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            )
            logger.error(f"模型: {model}, 温度: {temperature}")
            logger.error(f"响应内容: {e.response.text}")
            if e.response.status_code == 401:
                raise ValueError(f"OpenAI API 认证失败: 无效的 API 密钥") from e
            elif e.response.status_code == 403:
                raise ValueError(f"OpenAI API 访问被拒绝: 权限不足或模型不可用") from e
            elif e.response.status_code == 429:
                raise ValueError(f"OpenAI API 限流: 请求过于频繁，请稍后重试") from e
            elif e.response.status_code == 503:
                raise ValueError(f"OpenAI API 服务不可用: 服务暂时无法响应") from e
            else:
                raise ValueError(
                    f"OpenAI API HTTP 错误: {e.response.status_code} - {e.response.reason}"
                ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI 聊天完成调用失败: {str(e)}")
            raise RuntimeError(f"OpenAI 聊天完成调用失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"OpenAI 聊天 API 未知错误: {str(e)}")
            raise RuntimeError(f"OpenAI 聊天 API 未知错误: {str(e)}") from e


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
        super().__init__()
        self.api_key: str = api_key
        self.base_url: str = "https://api.deepseek.com/v1"

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @rate_limiter["deepseek"]
    def _fetch_models(self) -> List[str]:
        """
        从 DeepSeek API 获取模型列表

        该方法从DeepSeek服务器获取可用的模型列表，并进行适当的错误处理
        使用retry_with_backoff装饰器自动处理临时网络错误和API限流

        Returns:
            List[str]: 模型名称列表，如 ["deepseek-chat", "deepseek-coder"]

        Raises:
            ConnectionError: 无法连接到DeepSeek服务器时抛出
            TimeoutError: 请求超时超过5秒时抛出
            ValueError: API返回错误状态码或无效格式时抛出
            RuntimeError: 其他请求异常时抛出
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
            return models
        except requests.exceptions.ConnectionError as e:
            logger.error(f"DeepSeek API 连接失败: {str(e)}")
            logger.error(f"请检查网络连接和 API URL: {self.base_url}")
            raise ConnectionError(
                f"DeepSeek API 连接失败: {str(e)}. 请检查网络连接"
            ) from e
        except requests.exceptions.Timeout as e:
            logger.error(f"DeepSeek API 请求超时: {str(e)}")
            raise TimeoutError(f"DeepSeek API 请求超时: {str(e)}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"DeepSeek API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            )
            logger.error(f"响应内容: {e.response.text}")
            if e.response.status_code == 401:
                raise ValueError(f"DeepSeek API 认证失败: 无效的 API 密钥") from e
            elif e.response.status_code == 403:
                raise ValueError(f"DeepSeek API 访问被拒绝: 权限不足") from e
            else:
                raise ValueError(
                    f"DeepSeek API HTTP 错误: {e.response.status_code} - {e.response.reason}"
                ) from e
        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek API 响应解析失败: {str(e)}")
            raise ValueError(f"DeepSeek API 响应格式错误") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API 调用失败: {str(e)}")
            raise RuntimeError(f"DeepSeek API 调用失败: {str(e)}") from e

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @rate_limiter["deepseek"]
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        yield_full_response: bool = True,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        调用 DeepSeek API 生成聊天完成响应

        该方法封装了对DeepSeek聊天API的调用，支持同步和流式响应两种模式
        使用retry_with_backoff装饰器自动处理临时网络错误和API限流

        Args:
            messages: 聊天消息列表，包含角色(role)和内容(content)字段
                格式: [{"role": "user", "content": "你好"}, ...]
            model: 模型名称，如"deepseek-chat", "deepseek-coder"等
            temperature: 生成文本的随机性，范围0.0-1.0
                - 0.0: 生成结果更确定，适合需要精确回答的场景
                - 1.0: 生成结果更随机，适合创造性生成
            stream: 是否启用流式响应
                - True: 返回生成器，逐块返回响应内容
                - False: 等待完整响应后一次性返回
            yield_full_response: 仅在stream=True时有效
                - True: 每次返回截至当前的完整响应文本
                - False: 仅返回当前增量文本
            **kwargs: 其他参数，可传递给DeepSeek API的额外参数

        Returns:
            str or Generator[str, None, None]:
                - 非流式模式: 返回完整的响应文本字符串
                - 流式模式: 返回生成器，逐块生成响应文本

        Raises:
            ConnectionError: 网络连接失败时抛出
            TimeoutError: 请求超时超过300秒时抛出
            ValueError: 参数错误或API返回错误状态码时抛出
            RuntimeError: 其他请求异常时抛出
        """
        try:
            # 验证输入参数
            if not messages:
                raise ValueError("消息列表不能为空")
            if not model:
                raise ValueError("模型名称不能为空")
            if not (0.0 <= temperature <= 1.0):
                raise ValueError("温度值必须在0.0到1.0之间")

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
                try:
                    return self._process_stream_response(
                        response,
                        response_format="openai",
                        yield_full_response=yield_full_response,
                    )
                except Exception as stream_e:
                    logger.error(f"DeepSeek 流式响应处理失败: {str(stream_e)}")
                    raise RuntimeError(f"DeepSeek 流式响应处理失败: {str(stream_e)}") from stream_e
            else:
                try:
                    data = response.json()
                    return (
                        data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"DeepSeek 聊天 API 响应解析失败: {str(e)}")
                    logger.error(f"响应内容: {response.text}")
                    raise ValueError(f"DeepSeek 聊天 API 响应格式错误") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"DeepSeek 聊天 API 连接失败: {str(e)}")
            logger.error(f"请检查网络连接和 API URL: {self.base_url}")
            raise ConnectionError(
                f"DeepSeek 聊天 API 连接失败: {str(e)}. 请检查网络连接"
            ) from e
        except requests.exceptions.Timeout as e:
            logger.error(f"DeepSeek 聊天 API 请求超时: {str(e)}")
            raise TimeoutError(f"DeepSeek 聊天 API 请求超时: {str(e)}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"DeepSeek 聊天 API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            )
            logger.error(f"模型: {model}, 温度: {temperature}")
            logger.error(f"响应内容: {e.response.text}")
            if e.response.status_code == 401:
                raise ValueError(f"DeepSeek API 认证失败: 无效的 API 密钥") from e
            elif e.response.status_code == 403:
                raise ValueError(
                    f"DeepSeek API 访问被拒绝: 权限不足或模型不可用"
                ) from e
            elif e.response.status_code == 429:
                raise ValueError(f"DeepSeek API 限流: 请求过于频繁，请稍后重试") from e
            elif e.response.status_code == 503:
                raise ValueError(f"DeepSeek API 服务不可用: 服务暂时无法响应") from e
            else:
                raise ValueError(
                    f"DeepSeek API HTTP 错误: {e.response.status_code} - {e.response.reason}"
                ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek 聊天完成调用失败: {str(e)}")
            raise RuntimeError(f"DeepSeek 聊天完成调用失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"DeepSeek 聊天 API 未知错误: {str(e)}")
            raise RuntimeError(f"DeepSeek 聊天 API 未知错误: {str(e)}") from e


class OllamaCloudAIService(AIServiceInterface):
    """
    Ollama Cloud AI 服务实现
    直接调用 Ollama Cloud API
    """

    def __init__(self, api_key: str = "", base_url: str = "https://ollama.com"):
        """
        初始化 Ollama Cloud AI 服务

        Args:
            api_key: Ollama Cloud API 密钥
            base_url: API 基础 URL，默认为 Ollama Cloud 官方地址
        """
        super().__init__()
        self.api_key: str = api_key
        self.base_url: str = base_url.rstrip("/")
        logger.info(
            f"初始化 Ollama Cloud AI 服务，base_url: {self.base_url}"
        )

    def _fetch_models(self) -> List[str]:
        """
        获取 Ollama Cloud 模型列表
        返回固定的云端模型列表，这些模型需要通过本地 Ollama 访问云端服务

        该方法返回预定义的Ollama Cloud模型列表，无需实际调用API
        这些模型需要通过本地运行的Ollama服务访问云端资源

        Returns:
            List[str]: 预定义的云端模型名称列表，如 ["minimax-m2:cloud", "kimi-k2-thinking:cloud"]
        """
        # 直接返回默认的 Ollama Cloud 模型列表，这些模型是云端可用的
        models = [
            "minimax-m2:cloud",
            "kimi-k2-thinking:cloud",
            "gemini-3-pro-preview:latest",
            "deepseek-v3.1:671b-cloud",
            "gemma3:27b-cloud",
            "kimi-k2:1t-cloud",
            "qwen3-vl:235b-cloud",
            "gpt-oss:120b-cloud",
            "qwen3-coder:30b",
            "qwen3-vl:8b",
            "qwen3-vl:4b",
            "qwen3-vl:2b",
            "deepseek-r1:8b",
            "llava:7b",
            "llava:13b",
            "llava:34b",
            "phi4:14b",
            "llama4:16x17b",
            "gemma3:4b",
            "qwen3:8b",
            "llama4:latest",
            "gemma3:12b",
            "qwen3:4b",
            "gemma3:1b",
            "qwen3:32b",
            "qwen3:30b",
            "qwen3:14b",
            "qwen3:1.7b",
            "qwen3:0.6b",
            "qwen3:30b-a3b",
            "gemma3:27b",
            "deepseek-r1:70b",
            "deepseek-r1:1.5b",
            "deepseek-r1:32b",
            "phi4:latest",
            "llama3.3:latest",
            "deepseek-r1:7b",
            "deepseek-r1:14b",
        ]
        logger.info(f"✅ 使用固定的 Ollama Cloud 模型列表，共 {len(models)} 个模型")
        return models

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @rate_limiter["ollamacloud"]
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.8,
        stream: bool = False,
        yield_full_response: bool = True,
        **kwargs,
    ) -> str | Generator[str, None, None]:
        """
        调用 Ollama Cloud API 生成聊天完成响应
        直接调用云端API，不依赖本地Ollama服务

        该方法通过直接调用Ollama Cloud API生成聊天响应，支持同步和流式响应两种模式
        使用retry_with_backoff装饰器自动处理临时网络错误和API限流

        Args:
            messages: 聊天消息列表，包含角色(role)和内容(content)字段
                格式: [{"role": "user", "content": "你好"}, ...]
            model: 模型名称，如"minimax-m2:cloud", "kimi-k2-thinking:cloud"等
            temperature: 生成文本的随机性，范围0.0-1.0
                - 0.0: 生成结果更确定，适合需要精确回答的场景
                - 1.0: 生成结果更随机，适合创造性生成
            stream: 是否启用流式响应
                - True: 返回生成器，逐块返回响应内容
                - False: 等待完整响应后一次性返回
            yield_full_response: 仅在stream=True时有效
                - True: 每次返回截至当前的完整响应文本
                - False: 仅返回当前增量文本
            **kwargs: 其他参数，可传递给Ollama Cloud API的额外参数

        Returns:
            str or Generator[str, None, None]:
                - 非流式模式: 返回完整的响应文本字符串
                - 流式模式: 返回生成器，逐块生成响应文本

        Raises:
            ConnectionError: 无法连接到Ollama Cloud服务器时抛出
            TimeoutError: 请求超时超过300秒时抛出
            ValueError: 参数错误或API返回错误状态码时抛出
            RuntimeError: 其他请求异常时抛出
        """
        logger.info(f"使用 Ollama Cloud API 处理模型请求，模型: {model}")

        try:
            # 验证输入参数
            if not messages:
                raise ValueError("消息列表不能为空")
            if not model:
                raise ValueError("模型名称不能为空")
            if not (0.0 <= temperature <= 1.0):
                raise ValueError("温度值必须在0.0到1.0之间")

            # 构建正确的 Ollama Cloud API 请求 payload
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "options": {"temperature": temperature},
            }

            # 使用 Ollama Cloud API 端点
            chat_endpoint = f"{self.base_url}/api/chat"
            logger.info(f"使用 Ollama Cloud API 端点: {chat_endpoint}")
            # 不记录完整payload，避免泄露敏感信息
            logger.info(f"请求模型: {model}, 流式: {stream}, 温度: {temperature}")

            # 构建请求头，包含 API 密钥
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                logger.debug("已添加Authorization头")
            else:
                logger.warning("Ollama Cloud API 密钥未设置")
            
            # 发送请求
            response = requests.post(
                chat_endpoint,
                headers=headers,
                json=payload,
                stream=stream,
                timeout=300,
            )

            logger.info(f"Ollama Cloud API 响应状态码: {response.status_code}")
            logger.debug(f"响应头: {dict(response.headers)}")

            # 检查响应状态码
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error(f"响应内容: {response.text}")
                if e.response.status_code == 401:
                    logger.error(f"401错误 - API密钥可能无效或缺失: {self.api_key[:10]}...")
                raise

            if stream:
                try:
                    # 使用 Ollama 格式处理流式响应
                    return self._process_stream_response(
                        response,
                        response_format="ollama",
                        yield_full_response=yield_full_response,
                    )
                except Exception as stream_e:
                    logger.error(f"Ollama Cloud 流式响应处理失败: {str(stream_e)}")
                    raise RuntimeError(f"Ollama Cloud 流式响应处理失败: {str(stream_e)}") from stream_e
            else:
                try:
                    # 处理非流式响应
                    data = response.json()
                    # 不记录完整响应，避免泄露敏感信息
                    logger.info(f"Ollama Cloud API 响应: 成功")

                    # Ollama 格式的响应，内容在 message.content 中
                    return data.get("message", {}).get("content", "")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ollama Cloud API 响应解析失败: {str(e)}")
                    logger.error(f"响应内容: {response.text}")
                    raise ValueError(f"Ollama Cloud API 响应格式错误") from e

        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Ollama Cloud API 连接失败: {str(e)}")
            logger.error(f"请检查网络连接和 API URL: {self.base_url}")
            raise ConnectionError(
                f"Ollama Cloud API 连接失败: {str(e)}. 请检查网络连接"
            ) from e
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ Ollama Cloud API 请求超时: {str(e)}")
            raise TimeoutError(f"Ollama Cloud API 请求超时: {str(e)}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"❌ Ollama Cloud API HTTP 错误: {e.response.status_code} - {e.response.reason}"
            )
            logger.error(f"模型: {model}, 温度: {temperature}")
            # 记录响应内容以便调试
            if hasattr(e.response, 'text'):
                logger.error(f"响应内容: {e.response.text[:500]}...")
            if e.response.status_code == 401:
                raise ValueError(
                    f"Ollama Cloud API 认证失败: 无效的 API 密钥或未设置"
                ) from e
            elif e.response.status_code == 404:
                raise ValueError(
                    f"Ollama Cloud 模型未找到: {model}. 请检查模型名称是否正确"
                ) from e
            elif e.response.status_code == 500:
                raise RuntimeError(f"Ollama Cloud 服务内部错误. 请稍后重试") from e
            else:
                raise ValueError(
                    f"Ollama Cloud API HTTP 错误: {e.response.status_code} - {e.response.reason}"
                ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ollama Cloud API 调用失败: {str(e)}")
            raise RuntimeError(f"Ollama Cloud API 请求失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"❌ Ollama Cloud API 未知错误: {str(e)}")
            raise RuntimeError(f"Ollama Cloud API 未知错误: {str(e)}") from e


class AIServiceFactory:
    """
    AI 服务工厂类，用于创建不同类型的 AI 服务实例
    """

    @staticmethod
    def create_ai_service(service_type: str, **kwargs) -> AIServiceInterface:
        """
        创建 AI 服务实例

        Args:
            service_type: 服务类型，可选值："ollama", "openai", "deepseek", "ollama_cloud"
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
        elif service_type == "ollama_cloud":
            return OllamaCloudAIService(**kwargs)
        else:
            raise ValueError(f"不支持的 AI 服务类型: {service_type}")
