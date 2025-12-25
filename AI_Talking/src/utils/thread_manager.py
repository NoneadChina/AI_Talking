# -*- coding: utf-8 -*-
"""
线程管理模块，用于处理聊天和辩论的线程管理
"""

import time
import threading
from .logger_config import get_logger
from PyQt5.QtCore import QThread, pyqtSignal

# 获取日志记录器
logger = get_logger(__name__)


class ChatThread(QThread):
    """
    聊天线程类，用于处理聊天消息的发送和接收

    信号:
        update_signal: 更新聊天历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
    """

    update_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        model_name,
        api,
        message,
        messages,
        api_settings_widget,
        stream=False,
        temperature=0.8,
    ):
        """
        初始化聊天线程

        Args:
            model_name: 模型名称
            api: API类型
            message: 当前消息
            messages: 消息历史
            api_settings_widget: API设置组件
            stream: 是否使用流式输出
            temperature: 生成文本的随机性
        """
        super().__init__()
        self.model_name = model_name
        self.api = api
        self.message = message
        self.messages = messages
        self.api_settings_widget = api_settings_widget
        self.stream = stream
        self.temperature = temperature
        self._stop_event = threading.Event()

    def stop(self):
        """
        停止线程
        """
        self._stop_event.set()

    def is_stopped(self):
        """
        检查线程是否已停止

        Returns:
            bool: 线程是否已停止
        """
        return self._stop_event.is_set()

    def _cleanup_resources(self):
        """
        清理线程资源
        """
        logger.info("正在清理聊天线程资源...")
        # 清理消息历史
        self.messages = []
        self.message = ""

    def __del__(self):
        """
        析构函数，确保资源被正确清理
        """
        self._cleanup_resources()

    def run(self):
        """
        线程运行函数，处理聊天消息的发送和接收
        """
        try:
            response = ""

            # 根据API类型选择不同的发送方法
            if self.api == "ollama":
                response = self._send_ollama_message(
                    self.model_name, self.messages, stream=self.stream
                )
            elif self.api == "openai":
                response = self._send_openai_message(
                    self.model_name, self.messages, stream=self.stream
                )
            elif self.api == "deepseek":
                response = self._send_deepseek_message(
                    self.model_name, self.messages, stream=self.stream
                )
            else:
                response = f"不支持的API类型: {self.api}"

            # 发送更新信号
            self.update_signal.emit("AI", response)
            self.status_signal.emit("AI回复完成")

        except Exception as e:
            error_msg = f"聊天失败: {str(e)}"
            logger.error(error_msg)
            self.error_signal.emit(error_msg)
            self.status_signal.emit("聊天失败")

    def _send_ollama_message(self, model_name, messages, stream=False):
        """
        发送消息到Ollama API

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出

        Returns:
            str: AI回复内容
        """
        import requests
        import json

        base_url = self.api_settings_widget.get_ollama_base_url()
        full_response = ""

        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model_name,
                "messages": messages,
                "stream": stream,
                "options": {"temperature": self.temperature},
            },
        )
        response.raise_for_status()

        if stream:
            for line in response.iter_lines(decode_unicode=True):
                if line and not self.is_stopped():
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        content = data["message"]["content"]
                        full_response += content
                        self.update_signal.emit("AI", full_response)
        else:
            data = response.json()
            full_response = data.get("message", {}).get("content", "")

        return full_response

    def _send_openai_message(self, model_name, messages, stream=False):
        """
        发送消息到OpenAI API

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出

        Returns:
            str: AI回复内容
        """
        import requests
        import json

        api_key = self.api_settings_widget.get_openai_api_key()
        full_response = ""

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": messages,
                "stream": stream,
                "temperature": self.temperature,
            },
        )
        response.raise_for_status()

        if stream:
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: ") and not self.is_stopped():
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            content = delta["content"]
                            full_response += content
                            self.update_signal.emit("AI", full_response)
        else:
            data = response.json()
            full_response = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

        return full_response

    def _send_deepseek_message(self, model_name, messages, stream=False):
        """
        发送消息到DeepSeek API

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出

        Returns:
            str: AI回复内容
        """
        import requests
        import json

        api_key = self.api_settings_widget.get_deepseek_api_key()
        full_response = ""

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": messages,
                "stream": stream,
                "temperature": self.temperature,
            },
        )
        response.raise_for_status()

        if stream:
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: ") and not self.is_stopped():
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            content = delta["content"]
                            full_response += content
                            self.update_signal.emit("AI", full_response)
        else:
            data = response.json()
            full_response = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

        return full_response


class SummaryThread(QThread):
    """
    总结线程类，用于处理讨论总结

    信号:
        update_signal: 更新讨论历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
        stream_update_signal: 流式更新信号，参数为(发送者, 内容片段, 模型名称)
        finished_signal: 总结结束信号
    """

    update_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    stream_update_signal = pyqtSignal(str, str, str)
    finished_signal = pyqtSignal()

    def __init__(
        self,
        model_name,
        model_api,
        messages,
        api_settings_widget,
        temperature=0.8,
        config_panel=None,
    ):
        """
        初始化总结线程

        Args:
            model_name: 模型名称
            model_api: 模型API类型
            messages: 消息列表
            api_settings_widget: API设置组件
            temperature: 生成文本的随机性
            config_panel: 配置面板，用于实时获取温度值
        """
        super().__init__()
        self.model_name = model_name
        self.model_api = model_api
        self.messages = messages
        self.api_settings_widget = api_settings_widget
        self.temperature = temperature
        self.config_panel = config_panel
        self._stop_event = threading.Event()

    def stop(self):
        """
        停止线程
        """
        self._stop_event.set()

    def is_stopped(self):
        """
        检查线程是否已停止

        Returns:
            bool: 线程是否已停止
        """
        return self._stop_event.is_set()

    def _cleanup_resources(self):
        """
        清理线程资源
        """
        logger.info("正在清理总结线程资源...")
        # 清理消息列表
        self.messages = []

    def __del__(self):
        """
        析构函数，确保资源被正确清理
        """
        self._cleanup_resources()

    def run(self):
        """
        线程运行函数，处理总结
        """
        try:
            # 确定发送者名称
            sender_name = "专家AI3"  # 默认使用专家AI3

            # 1. 首先检查系统提示词内容，确定是专家AI3还是裁判AI3
            for msg in self.messages:
                if msg["role"] == "system":
                    content = msg["content"]
                    if "辩论裁判AI" in content:
                        sender_name = "裁判AI3"
                        break
                    elif "学术讨论分析师" in content:
                        sender_name = "专家AI3"
                        break

            # 2. 检查系统提示词的来源环境变量，进一步确认
            for msg in self.messages:
                if msg["role"] == "system":
                    content = msg["content"]
                    # 如果包含裁判特定的系统提示词内容，使用裁判AI3
                    if (
                        "评分体系" in content
                        or "胜负裁决标准" in content
                        or "辩论总结" in content
                    ):
                        sender_name = "裁判AI3"
                        break
                    # 如果包含专家特定的系统提示词内容，使用专家AI3
                    elif (
                        "核心论点梳理" in content
                        or "讨论质量评估" in content
                        or "讨论概览" in content
                    ):
                        sender_name = "专家AI3"
                        break

            # 3. 检查用户消息内容，确认功能类型
            for msg in self.messages:
                if msg["role"] == "user":
                    content = msg["content"]
                    if "正方" in content and "反方" in content:
                        # 辩论功能，使用裁判AI3
                        sender_name = "裁判AI3"
                        break
                    elif "学者AI1" in content and "学者AI2" in content:
                        # 讨论功能，使用专家AI3
                        sender_name = "专家AI3"
                        break
            self.status_signal.emit(
                f"{sender_name}开始总结，模型: {self.model_name} (API: {self.model_api})"
            )

            # 发送总结响应
            full_response = ""

            # 实时获取最新温度值
            temperature = self.temperature
            if self.config_panel:
                temperature = self.config_panel.get_temperature()

            # 根据API类型选择不同的发送方法
            if self.model_api == "ollama":
                import requests
                import json

                base_url = self.api_settings_widget.get_ollama_base_url()

                if True:  # stream=True
                    # 使用流式响应
                    response = requests.post(
                        f"{base_url}/api/chat",
                        json={
                            "model": self.model_name,
                            "messages": self.messages,
                            "stream": True,
                            "options": {"temperature": temperature},
                        },
                        stream=True,
                    )
                    response.raise_for_status()

                    for line in response.iter_lines(decode_unicode=True):
                        if line and not self.is_stopped():
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                content = data["message"]["content"]
                                full_response += content
                                # 发送流式更新信号
                                self.stream_update_signal.emit(
                                    sender_name, full_response, self.model_name
                                )
                else:
                    # 使用非流式响应
                    response_data = requests.post(
                        f"{base_url}/api/chat",
                        json={
                            "model": self.model_name,
                            "messages": self.messages,
                            "options": {"temperature": temperature},
                            "stream": False,
                        },
                    )
                    response_data.raise_for_status()
                    data = response_data.json()
                    full_response = data.get("message", {}).get("content", "")
                    # 发送更新信号
                    self.update_signal.emit(sender_name, full_response)
            elif self.model_api == "openai":
                import requests
                import json

                api_key = self.api_settings_widget.get_openai_api_key()

                if True:  # stream=True
                    # 使用流式响应
                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model_name,
                            "messages": self.messages,
                            "temperature": self.temperature,
                            "stream": True,
                        },
                        stream=True,
                    )
                    response.raise_for_status()

                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: ") and not self.is_stopped():
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content = delta["content"]
                                    full_response += content
                                    # 发送流式更新信号
                                    self.stream_update_signal.emit(
                                        sender_name, full_response, self.model_name
                                    )
                else:
                    # 使用非流式响应
                    response_data = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model_name,
                            "messages": self.messages,
                            "temperature": self.temperature,
                            "stream": False,
                        },
                    )
                    response_data.raise_for_status()
                    data = response_data.json()
                    full_response = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    # 发送更新信号
                    self.update_signal.emit(sender_name, full_response)
            elif self.model_api == "deepseek":
                import requests
                import json

                api_key = self.api_settings_widget.get_deepseek_api_key()

                if True:  # stream=True
                    # 使用流式响应
                    response = requests.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model_name,
                            "messages": self.messages,
                            "temperature": temperature,
                            "stream": True,
                        },
                        stream=True,
                    )
                    response.raise_for_status()

                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: ") and not self.is_stopped():
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content = delta["content"]
                                    full_response += content
                                    # 发送流式更新信号
                                    self.stream_update_signal.emit(
                                        sender_name, full_response, self.model_name
                                    )
                else:
                    # 使用非流式响应
                    response_data = requests.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model_name,
                            "messages": self.messages,
                            "temperature": self.temperature,
                            "stream": False,
                        },
                    )
                    response_data.raise_for_status()
                    data = response_data.json()
                    full_response = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    # 发送更新信号
                    self.update_signal.emit(sender_name, full_response)

            # 添加总结完成消息到讨论历史
            self.status_signal.emit("总结完成")
            self.finished_signal.emit()

        except Exception as e:
            error_msg = f"总结失败: {str(e)}"
            logger.error(error_msg)
            self.error_signal.emit(error_msg)
            self.finished_signal.emit()


class DebateThread(QThread):
    """
    辩论线程类，用于处理双AI辩论

    信号:
        update_signal: 更新辩论历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
        stream_update_signal: 流式更新信号，参数为(发送者, 内容片段, 模型名称)
        finished_signal: 辩论结束信号
    """

    update_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    stream_update_signal = pyqtSignal(str, str, str)
    finished_signal = pyqtSignal()

    def __init__(
        self,
        topics,
        model1_name,
        model2_name,
        model3_name=None,
        model1_api="ollama",
        model2_api="ollama",
        model3_api="ollama",
        rounds=3,
        time_limit=600,
        api_settings_widget=None,
        temperature=0.8,
    ):
        """
        辩论线程初始化

        Args:
            topics: 辩论主题列表
            model1_name: 模型1名称
            model2_name: 模型2名称
            model3_name: 模型3名称（裁判AI）
            model1_api: 模型1 API类型（如ollama、openai、deepseek）
            model2_api: 模型2 API类型
            model3_api: 模型3 API类型
            rounds: 辩论轮数
            time_limit: 时间限制（秒）
            api_settings_widget: API设置组件，用于获取API配置
            temperature: 生成文本的随机性，默认为0.8
        """
        super().__init__()
        self.topics = topics
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.model3_name = model3_name
        self.model1_api = model1_api
        self.model2_api = model2_api
        self.model3_api = model3_api
        self.rounds = rounds
        self.time_limit = time_limit
        self.api_settings_widget = api_settings_widget
        self.temperature = temperature
        self._stop_event = threading.Event()
        self.debate_history_messages = []
        self.start_time = None

    def stop(self):
        """
        停止线程
        """
        self._stop_event.set()

    def is_stopped(self):
        """
        检查线程是否已停止

        Returns:
            bool: 线程是否已停止
        """
        return self._stop_event.is_set()

    def get_debate_history(self):
        """
        获取辩论历史

        Returns:
            list: 辩论历史列表
        """
        return self.debate_history_messages

    def _cleanup_resources(self):
        """
        清理线程资源
        """
        logger.info("正在清理辩论线程资源...")
        # 清理辩论历史消息
        self.debate_history_messages = []

    def __del__(self):
        """
        析构函数，确保资源被正确清理
        """
        self._cleanup_resources()

    def run(self):
        """
        线程运行函数，处理双AI辩论
        """
        self.start_time = time.time()

        try:
            # 获取辩论系统提示词（从环境变量读取，确保使用最新的设置）
            import os

            debate_common_prompt = os.getenv("DEBATE_SYSTEM_PROMPT", "").strip()
            debate_ai1_prompt = os.getenv("DEBATE_AI1_SYSTEM_PROMPT", "").strip()
            debate_ai2_prompt = os.getenv("DEBATE_AI2_SYSTEM_PROMPT", "").strip()

            # 初始化辩论历史
            self.debate_history_messages = []

            # 开始辩论
            for i, topic in enumerate(self.topics):
                if self.is_stopped():
                    break

                # 检查时间限制
                if (
                    self.time_limit > 0
                    and (time.time() - self.start_time) > self.time_limit
                ):
                    self.status_signal.emit("辩论已超时")
                    break

                # 发送主题
                # self.update_signal.emit("系统", f"=== 辩论主题: {topic} ===")
                # 将主题添加到辩论历史
                self.debate_history_messages.append(
                    {"role": "system", "content": f"辩论主题: {topic}"}
                )

                # 进行辩论轮次
                for round_num in range(1, self.rounds + 1):
                    if self.is_stopped():
                        break

                    self.update_signal.emit("系统", f"=== 第 {round_num} 轮辩论 ===")
                    # 将轮次信息添加到辩论历史
                    self.debate_history_messages.append(
                        {"role": "system", "content": f"第 {round_num} 轮辩论"}
                    )

                    # 正方发言
                    self.status_signal.emit(f"正方{self.model1_name}正在发言...")
                    model1_response = self._send_debate_message(
                        self.model1_name,
                        self.model1_api,
                        debate_common_prompt,
                        debate_ai1_prompt,
                        topic,
                        self.temperature,
                        previous_response="",
                        stream=True,
                        sender_prefix="正方",
                    )
                    if self.is_stopped():
                        break

                    # 将正方发言添加到辩论历史
                    self.debate_history_messages.append(
                        {"role": f"正方{self.model1_name}", "content": model1_response}
                    )

                    if self.is_stopped():
                        break

                    # 反方发言
                    self.status_signal.emit(f"反方{self.model2_name}正在发言...")
                    model2_response = self._send_debate_message(
                        self.model2_name,
                        self.model2_api,
                        debate_common_prompt,
                        debate_ai2_prompt,
                        topic,
                        self.temperature,
                        previous_response=model1_response,
                        stream=True,
                        sender_prefix="反方",
                    )
                    if self.is_stopped():
                        break

                    # 将反方发言添加到辩论历史
                    self.debate_history_messages.append(
                        {"role": f"反方{self.model2_name}", "content": model2_response}
                    )

                    if self.is_stopped():
                        break

            total_time = time.time() - self.start_time
            self.status_signal.emit(f"辩论结束，总耗时: {total_time:.2f} 秒")
            # 添加辩论结束消息到辩论历史
            self.update_signal.emit("系统", "辩论结束")
            self.debate_history_messages.append(
                {"role": "system", "content": "辩论结束"}
            )
            self.finished_signal.emit()

        except Exception as e:
            error_msg = f"辩论失败: {str(e)}"
            logger.error(error_msg)
            self.error_signal.emit(error_msg)
            self.finished_signal.emit()

    def _send_debate_message(
        self,
        model_name,
        api,
        debate_common_prompt,
        debate_ai_prompt,
        topic,
        temperature,
        previous_response="",
        stream=False,
        sender_prefix="正方",
    ):
        """
        发送辩论消息到AI

        Args:
            model_name: 模型名称
            api: API类型
            debate_common_prompt: 辩论共享系统提示词
            debate_ai_prompt: 特定AI系统提示词
            topic: 辩论主题
            temperature: 生成文本的随机性
            previous_response: 前一个回应
            stream: 是否使用流式输出
            sender_prefix: 发送者前缀，用于区分正方和反方

        Returns:
            str: AI回复内容
        """
        # 合并系统提示词
        full_system_prompt = debate_common_prompt
        if debate_ai_prompt:
            full_system_prompt += "\n" + debate_ai_prompt

        # 构建辩论消息
        message = f"辩论主题: {topic}\n"
        if previous_response:
            message += f"对方观点: {previous_response}\n"
        message += "请根据你的立场进行辩论，逻辑清晰，论点明确。"

        # 构建消息历史
        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": message},
        ]

        # 根据API类型选择不同的发送方法
        response = ""
        try:
            if api == "ollama":
                response = self._send_ollama_message(
                    model_name, messages, stream=stream, sender_prefix=sender_prefix
                )
            elif api == "openai":
                response = self._send_openai_message(
                    model_name, messages, stream=stream, sender_prefix=sender_prefix
                )
            elif api == "deepseek":
                response = self._send_deepseek_message(
                    model_name, messages, stream=stream, sender_prefix=sender_prefix
                )
            else:
                response = f"不支持的API类型: {api}"
        except Exception as e:
            logger.error(f"发送辩论消息失败: {str(e)}")
            response = f"抱歉，我暂时无法提供观点。错误: {str(e)}"

        return response

    def _send_ollama_message(
        self, model_name, messages, stream=False, sender_prefix="正方"
    ):
        """
        发送消息到Ollama API，支持流式输出

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出
            sender_prefix: 发送者前缀，用于区分正方和反方

        Returns:
            str: AI回复内容
        """
        base_url = self.api_settings_widget.get_ollama_base_url()
        import requests
        import json

        full_response = ""

        if stream:
            # 使用流式响应
            response = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": True,
                },
                stream=True,
            )
            response.raise_for_status()

            # 处理流式响应
            for chunk in response.iter_lines(decode_unicode=True):
                if self.is_stopped():
                    break

                if chunk:
                    try:
                        chunk_data = json.loads(chunk)
                        if (
                            "message" in chunk_data
                            and "content" in chunk_data["message"]
                        ):
                            content = chunk_data["message"]["content"]
                            if content:
                                full_response += content
                                # 发送流式更新信号
                                self.stream_update_signal.emit(
                                    f"{sender_prefix}{model_name}",
                                    full_response,
                                    model_name,
                                )
                    except json.JSONDecodeError as e:
                        logger.error(f"解析Ollama流式响应失败: {str(e)}")
        else:
            # 使用非流式响应
            response_data = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": False,
                },
            )
            response_data.raise_for_status()
            data = response_data.json()
            full_response = data.get("message", {}).get("content", "")

        return full_response

    def _send_openai_message(
        self, model_name, messages, stream=False, sender_prefix="正方"
    ):
        """
        发送消息到OpenAI API，支持流式输出

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出
            sender_prefix: 发送者前缀，用于区分正方和反方

        Returns:
            str: AI回复内容
        """
        api_key = self.api_settings_widget.get_openai_api_key()
        import requests
        import json

        full_response = ""

        if stream:
            # 使用流式响应
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": True,
                },
                stream=True,
            )
            response.raise_for_status()

            # 处理流式响应
            for chunk in response.iter_lines(decode_unicode=True):
                if self.is_stopped():
                    break

                if chunk and chunk.startswith("data: "):
                    try:
                        chunk_data = json.loads(chunk[6:])
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                content = delta["content"]
                                full_response += content
                                # 发送流式更新信号
                                self.stream_update_signal.emit(
                                    f"{sender_prefix}{model_name}",
                                    full_response,
                                    model_name,
                                )
                    except json.JSONDecodeError as e:
                        logger.error(f"解析OpenAI流式响应失败: {str(e)}")
        else:
            # 使用非流式响应
            response_data = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": False,
                },
            )
            response_data.raise_for_status()
            data = response_data.json()
            full_response = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

        return full_response

    def _send_deepseek_message(
        self, model_name, messages, stream=False, sender_prefix="正方"
    ):
        """
        发送消息到DeepSeek API，支持流式输出

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出
            sender_prefix: 发送者前缀，用于区分正方和反方

        Returns:
            str: AI回复内容
        """
        api_key = self.api_settings_widget.get_deepseek_api_key()
        import requests
        import json

        full_response = ""

        if stream:
            # 使用流式响应
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": True,
                },
                stream=True,
            )
            response.raise_for_status()

            # 处理流式响应
            for chunk in response.iter_lines(decode_unicode=True):
                if self.is_stopped():
                    break

                if chunk and chunk.startswith("data: "):
                    try:
                        chunk_data = json.loads(chunk[6:])
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                content = delta["content"]
                                full_response += content
                                # 发送流式更新信号
                                self.stream_update_signal.emit(
                                    f"{sender_prefix}{model_name}",
                                    full_response,
                                    model_name,
                                )
                    except json.JSONDecodeError as e:
                        logger.error(f"解析DeepSeek流式响应失败: {str(e)}")
        else:
            # 使用非流式响应
            response_data = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": False,
                },
            )
            response_data.raise_for_status()
            data = response_data.json()
            full_response = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

        return full_response


class DiscussionThread(QThread):
    """
    讨论线程类，用于处理双AI讨论

    信号:
        update_signal: 更新讨论历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
        stream_update_signal: 流式更新信号，参数为(发送者, 内容片段, 模型名称)
        finished_signal: 讨论结束信号
    """

    update_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    stream_update_signal = pyqtSignal(str, str, str)
    finished_signal = pyqtSignal()

    def __init__(
        self,
        topic,
        model1_name,
        model2_name,
        model3_name=None,
        model1_api="ollama",
        model2_api="ollama",
        model3_api="ollama",
        rounds=3,
        time_limit=600,
        api_settings_widget=None,
        temperature=0.8,
        config_panel=None,
    ):
        """
        初始化讨论线程

        Args:
            topic: 讨论主题
            model1_name: 模型1名称
            model2_name: 模型2名称
            model3_name: 模型3名称（专家AI）
            model1_api: 模型1 API类型
            model2_api: 模型2 API类型
            model3_api: 模型3 API类型
            rounds: 讨论轮数
            time_limit: 时间限制（秒）
            api_settings_widget: API设置组件
            temperature: 生成文本的随机性
            config_panel: 配置面板，用于实时获取温度值
        """
        super().__init__()
        self.topic = topic
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.model1_api = model1_api
        self.model2_api = model2_api
        self.model3_name = model3_name
        self.model3_api = model3_api
        self.rounds = rounds
        self.time_limit = time_limit
        self.api_settings_widget = api_settings_widget
        self.temperature = temperature
        self.config_panel = config_panel
        self._stop_event = threading.Event()

        # 讨论历史存储
        self.discussion_history = []

        # 时间管理
        self.start_time = None

    def stop(self):
        """
        停止线程
        """
        self._stop_event.set()

    def is_stopped(self):
        """
        检查线程是否已停止

        Returns:
            bool: 线程是否已停止
        """
        return self._stop_event.is_set()

    def get_discussion_history(self):
        """
        获取讨论历史

        Returns:
            list: 讨论历史列表
        """
        return self.discussion_history

    def _cleanup_resources(self):
        """
        清理线程资源
        """
        logger.info("正在清理讨论线程资源...")
        # 清理讨论历史消息
        self.discussion_history = []

    def __del__(self):
        """
        析构函数，确保资源被正确清理
        """
        self._cleanup_resources()

    def run(self):
        """
        线程运行函数，处理双AI讨论
        """
        self.start_time = time.time()

        try:
            # 获取讨论系统提示词（从环境变量读取，确保使用最新的设置）
            import os

            discussion_common_prompt = os.getenv("DISCUSSION_SYSTEM_PROMPT", "").strip()
            discussion_ai1_prompt = os.getenv(
                "DISCUSSION_AI1_SYSTEM_PROMPT", ""
            ).strip()
            discussion_ai2_prompt = os.getenv(
                "DISCUSSION_AI2_SYSTEM_PROMPT", ""
            ).strip()

            # 初始化讨论历史
            self.discussion_history = []
            # 添加系统提示词到讨论历史
            self.discussion_history.append(
                {"role": "system", "content": discussion_common_prompt}
            )

            # 开始讨论
            self.status_signal.emit(f"两个AI开始围绕主题 '{self.topic}' 进行讨论")
            self.status_signal.emit(
                f"学者AI1: {self.model1_name} (API: {self.model1_api})"
            )
            self.status_signal.emit(
                f"学者AI2: {self.model2_name} (API: {self.model2_api})"
            )
            self.status_signal.emit(f"讨论轮数: {self.rounds} 轮")

            if self.time_limit > 0:
                self.status_signal.emit(f"时间限制: {self.time_limit} 秒")

            # AI1的初始消息
            ai1_initial_message = f"主题：{self.topic}。请提供你的见解和观点。"

            # 讨论轮次循环，执行指定轮数的讨论
            for round_num in range(1, self.rounds + 1):
                # 检查是否需要停止线程
                if self.is_stopped():
                    logger.info(f"讨论线程已停止，当前轮次: {round_num}")
                    break

                # 检查时间限制
                if (
                    self.time_limit > 0
                    and (time.time() - self.start_time) > self.time_limit
                ):
                    self.status_signal.emit("讨论已超时")
                    logger.info(f"讨论已超时，当前轮次: {round_num}")
                    break

                # 更新状态信号，显示当前轮次
                self.status_signal.emit(
                    f"----- 第 {round_num}/{self.rounds} 轮开始 -----"
                )

                # 发送系统提示，显示当前轮次
                self.update_signal.emit("系统", f"=== 第 {round_num} 轮讨论 ===")

                # ============================ AI1发言阶段 ============================
                # 更新状态，显示AI1正在发言
                self.status_signal.emit(f"学者AI1 {self.model1_name} 正在发言...")

                # 构建AI1的系统提示词，合并公共提示词和AI1专用提示词
                ai1_system_prompt = discussion_common_prompt
                if discussion_ai1_prompt:
                    ai1_system_prompt += "\n" + discussion_ai1_prompt

                # 构建AI1的上下文，包含主题和之前的讨论内容
                ai1_context = f"主题：{self.topic}。\n\n"
                if self.discussion_history:
                    # 添加之前的讨论内容，跳过系统提示词
                    for i, msg in enumerate(self.discussion_history[1:]):
                        speaker = "AI1" if i % 2 == 0 else "AI2"
                        ai1_context += f"{speaker}：{msg['content']}\n\n"
                # 添加AI1的任务指令
                ai1_context += "请继续提供你的观点和分析。"

                # 构建完整的AI1消息历史
                ai1_messages = [
                    {"role": "system", "content": ai1_system_prompt},
                    {"role": "user", "content": ai1_context},
                ]

                # 调用AI1获取响应，使用流式输出
                ai1_response = self._get_ai_response(
                    self.model1_name,
                    self.model1_api,
                    ai1_messages,
                    stream=True,
                    sender_prefix="学者AI1",
                )

                # 检查是否需要停止线程
                if self.is_stopped():
                    logger.info(f"讨论线程已停止，AI1发言中断")
                    break

                # 将AI1的响应添加到讨论历史，使用"AI1"角色标识
                self.discussion_history.append({"role": "AI1", "content": ai1_response})
                logger.info(f"AI1发言完成，轮次: {round_num}")

                # ============================ AI2发言阶段 ============================
                # 更新状态，显示AI2正在发言
                self.status_signal.emit(f"学者AI2 {self.model2_name} 正在回应...")

                # 构建AI2的系统提示词，合并公共提示词和AI2专用提示词
                ai2_system_prompt = discussion_common_prompt
                if discussion_ai2_prompt:
                    ai2_system_prompt += "\n" + discussion_ai2_prompt

                # 构建AI2的上下文，包含主题和所有讨论内容（包括本轮AI1的发言）
                ai2_context = f"主题：{self.topic}。\n\n"
                for i, msg in enumerate(self.discussion_history[1:]):  # 跳过系统提示词
                    speaker = "AI1" if i % 2 == 0 else "AI2"
                    ai2_context += f"{speaker}：{msg['content']}\n\n"
                # 添加AI2的任务指令
                ai2_context += "请继续提供你的观点和分析。"

                # 构建完整的AI2消息历史
                ai2_messages = [
                    {"role": "system", "content": ai2_system_prompt},
                    {"role": "user", "content": ai2_context},
                ]

                # 调用AI2获取响应，使用流式输出
                ai2_response = self._get_ai_response(
                    self.model2_name,
                    self.model2_api,
                    ai2_messages,
                    stream=True,
                    sender_prefix="学者AI2",
                )

                # 检查是否需要停止线程
                if self.is_stopped():
                    logger.info(f"讨论线程已停止，AI2发言中断")
                    break

                # 将AI2的响应添加到讨论历史，使用"AI2"角色标识
                self.discussion_history.append({"role": "AI2", "content": ai2_response})
                logger.info(f"AI2发言完成，轮次: {round_num}")

                # ============================ 本轮讨论结束 ============================

            total_time = time.time() - self.start_time
            self.status_signal.emit(f"讨论结束，总耗时: {total_time:.2f} 秒")
            # 添加讨论结束消息到讨论历史
            self.update_signal.emit("系统", "讨论结束")
            self.finished_signal.emit()

        except Exception as e:
            error_msg = f"讨论失败: {str(e)}"
            logger.error(error_msg)
            self.error_signal.emit(error_msg)
            self.finished_signal.emit()

    def _get_ai_response(
        self, model_name, api, messages, stream=False, sender_prefix="学者AI1"
    ):
        """
        获取AI模型的响应，支持流式输出

        Args:
            model_name: 模型名称
            api: API类型
            messages: 消息历史
            stream: 是否使用流式输出
            sender_prefix: 发送者前缀，用于区分AI1和AI2

        Returns:
            str: AI回复内容
        """
        response = ""
        try:
            # 实时获取最新温度值
            current_temperature = self.temperature
            if self.config_panel:
                current_temperature = self.config_panel.get_temperature()

            # 根据API类型选择不同的发送方法
            if api == "ollama":
                response = self._send_ollama_message(
                    model_name,
                    messages,
                    stream=stream,
                    sender_prefix=sender_prefix,
                    temperature=current_temperature,
                )
            elif api == "openai":
                response = self._send_openai_message(
                    model_name,
                    messages,
                    stream=stream,
                    sender_prefix=sender_prefix,
                    temperature=current_temperature,
                )
            elif api == "deepseek":
                response = self._send_deepseek_message(
                    model_name,
                    messages,
                    stream=stream,
                    sender_prefix=sender_prefix,
                    temperature=current_temperature,
                )
            else:
                response = f"不支持的API类型: {api}"
        except Exception as e:
            logger.error(f"获取AI响应失败: {str(e)}")
            response = f"抱歉，我暂时无法提供观点。错误: {str(e)}"

        return response

    def _send_ollama_message(
        self,
        model_name,
        messages,
        stream=False,
        sender_prefix="学者AI1",
        temperature=None,
    ):
        """
        发送消息到Ollama API，支持流式输出

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出
            sender_prefix: 发送者前缀，用于区分AI1和AI2
            temperature: 生成文本的随机性

        Returns:
            str: AI回复内容
        """
        base_url = self.api_settings_widget.get_ollama_base_url()
        import requests
        import json

        full_response = ""

        # 使用传入的温度值，如果没有则使用默认值
        if temperature is None:
            temperature = self.temperature
            if self.config_panel:
                temperature = self.config_panel.get_temperature()

        if stream:
            # 使用流式响应
            response = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True,
                },
                stream=True,
            )
            response.raise_for_status()

            # 处理流式响应
            for chunk in response.iter_lines(decode_unicode=True):
                if self.is_stopped():
                    break

                if chunk:
                    try:
                        chunk_data = json.loads(chunk)
                        if (
                            "message" in chunk_data
                            and "content" in chunk_data["message"]
                        ):
                            content = chunk_data["message"]["content"]
                            if content:
                                full_response += content
                                # 发送流式更新信号
                                self.stream_update_signal.emit(
                                    f"{sender_prefix} {model_name}",
                                    full_response,
                                    model_name,
                                )
                    except json.JSONDecodeError as e:
                        logger.error(f"解析Ollama流式响应失败: {str(e)}")
        else:
            # 使用非流式响应
            response_data = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response_data.raise_for_status()
            data = response_data.json()
            full_response = data.get("message", {}).get("content", "")

        return full_response

    def _send_openai_message(
        self,
        model_name,
        messages,
        stream=False,
        sender_prefix="学者AI1",
        temperature=None,
    ):
        """
        发送消息到OpenAI API，支持流式输出

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出
            sender_prefix: 发送者前缀，用于区分AI1和AI2
            temperature: 生成文本的随机性

        Returns:
            str: AI回复内容
        """
        api_key = self.api_settings_widget.get_openai_api_key()
        import requests
        import json

        # 使用传入的温度值，如果没有则使用默认值
        if temperature is None:
            temperature = self.temperature
            if self.config_panel:
                temperature = self.config_panel.get_temperature()

        full_response = ""

        if stream:
            # 使用流式响应
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True,
                },
                stream=True,
            )
            response.raise_for_status()

            # 处理流式响应
            for chunk in response.iter_lines(decode_unicode=True):
                if self.is_stopped():
                    break

                if chunk and chunk.startswith("data: "):
                    try:
                        chunk_data = json.loads(chunk[6:])
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                content = delta["content"]
                                full_response += content
                                # 发送流式更新信号
                                self.stream_update_signal.emit(
                                    f"{sender_prefix} {model_name}",
                                    full_response,
                                    model_name,
                                )
                    except json.JSONDecodeError as e:
                        logger.error(f"解析OpenAI流式响应失败: {str(e)}")
        else:
            # 使用非流式响应
            response_data = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response_data.raise_for_status()
            data = response_data.json()
            full_response = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

        return full_response

    def _send_deepseek_message(
        self,
        model_name,
        messages,
        stream=False,
        sender_prefix="学者AI1",
        temperature=None,
    ):
        """
        发送消息到DeepSeek API，支持流式输出

        Args:
            model_name: 模型名称
            messages: 消息历史
            stream: 是否使用流式输出
            sender_prefix: 发送者前缀，用于区分AI1和AI2
            temperature: 生成文本的随机性

        Returns:
            str: AI回复内容
        """
        api_key = self.api_settings_widget.get_deepseek_api_key()
        import requests
        import json

        # 使用传入的温度值，如果没有则使用默认值
        if temperature is None:
            temperature = self.temperature
            if self.config_panel:
                temperature = self.config_panel.get_temperature()

        full_response = ""

        if stream:
            # 使用流式响应
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True,
                },
                stream=True,
            )
            response.raise_for_status()

            # 处理流式响应
            for chunk in response.iter_lines(decode_unicode=True):
                if self.is_stopped():
                    break

                if chunk and chunk.startswith("data: "):
                    try:
                        chunk_data = json.loads(chunk[6:])
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                content = delta["content"]
                                full_response += content
                                # 发送流式更新信号
                                self.stream_update_signal.emit(
                                    f"{sender_prefix} {model_name}",
                                    full_response,
                                    model_name,
                                )
                    except json.JSONDecodeError as e:
                        logger.error(f"解析DeepSeek流式响应失败: {str(e)}")
        else:
            # 使用非流式响应
            response_data = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response_data.raise_for_status()
            data = response_data.json()
            full_response = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

        return full_response
