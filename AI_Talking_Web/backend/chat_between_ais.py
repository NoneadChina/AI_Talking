import os
import requests
import json
import logging
from typing import List, Dict, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIChatManager:
    """
    AI聊天管理器类，用于处理与各种AI API的交互
    """
    
    def __init__(self, model1_name: str = "qwen3:14b", model2_name: str = "deepseek-r1:14b", 
                 model1_api: str = "ollama", model2_api: str = "ollama",
                 temperature: float = 0.8, **kwargs):
        """
        初始化AI聊天管理器
        """
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.model1_api = model1_api
        self.model2_api = model2_api
        self.temperature = temperature
        
        # 初始化各API的配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def get_ai_response(self, model_name: str, messages: List[Dict[str, str]], api_type: str = "ollama") -> str:
        """
        获取AI模型的响应
        
        Args:
            model_name: 模型名称
            messages: 消息列表
            api_type: API类型
            
        Returns:
            str: AI模型的响应
        """
        logger.info(f"获取AI响应: 模型={model_name}, API类型={api_type}, 消息数={len(messages)}")
        
        try:
            if api_type == "ollama":
                return self._handle_ollama_request(model_name, messages)
            elif api_type == "openai":
                return self._handle_openai_request(model_name, messages)
            elif api_type == "deepseek":
                return self._handle_deepseek_request(model_name, messages)
            else:
                raise ValueError(f"不支持的API类型: {api_type}")
        except Exception as e:
            logger.error(f"获取AI响应失败: {str(e)}")
            return f"获取AI响应失败: {str(e)}"
            
    def get_ai_stream_response(self, model_name: str, messages: List[Dict[str, str]], api_type: str = "ollama"):
        """
        获取AI模型的流式响应
        
        Args:
            model_name: 模型名称
            messages: 消息列表
            api_type: API类型
            
        Returns:
            Generator[str, None, None]: AI模型的流式响应生成器
        """
        logger.info(f"获取AI流式响应: 模型={model_name}, API类型={api_type}, 消息数={len(messages)}")
        
        try:
            if api_type == "ollama":
                return self._handle_ollama_stream_request(model_name, messages)
            elif api_type == "openai":
                return self._handle_openai_stream_request(model_name, messages)
            elif api_type == "deepseek":
                return self._handle_deepseek_stream_request(model_name, messages)
            else:
                raise ValueError(f"不支持的API类型: {api_type}")
        except Exception as e:
            logger.error(f"获取AI流式响应失败: {str(e)}")
            yield f"获取AI流式响应失败: {str(e)}"
    
    def _handle_ollama_request(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理Ollama API请求
        """
        url = f"{self.ollama_base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("message", {}).get("content", "")
    
    def _handle_openai_request(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理OpenAI API请求
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    def _handle_deepseek_request(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        """
        处理DeepSeek API请求
        """
        if not self.deepseek_api_key:
            raise ValueError("DeepSeek API密钥未配置")
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_api_key}"
        }
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    def _handle_ollama_stream_request(self, model_name: str, messages: List[Dict[str, str]]):
        """
        处理Ollama API流式请求
        """
        url = f"{self.ollama_base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature
            }
        }
        
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        response.raise_for_status()
        
        for chunk in response.iter_lines():
            if chunk:
                chunk_str = chunk.decode('utf-8')
                if chunk_str.strip():
                    try:
                        chunk_data = json.loads(chunk_str)
                        if chunk_data.get('message'):
                            content = chunk_data['message'].get('content', '')
                            if content:
                                yield content
                    except json.JSONDecodeError as e:
                        logger.error(f"解析Ollama流式响应失败: {str(e)}")
                        continue
    
    def _handle_openai_stream_request(self, model_name: str, messages: List[Dict[str, str]]):
        """
        处理OpenAI API流式请求
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True
        }
        
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        response.raise_for_status()
        
        for chunk in response.iter_lines():
            if chunk:
                chunk_str = chunk.decode('utf-8')
                if chunk_str.startswith('data: '):
                    chunk_str = chunk_str[6:]
                    if chunk_str.strip() == '[DONE]':
                        break
                    try:
                        chunk_data = json.loads(chunk_str)
                        if chunk_data.get('choices'):
                            delta = chunk_data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                    except json.JSONDecodeError as e:
                        logger.error(f"解析OpenAI流式响应失败: {str(e)}")
                        continue
    
    def _handle_deepseek_stream_request(self, model_name: str, messages: List[Dict[str, str]]):
        """
        处理DeepSeek API流式请求
        """
        if not self.deepseek_api_key:
            raise ValueError("DeepSeek API密钥未配置")
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_api_key}"
        }
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True
        }
        
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        response.raise_for_status()
        
        for chunk in response.iter_lines():
            if chunk:
                chunk_str = chunk.decode('utf-8')
                if chunk_str.startswith('data: '):
                    chunk_str = chunk_str[6:]
                    if chunk_str.strip() == '[DONE]':
                        break
                    try:
                        chunk_data = json.loads(chunk_str)
                        if chunk_data.get('choices'):
                            delta = chunk_data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                    except json.JSONDecodeError as e:
                        logger.error(f"解析DeepSeek流式响应失败: {str(e)}")
                        continue
    
    def get_ollama_models(self):
        """
        获取Ollama模型列表
        
        Returns:
            list: Ollama模型列表
        """
        logger.info("获取Ollama模型列表")
        
        try:
            url = f"{self.ollama_base_url}/api/tags"
            headers = {"Content-Type": "application/json"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            
            return response_data.get("models", [])
        except Exception as e:
            logger.error(f"获取Ollama模型列表失败: {str(e)}")
            return []
