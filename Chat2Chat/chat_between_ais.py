import os
import time
import argparse
import json
import requests
import logging
import sys
import gc
import re
import contextlib
from typing import List, Dict, Any, Optional, Union, Tuple, Callable, TypeVar
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 导入日志配置模块
from logger_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 加载环境变量 - 明确指定可执行文件所在目录下的.env文件
# 处理PyInstaller打包后的情况
if getattr(sys, 'frozen', False):
    # 打包后的可执行文件所在目录
    current_dir = os.path.dirname(sys.executable)
else:
    # 开发环境下的当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

# 使用f-strings简化路径拼接
env_path = f"{current_dir}/.env"
load_dotenv(dotenv_path=env_path)

class AIChatManager:
    """
    AI聊天管理器类，用于管理不同AI API的调用和对话。
    
    该类支持OpenAI、DeepSeek、Ollama三种API，能够管理两个AI之间的对话，
    包括讨论和辩论两种模式。
    """
    
    def __init__(self, model1_name: str = "qwen3:14b", model2_name: str = "deepseek-r1:14b", 
                 model1_api: str = "ollama", model2_api: str = "ollama",
                 openai_api_key: str = None, deepseek_api_key: str = None,
                 ollama_base_url: str = None, temperature: float = 0.8,
                 common_system_prompt: str = None, ai1_system_prompt: str = None, ai2_system_prompt: str = None,
                 debate_common_prompt: str = None, debate_ai1_prompt: str = None, debate_ai2_prompt: str = None):
        """
        初始化AI聊天管理器。
        
        Args:
            model1_name: 第一个AI模型名称
            model2_name: 第二个AI模型名称
            model1_api: 第一个AI使用的API类型，可选值：openai、deepseek、ollama
            model2_api: 第二个AI使用的API类型，可选值：openai、deepseek、ollama
            openai_api_key: OpenAI API密钥
            deepseek_api_key: DeepSeek API密钥
            ollama_base_url: Ollama API基础URL
            temperature: 生成文本的随机性，范围0.0-2.0
            common_system_prompt: 通用系统提示词，将应用于所有AI
            ai1_system_prompt: 第一个AI的系统提示词
            ai2_system_prompt: 第二个AI的系统提示词
            debate_common_prompt: 辩论模式下的通用系统提示词
            debate_ai1_prompt: 辩论模式下第一个AI的系统提示词
            debate_ai2_prompt: 辩论模式下第二个AI的系统提示词
        """
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.model1_api = model1_api
        self.model2_api = model2_api
        self.temperature = temperature
        
        # 初始化各API的配置
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # 初始化系统提示词
        self.common_system_prompt = common_system_prompt or os.getenv("COMMON_SYSTEM_PROMPT", "")
        self.ai1_system_prompt = ai1_system_prompt or os.getenv("AI1_SYSTEM_PROMPT", "")
        self.ai2_system_prompt = ai2_system_prompt or os.getenv("AI2_SYSTEM_PROMPT", "")
        
        # 组合系统提示词（讨论模式）
        self.full_ai1_system_prompt = self.common_system_prompt
        if self.ai1_system_prompt:
            self.full_ai1_system_prompt += "\n" + self.ai1_system_prompt
        
        self.full_ai2_system_prompt = self.common_system_prompt
        if self.ai2_system_prompt:
            self.full_ai2_system_prompt += "\n" + self.ai2_system_prompt
        
        # 初始化辩论系统提示词
        self.debate_common_prompt = debate_common_prompt or os.getenv("DEBATE_COMMON_PROMPT", "")
        self.debate_ai1_prompt = debate_ai1_prompt or os.getenv("DEBATE_AI1_PROMPT", "")
        self.debate_ai2_prompt = debate_ai2_prompt or os.getenv("DEBATE_AI2_PROMPT", "")
        
        # 组合系统提示词（辩论模式）
        self.full_debate_ai1_prompt = self.debate_common_prompt
        if self.debate_ai1_prompt:
            self.full_debate_ai1_prompt += "\n" + self.debate_ai1_prompt
        
        self.full_debate_ai2_prompt = self.debate_common_prompt
        if self.debate_ai2_prompt:
            self.full_debate_ai2_prompt += "\n" + self.debate_ai2_prompt
        
        # 初始化OpenAI客户端（如果需要）
        if self.openai_api_key:
            # 显式创建httpx.Client实例，避免proxies参数问题
            import httpx
            # 创建不带proxies参数的HTTP客户端
            http_client = httpx.Client(timeout=300)
            self.openai_client = OpenAI(api_key=self.openai_api_key, http_client=http_client, timeout=300)
        else:
            self.openai_client = None
        
        # 验证必要的API密钥
        if self.model1_api == "openai" and not self.openai_api_key:
            raise ValueError("请提供OpenAI API密钥或在.env文件中设置OPENAI_API_KEY环境变量")
        if self.model2_api == "openai" and not self.openai_api_key:
            raise ValueError("请提供OpenAI API密钥或在.env文件中设置OPENAI_API_KEY环境变量")
        if self.model1_api == "deepseek" and not self.deepseek_api_key:
            raise ValueError("请提供DeepSeek API密钥或在.env文件中设置DEEPSEEK_API_KEY环境变量")
        if self.model2_api == "deepseek" and not self.deepseek_api_key:
            raise ValueError("请提供DeepSeek API密钥或在.env文件中设置DEEPSEEK_API_KEY环境变量")
    
    def _get_ollama_models(self):
        """
        获取Ollama服务器上的可用模型列表。
        
        该方法尝试从Ollama服务器获取可用模型列表，支持多种端点。
        首先尝试标准的/api/tags端点，如果失败则尝试/v1/models端点。
        
        Returns:
            list: 可用模型名称列表，如果获取失败则返回空列表
        """
        try:
            # 创建带增强重试机制的会话
            session = requests.Session()
            retry = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],  # 添加429 (Too Many Requests)
                allowed_methods=["GET", "POST"]
            )
            adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            # 尝试标准的/api/tags端点
            ollama_base_url = self.ollama_base_url.rstrip('/')
            response = session.get(f"{ollama_base_url}/api/tags", timeout=30)
            response.raise_for_status()  # 抛出HTTP错误
            
            models_data = response.json()
            # 解析模型列表
            if "models" in models_data and isinstance(models_data["models"], list):
                model_list = [model["name"] for model in models_data["models"]]
                logger.info(f"获取到可用模型列表: {', '.join(model_list)}")
                return model_list
            
            # 如果/api/tags失败，尝试其他可能的端点
            response = session.get(f"{ollama_base_url}/v1/models", timeout=30)
            response.raise_for_status()  # 抛出HTTP错误
            
            models_data = response.json()
            if "data" in models_data and isinstance(models_data["data"], list):
                model_list = [model["id"] for model in models_data["data"]]
                logger.info(f"获取到可用Ollama模型列表: {', '.join(model_list)}")
                return model_list
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"获取Ollama模型列表失败 - HTTP错误: {e}")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"获取Ollama模型列表失败 - 连接错误: {e}")
            return []
        except requests.exceptions.Timeout as e:
            logger.error(f"获取Ollama模型列表失败 - 请求超时: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"获取Ollama模型列表失败 - JSON解析错误: {e}")
            return []
        except Exception as e:
            logger.error(f"获取Ollama模型列表失败 - 未知错误: {e}")
            return []
        return []
        
    def _select_smallest_model(self, models: list[str]) -> str | None:
        """
        从模型列表中选择一个较小的模型，基于模型名称中包含的参数量信息。
        
        该方法根据模型名称中的关键词（如7b、14b等）来判断模型大小，
        并选择最小的模型。
        
        Args:
            models: 模型名称列表
            
        Returns:
            str | None: 选择的最小模型名称，如果列表为空则返回None
        """
        if not models:
            return None
            
        # 定义模型大小优先级（根据名称中的关键词）
        size_keywords = {
            # 最小的模型在前
            '0.6b': 0, '1b': 1, '2b': 2, '3b': 3, '7b': 4,
            '13b': 5, '14b': 6, '30b': 7, '70b': 8, '120b': 9
        }
        
        # 为每个模型评分
        def score_model(model: str) -> tuple[int, str]:
            model_lower = model.lower()
            score = 100  # 默认最高分数（最大模型）
            
            # 检查是否包含小模型的关键词
            for keyword, keyword_score in size_keywords.items():
                if keyword in model_lower:
                    score = keyword_score
                    break
            
            # 额外检查vision和llava等可能较小的模型
            if any(prefix in model_lower for prefix in ['vision', 'llava', 'qwen']):
                score = min(score, 5)  # 给这些模型一个中等分数
                
            # 检查是否包含gpt或deepseek等可能较大的模型
            if any(prefix in model_lower for prefix in ['gpt', 'deepseek']):
                score = max(score, 10)  # 给这些模型一个较高分数
                
            return score, model
        
        # 按分数排序，选择最小的（分数最低的）
        selected_model = min(models, key=score_model)
        print(f"选择的小模型: {selected_model}")
        return selected_model
        
    def _parse_deepseek_response(self, json_response) -> str:
        """
        专门用于解析DeepSeek模型的响应，保留原始内容
        
        Args:
            json_response: 响应内容，可以是字典或字符串
            
        Returns:
            str: 解析后的文本内容
        """
        # 定义清理函数，用于在各个路径中重用
        def clean_content(raw_content: str) -> str:
            # 完全保留原始内容
            return raw_content
        
        try:
            # 使用match-case简化类型判断
            match json_response:
                case dict():
                    # 定义内容提取路径的优先级列表
                    content_paths = [
                        ("choices", 0, "message", "content"),  # OpenAI标准格式
                        ("message", "content"),               # 简化消息格式
                        ("content",),                          # 直接内容
                        ("response",)                          # 响应字段
                    ]
                    
                    # 按优先级尝试各个路径
                    for path in content_paths:
                        data = json_response
                        valid = True
                        
                        for key in path:
                            try:
                                if isinstance(data, dict) and key in data:
                                    data = data[key]
                                elif isinstance(data, list) and isinstance(key, int) and 0 <= key < len(data):
                                    data = data[key]
                                else:
                                    valid = False
                                    break
                            except (KeyError, IndexError, TypeError):
                                valid = False
                                break
                        
                        if valid and isinstance(data, str) and data.strip():
                            return clean_content(data)
                    
                    # 尝试将整个字典转换为字符串作为后备方案
                    response_str = json.dumps(json_response, ensure_ascii=False)
                    return clean_content(response_str)
                
                case str():
                    # 尝试将字符串解析为JSON
                    if json_response.strip().startswith('{') and json_response.strip().endswith('}'):
                        try:
                            dict_response = json.loads(json_response)
                            return self._parse_deepseek_response(dict_response)  # 递归调用以复用解析逻辑
                        except json.JSONDecodeError:
                            pass  # 解析失败则回退到直接返回字符串
                    return clean_content(json_response)
                
                case _:
                    # 如果无法识别类型
                    logger.warning("无法识别的响应类型")
                    return "我是一个AI助手，很高兴为您服务。"
            
        except json.JSONDecodeError as e:
            logger.error(f"解析DeepSeek响应失败 - JSON解析错误: {e}")
            return "我是一个AI助手，很高兴为您服务。"
        except Exception as e:
            logger.error(f"解析DeepSeek响应失败 - 未知错误: {e}")
            return "我是一个AI助手，很高兴为您服务。"
    
    def get_ai_response(self, model_name: str, messages: List[Dict[str, str]], api_type: str = "ollama") -> str:
        """
        获取AI模型的响应，支持多种API类型，包含资源管理和错误处理。
        
        该方法是一个调度器，根据指定的API类型调用对应的处理函数，
        支持ollama、openai、deepseek三种API类型。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            api_type: API类型，可选值：ollama, openai, deepseek
            
        Returns:
            str: AI模型的响应内容，发生错误时返回友好提示信息
        """
        # 使用logger替代print进行调试信息记录
        logger.info(f"\n{'='*50}\n调用get_ai_response - 模型: {model_name}, API类型: {api_type}")
        logger.info(f"消息列表长度: {len(messages)}")
        if messages:
            last_msg = messages[-1]
            logger.info(f"最后一条消息: {last_msg['role']}: {last_msg['content'][:100]}...")
        
        # 内存优化：创建消息副本以避免修改原始数据，并限制消息长度
        messages_copy = [msg.copy() for msg in messages]
        
        # 限制消息列表长度，避免内存占用过高
        max_messages = 100  # 最多保留100条消息
        if len(messages_copy) > max_messages:
            # 保留系统提示和最近的消息
            system_messages = [msg for msg in messages_copy if msg['role'] == 'system']
            recent_messages = messages_copy[-max_messages + len(system_messages):]
            messages_copy = system_messages + recent_messages
            logger.info(f"内存优化：消息列表长度从 {len(messages)} 减少到 {len(messages_copy)}")
        
        # 使用上下文管理器确保资源正确释放
        with self._resource_manager():
            try:
                # 使用调度器模式处理不同API类型
                if (handler := getattr(self, f"_handle_{api_type}_request", None)) is None:
                    logger.error(f"不支持的API类型: {api_type}")
                    return "抱歉，不支持的AI模型类型。"
                
                # 调用对应的处理函数
                response = handler(model_name, messages_copy)
                
                # 内存优化：立即清理不再需要的大型对象
                del messages_copy[:]  # 清空列表内容
                del handler
                gc.collect()  # 强制垃圾回收
                
                return response
                
            except requests.exceptions.Timeout:
                logger.error("请求超时错误")
                return "抱歉，请求超时，请检查网络连接或稍后再试。"
            except requests.exceptions.ConnectionError:
                logger.error("连接错误")
                return "抱歉，无法连接到服务器，请检查网络连接。"
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP错误: {e}")
                return f"服务器返回错误: {str(e)[:100]}..."
            except Exception as e:
                logger.error(f"获取AI响应时发生错误: {e}")
                logger.error(f"错误类型: {type(e).__name__}")
                return "抱歉，我暂时无法提供回答。请稍后再试。"
    
    def get_ai_stream_response(self, model_name: str, messages: List[Dict[str, str]], api_type: str = "ollama"):
        """
        获取AI模型的流式响应，支持多种API类型。
        
        该方法是一个调度器，根据指定的API类型调用对应的处理函数，
        支持ollama、openai、deepseek三种API类型的流式输出。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            api_type: API类型，可选值：ollama, openai, deepseek
            
        Yields:
            str: AI模型的响应内容片段
        """
        # 使用logger替代print进行调试信息记录
        logger.info(f"\n{'='*50}\n调用get_ai_stream_response - 模型: {model_name}, API类型: {api_type}")
        logger.info(f"消息列表长度: {len(messages)}")
        if messages:
            last_msg = messages[-1]
            logger.info(f"最后一条消息: {last_msg['role']}: {last_msg['content'][:100]}...")
        
        # 内存优化：创建消息副本以避免修改原始数据，并限制消息长度
        messages_copy = [msg.copy() for msg in messages]
        
        # 限制消息列表长度，避免内存占用过高
        max_messages = 100  # 最多保留100条消息
        if len(messages_copy) > max_messages:
            # 保留系统提示和最近的消息
            system_messages = [msg for msg in messages_copy if msg['role'] == 'system']
            recent_messages = messages_copy[-max_messages + len(system_messages):]
            messages_copy = system_messages + recent_messages
            logger.info(f"内存优化：消息列表长度从 {len(messages)} 减少到 {len(messages_copy)}")
        
        try:
            # 使用调度器模式处理不同API类型
            if (handler := getattr(self, f"_handle_{api_type}_stream_request", None)) is None:
                logger.error(f"不支持的API类型: {api_type}")
                yield "抱歉，不支持的AI模型类型。"
                return
            
            # 调用对应的处理函数
            for chunk in handler(model_name, messages_copy):
                yield chunk
            
            # 内存优化：立即清理不再需要的大型对象
            del messages_copy[:]  # 清空列表内容
            del handler
            gc.collect()  # 强制垃圾回收
            
        except requests.exceptions.Timeout:
            logger.error("请求超时错误")
            yield "抱歉，请求超时，请检查网络连接或稍后再试。"
        except requests.exceptions.ConnectionError:
            logger.error("连接错误")
            yield "抱歉，无法连接到服务器，请检查网络连接。"
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {e}")
            yield f"服务器返回错误: {str(e)[:100]}..."
        except Exception as e:
            logger.error(f"获取AI响应时发生错误: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            yield "抱歉，我暂时无法提供回答。请稍后再试。"
    
    def _resource_manager(self) -> contextlib.AbstractContextManager:
        """
        上下文管理器，用于管理API请求过程中的资源。
        
        该上下文管理器在请求开始时准备资源，在请求结束时清理资源，
        确保资源正确释放，避免内存泄漏。
        
        Returns:
            contextlib.AbstractContextManager: 上下文管理器实例
        """
        import contextlib
        
        @contextlib.contextmanager
        def resource_context():
            try:
                # 请求开始时的资源准备
                logger.debug("资源管理: 请求开始")
                yield
            except Exception as e:
                logger.error(f"请求异常: {type(e).__name__}: {e}")
                raise
            finally:
                # 请求结束时的资源清理
                logger.debug("资源管理: 请求结束，清理资源")
                # 执行垃圾回收
                gc.collect()
        
        return resource_context()
    
    def _handle_ollama_request(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理Ollama API请求的封装方法。
        
        该方法是Ollama API请求的封装，调用_get_ollama_response方法获取响应。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Returns:
            str: AI响应内容，发生错误时返回友好提示信息
        """
        return self._get_ollama_response(model_name, messages)
    
    def _handle_openai_request(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理OpenAI API请求的封装方法。
        
        该方法是OpenAI API请求的封装，调用_get_openai_response方法获取响应。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Returns:
            str: AI响应内容，发生错误时返回友好提示信息
        """
        return self._get_openai_response(model_name, messages)
    
    def _handle_deepseek_request(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理DeepSeek API请求的封装方法。
        
        该方法是DeepSeek API请求的封装，调用_get_deepseek_response方法获取响应。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Returns:
            str: AI响应内容，发生错误时返回友好提示信息
        """
        return self._get_deepseek_response(model_name, messages)
    
    def _handle_ollama_stream_request(self, model_name: str, messages: List[Dict[str, str]]):
        """
        处理Ollama API流式请求。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Yields:
            str: AI响应内容片段
        """
        logger.info(f"调用Ollama API（流式） - 模型: {model_name}")
        
        # 使用上下文管理器管理会话资源
        with requests.Session() as session:
            # 创建带增强重试机制的会话
            retry = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"]
            )
            adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            try:
                # 构建Ollama API请求
                ollama_base_url = self.ollama_base_url.rstrip('/')
                endpoint = f"{ollama_base_url}/api/chat"
                
                # 请求参数
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": True  # 流式响应
                }
                
                # 发送请求
                logger.debug(f"向Ollama发送请求 - URL: {endpoint}, 数据大小: {len(str(payload))} 字符")
                response = session.post(endpoint, json=payload, stream=True, timeout=300)
                response.raise_for_status()  # 抛出HTTP错误
                
                # 解析响应
                for chunk in response.iter_lines():
                    if chunk:
                        chunk_str = chunk.decode('utf-8')
                        if chunk_str.strip():
                            try:
                                response_data = json.loads(chunk_str)
                                if (message := response_data.get("message")) and (content := message.get("content")):
                                    yield content
                            except json.JSONDecodeError:
                                logger.error(f"解析Ollama流式响应失败: {chunk_str}")
                                continue
                                
            except requests.exceptions.HTTPError as e:
                logger.error(f"Ollama API HTTP错误: {e}")
                if e.response and e.response.status_code == 404:
                    yield f"找不到Ollama模型: {model_name}，请确认模型已安装。"
                else:
                    yield f"请求处理失败: {str(e)[:50]}..."
                    
            except requests.exceptions.ConnectionError:
                logger.error("Ollama连接错误")
                yield "无法连接到Ollama服务器，请检查服务器地址和网络连接。"
                
            except requests.exceptions.Timeout:
                logger.error("Ollama请求超时")
                yield "请求超时，请稍后再试。"
                
            except json.JSONDecodeError:
                logger.error("Ollama响应JSON解析错误")
                yield "无法解析服务器响应，请稍后再试。"
                
            except Exception as e:
                logger.error(f"Ollama API未知错误: {e}")
                yield "抱歉，处理您的请求时发生了未知错误。"
    
    def _handle_openai_stream_request(self, model_name: str, messages: List[Dict[str, str]]):
        """
        处理OpenAI API流式请求。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Yields:
            str: AI响应内容片段
        """
        logger.info(f"调用OpenAI API（流式） - 模型: {model_name}")
        
        # 验证OpenAI客户端是否已初始化
        if not self.openai_client:
            logger.error("OpenAI客户端未初始化，请检查API密钥")
            yield "抱歉，无法连接到OpenAI服务，请检查API密钥配置。"
            return
        
        try:
            # 发送请求到OpenAI API
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=4096,  # 设置最大token数
                stream=True  # 流式响应
            )
            
            # 提取响应内容
            for chunk in response:
                if (choices := getattr(chunk, 'choices', [])) and len(choices) > 0:
                    if (choice := choices[0]) and (delta := getattr(choice, 'delta', None)):
                        if (content := getattr(delta, 'content', None)):
                            yield content
                            
        except Exception as e:
            logger.error(f"OpenAI API请求失败: {e}")
            # 处理不同类型的OpenAI错误
            error_str = str(e).lower()
            
            # 根据错误类型返回不同的提示信息
            match True:
                case _ if "invalid_api_key" in error_str or "authentication" in error_str:
                    yield "OpenAI API密钥无效，请检查您的密钥配置。"
                case _ if "insufficient_quota" in error_str or "billing" in error_str:
                    yield "OpenAI API额度不足，请检查您的账户状态。"
                case _ if "model_not_found" in error_str or "model is not available" in error_str:
                    yield f"找不到OpenAI模型: {model_name}，请使用有效的模型名称。"
                case _ if "context_length_exceeded" in error_str or "maximum context length" in error_str:
                    yield "输入内容过长，请减少消息长度后重试。"
                case _:
                    # 截断错误消息，避免显示过多技术细节
                    error_summary = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                    yield f"OpenAI服务暂时不可用: {error_summary}"
    
    def _handle_deepseek_stream_request(self, model_name: str, messages: List[Dict[str, str]]):
        """
        处理DeepSeek API流式请求。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Yields:
            str: AI响应内容片段
        """
        logger.info(f"调用DeepSeek API（流式） - 模型: {model_name}")
        
        # 验证API密钥
        if not self.deepseek_api_key:
            logger.error("DeepSeek API密钥未配置")
            yield "抱歉，无法连接到DeepSeek服务，请检查API密钥配置。"
            return
        
        # 使用上下文管理器管理会话资源
        with requests.Session() as session:
            # 创建带增强重试机制的会话
            retry = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"]
            )
            adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
            session.mount('https://', adapter)
            
            try:
                # DeepSeek API的基础URL
                deepseek_base_url = "https://api.deepseek.com/v1"
                endpoint = f"{deepseek_base_url}/chat/completions"
                
                # 请求头部
                headers = {
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                }
                
                # 请求参数
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": 4096,  # 设置最大token数
                    "stream": True  # 流式响应
                }
                
                # 发送请求
                logger.debug(f"向DeepSeek发送请求 - URL: {endpoint}, 数据大小: {len(str(payload))} 字符")
                response = session.post(endpoint, headers=headers, json=payload, stream=True, timeout=300)
                response.raise_for_status()  # 抛出HTTP错误
                
                # 解析响应
                for chunk in response.iter_lines():
                    if chunk:
                        chunk_str = chunk.decode('utf-8')
                        if chunk_str.startswith('data: '):
                            chunk_str = chunk_str[6:]
                            if chunk_str.strip() == '[DONE]':
                                break
                            try:
                                response_data = json.loads(chunk_str)
                                if (choices := response_data.get("choices")) and len(choices) > 0:
                                    if (choice := choices[0]) and (delta := choice.get("delta")):
                                        if (content := delta.get("content")):
                                            yield content
                            except json.JSONDecodeError:
                                logger.error(f"解析DeepSeek流式响应失败: {chunk_str}")
                                continue
                                
            except requests.exceptions.HTTPError as e:
                logger.error(f"DeepSeek API HTTP错误: {e}")
                error_str = str(e).lower()
                
                # 尝试解析错误响应
                error_msg = None
                if e.response:
                    try:
                        if (error_data := e.response.json()) and (error_info := error_data.get("error")):
                            error_msg = error_info.get("message", "")
                            logger.error(f"DeepSeek API错误消息: {error_msg}")
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                # 根据错误类型返回不同的提示信息
                match True:
                    case _ if "invalid_api_key" in error_str or "authentication" in error_str:
                        yield "DeepSeek API密钥无效，请检查您的密钥配置。"
                    case _ if "insufficient_quota" in error_str or "billing" in error_str:
                        yield "DeepSeek API额度不足，请检查您的账户状态。"
                    case _ if "model_not_found" in error_str or "model is not available" in error_str:
                        yield f"找不到DeepSeek模型: {model_name}，请使用有效的模型名称。"
                    case _:
                        yield f"DeepSeek服务错误: {error_msg[:100] if error_msg else str(e)[:100]}..."
                        
            except requests.exceptions.ConnectionError:
                logger.error("DeepSeek连接错误")
                yield "无法连接到DeepSeek服务器，请检查网络连接。"
                
            except requests.exceptions.Timeout:
                logger.error("DeepSeek请求超时")
                yield "请求超时，请稍后再试。"
                
            except json.JSONDecodeError:
                logger.error("DeepSeek响应JSON解析错误")
                yield "无法解析服务器响应，请稍后再试。"
                
            except Exception as e:
                logger.error(f"DeepSeek API未知错误: {e}")
                yield "抱歉，处理您的请求时发生了未知错误。"
    
    def _get_ollama_response(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理Ollama API请求并返回响应内容。
        
        该方法直接调用Ollama API，发送请求并处理响应。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Returns:
            str: AI响应内容，发生错误时返回友好提示信息
        """
        logger.info(f"调用Ollama API - 模型: {model_name}")
        
        # 使用上下文管理器管理会话资源
        with requests.Session() as session:
            # 创建带增强重试机制的会话
            retry = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"]
            )
            adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            try:
                # 构建Ollama API请求
                ollama_base_url = self.ollama_base_url.rstrip('/')
                endpoint = f"{ollama_base_url}/api/chat"
                
                # 请求参数
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": False  # 非流式响应
                }
                
                # 发送请求
                logger.debug(f"向Ollama发送请求 - URL: {endpoint}, 数据大小: {len(str(payload))} 字符")
                response = session.post(endpoint, json=payload, timeout=300)
                response.raise_for_status()  # 抛出HTTP错误
                
                # 解析响应
                response_data = response.json()
                
                # 提取响应内容
                if (message := response_data.get("message")) and (content := message.get("content")):
                    logger.info(f"成功获取Ollama响应 - 内容长度: {len(content)} 字符")
                    return content
                else:
                    logger.error(f"Ollama响应格式不正确: {response_data}")
                    return "抱歉，我暂时无法提供回答。"
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"Ollama API HTTP错误: {e}")
                if e.response and e.response.status_code == 404:
                    return f"找不到Ollama模型: {model_name}，请确认模型已安装。"
                return f"请求处理失败: {str(e)[:50]}..."
                
            except requests.exceptions.ConnectionError:
                logger.error("Ollama连接错误")
                return "无法连接到Ollama服务器，请检查服务器地址和网络连接。"
                
            except requests.exceptions.Timeout:
                logger.error("Ollama请求超时")
                return "请求超时，请稍后再试。"
                
            except json.JSONDecodeError:
                logger.error("Ollama响应JSON解析错误")
                return "无法解析服务器响应，请稍后再试。"
                
            except Exception as e:
                logger.error(f"Ollama API未知错误: {e}")
                return "抱歉，处理您的请求时发生了未知错误。"
            
        # 会话会在with块结束后自动关闭，无需手动清理
    

    
    def _get_openai_response(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理OpenAI API请求并返回响应内容。
        
        该方法使用OpenAI Python SDK调用OpenAI API，发送请求并处理响应。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Returns:
            str: AI响应内容，发生错误时返回友好提示信息
        """
        logger.info(f"调用OpenAI API - 模型: {model_name}")
        
        # 验证OpenAI客户端是否已初始化
        if not self.openai_client:
            logger.error("OpenAI客户端未初始化，请检查API密钥")
            return "抱歉，无法连接到OpenAI服务，请检查API密钥配置。"
        
        try:
            # 发送请求到OpenAI API
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=4096  # 设置最大token数
            )
            
            # 提取响应内容，使用海象运算符简化代码
            if (choices := getattr(response, 'choices', [])) and len(choices) > 0:
                if (choice := choices[0]) and (message := getattr(choice, 'message', None)):
                    if (content := getattr(message, 'content', None)):
                        logger.info(f"成功获取OpenAI响应 - 内容长度: {len(content)} 字符")
                        return content
                    else:
                        logger.error(f"OpenAI响应缺少content字段: {response}")
                else:
                    logger.error(f"OpenAI响应缺少message字段: {response}")
            else:
                logger.error(f"OpenAI响应格式不正确: {response}")
            
            return "抱歉，我暂时无法提供回答。"
                
        except Exception as e:
            logger.error(f"OpenAI API请求失败: {e}")
            # 处理不同类型的OpenAI错误
            error_str = str(e).lower()
            
            # 根据错误类型返回不同的提示信息
            match True:
                case _ if "invalid_api_key" in error_str or "authentication" in error_str:
                    return "OpenAI API密钥无效，请检查您的密钥配置。"
                case _ if "insufficient_quota" in error_str or "billing" in error_str:
                    return "OpenAI API额度不足，请检查您的账户状态。"
                case _ if "model_not_found" in error_str or "model is not available" in error_str:
                    return f"找不到OpenAI模型: {model_name}，请使用有效的模型名称。"
                case _ if "context_length_exceeded" in error_str or "maximum context length" in error_str:
                    return "输入内容过长，请减少消息长度后重试。"
                case _:
                    # 截断错误消息，避免显示过多技术细节
                    error_summary = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                    return f"OpenAI服务暂时不可用: {error_summary}"
                
        finally:
            # 提示垃圾回收器运行（可选，但有助于清理大对象）
            gc.collect()
            
    def _get_deepseek_response(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理DeepSeek API请求并返回响应内容。
        
        该方法直接调用DeepSeek API，发送请求并处理响应。
        
        Args:
            model_name: 模型名称
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            
        Returns:
            str: AI响应内容，发生错误时返回友好提示信息
        """
        logger.info(f"调用DeepSeek API - 模型: {model_name}")
        
        # 验证API密钥
        if not self.deepseek_api_key:
            logger.error("DeepSeek API密钥未配置")
            return "抱歉，无法连接到DeepSeek服务，请检查API密钥配置。"
        
        # 使用上下文管理器管理会话资源
        with requests.Session() as session:
            # 创建带增强重试机制的会话
            retry = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"]
            )
            adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
            session.mount('https://', adapter)
            
            try:
                # DeepSeek API的基础URL
                deepseek_base_url = "https://api.deepseek.com/v1"
                endpoint = f"{deepseek_base_url}/chat/completions"
                
                # 请求头部
                headers = {
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                }
                
                # 请求参数
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": 4096  # 设置最大token数
                }
                
                # 发送请求
                logger.debug(f"向DeepSeek发送请求 - URL: {endpoint}, 数据大小: {len(str(payload))} 字符")
                response = session.post(endpoint, headers=headers, json=payload, timeout=300)
                response.raise_for_status()  # 抛出HTTP错误
                
                # 解析响应
                response_data = response.json()
                
                # 使用专门的解析函数处理DeepSeek响应
                content = self._parse_deepseek_response(response_data)
                logger.info(f"成功获取DeepSeek响应 - 内容长度: {len(content)} 字符")
                return content
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"DeepSeek API HTTP错误: {e}")
                error_str = str(e).lower()
                
                # 尝试解析错误响应
                error_msg = None
                if e.response:
                    try:
                        if (error_data := e.response.json()) and (error_info := error_data.get("error")):
                            error_msg = error_info.get("message", "")
                            logger.error(f"DeepSeek API错误消息: {error_msg}")
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                # 根据错误类型返回不同的提示信息
                match True:
                    case _ if "invalid_api_key" in error_str or "authentication" in error_str:
                        return "DeepSeek API密钥无效，请检查您的密钥配置。"
                    case _ if "insufficient_quota" in error_str or "billing" in error_str:
                        return "DeepSeek API额度不足，请检查您的账户状态。"
                    case _ if "model_not_found" in error_str or "model is not available" in error_str:
                        return f"找不到DeepSeek模型: {model_name}，请使用有效的模型名称。"
                    case _:
                        return f"DeepSeek服务错误: {error_msg[:100] if error_msg else str(e)[:100]}..."
                
            except requests.exceptions.ConnectionError:
                logger.error("DeepSeek连接错误")
                return "无法连接到DeepSeek服务器，请检查网络连接。"
                
            except requests.exceptions.Timeout:
                logger.error("DeepSeek请求超时")
                return "请求超时，请稍后再试。"
                
            except json.JSONDecodeError:
                logger.error("DeepSeek响应JSON解析错误")
                return "无法解析服务器响应，请稍后再试。"
                
            except Exception as e:
                logger.error(f"DeepSeek API未知错误: {e}")
                return "抱歉，处理您的请求时发生了未知错误。"
        
        # 会话会在with块结束后自动关闭，无需手动清理


def main():
    """主函数，处理命令行参数并启动相应功能"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='AI聊天程序')
    
    # 添加GUI参数
    parser.add_argument('--gui', action='store_true', help='启动图形用户界面')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果指定了--gui参数，则启动GUI
    if args.gui:
        # 导入并启动GUI
        try:
            # 导入chat_gui模块中的main函数
            from chat_gui import main as gui_main
            # 调用GUI的main函数启动界面
            gui_main()
        except ImportError as e:
            logger.error(f"导入GUI模块失败: {e}")
        except Exception as e:
            logger.error(f"启动GUI失败: {e}")
    else:
        # 命令行模式的默认行为
        print("这是命令行模式。使用 --gui 参数启动图形界面。")


if __name__ == "__main__":
    main()