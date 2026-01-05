# -*- coding: utf-8 -*-
"""
线程管理模块，用于处理聊天和辩论的线程管理
"""

import time
import threading
import requests
from .logger_config import get_logger
from .config_manager import config_manager
from .i18n_manager import i18n
from PyQt5.QtCore import QThread, pyqtSignal

# 获取日志记录器
logger = get_logger(__name__)


class BaseAITaskThread(QThread):
    """
    AI任务基础线程类，包含通用的线程管理、资源清理和AI服务创建逻辑

    信号:
        update_signal: 更新历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
        stream_update_signal: 流式更新信号，参数为(发送者, 内容片段, 模型名称)
        finished_signal: 任务结束信号
    """

    update_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    stream_update_signal = pyqtSignal(str, str, str)
    finished_signal = pyqtSignal()

    def __init__(self, api_settings_widget=None, temperature=0.8):
        """
        初始化基础线程

        Args:
            api_settings_widget: API设置组件
            temperature: 生成文本的随机性
        """
        super().__init__()
        self.api_settings_widget = api_settings_widget
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

    def _create_ai_service(self, api_type, model_name=None):
        """
        创建AI服务实例

        该方法根据API类型创建对应的AI服务实例，支持多种AI服务提供商
        严格按照用户选择的API类型来决定使用哪个服务，不受模型名称影响

        Args:
            api_type: API类型，可选值："ollama", "openai", "deepseek", "ollama_cloud"
            model_name: 模型名称，可选，仅用于日志记录，不影响服务选择

        Returns:
            AIServiceInterface: AI服务实例，实现了统一的AI服务接口

        Raises:
            ValueError: 当提供了不支持的API类型时抛出
        """
        from src.utils.ai_service import AIServiceFactory

        # 检查API设置组件是否可用
        if not self.api_settings_widget:
            raise ValueError("API 设置组件未初始化")

        # 严格按照用户选择的API类型来决定使用哪个服务
        # 不管模型名称是什么，只要用户选择了Ollama，就使用Ollama服务
        # 不管模型名称是什么，只要用户选择了Ollama Cloud，就使用Ollama Cloud服务
        if api_type == "ollama" or api_type == "Ollama":
            try:
                base_url = self.api_settings_widget.get_ollama_base_url()
                logger.info(f"使用Ollama服务，模型: {model_name}，基础URL: {base_url}")
                return AIServiceFactory.create_ai_service(
                    "ollama", base_url=base_url
                )
            except AttributeError as e:
                raise ValueError(f"获取Ollama基础URL失败: {str(e)}")
        elif api_type == "openai" or api_type == "OpenAI":
            try:
                api_key = self.api_settings_widget.get_openai_api_key()
                return AIServiceFactory.create_ai_service(
                    "openai", api_key=api_key
                )
            except AttributeError as e:
                raise ValueError(f"获取OpenAI API密钥失败: {str(e)}")
        elif api_type == "deepseek" or api_type == "DeepSeek":
            try:
                api_key = self.api_settings_widget.get_deepseek_api_key()
                return AIServiceFactory.create_ai_service(
                    "deepseek", api_key=api_key
                )
            except AttributeError as e:
                raise ValueError(f"获取DeepSeek API密钥失败: {str(e)}")
        elif api_type == "ollama_cloud" or api_type == "Ollama Cloud":
            try:
                api_key = self.api_settings_widget.get_ollama_cloud_api_key()
                # 检查API密钥是否已设置
                if not api_key:
                    logger.warning("Ollama Cloud API 密钥未设置，尝试使用空密钥调用")
                base_url = self.api_settings_widget.get_ollama_cloud_base_url()
                logger.info(f"使用Ollama Cloud服务，模型: {model_name}，基础URL: {base_url}")
                return AIServiceFactory.create_ai_service(
                    "ollama_cloud", 
                    api_key=api_key,
                    base_url=base_url
                )
            except AttributeError as e:
                raise ValueError(f"获取Ollama Cloud设置失败: {str(e)}")
        else:
            raise ValueError(f"不支持的API类型: {api_type}")

    def _cleanup_resources(self):
        """
        清理线程资源
        """
        logger.info(f"正在清理{self.__class__.__name__}线程资源...")

    def _handle_error(self, error: Exception, error_context: str = ""):
        """
        统一处理线程中的错误

        Args:
            error: 捕获到的异常
            error_context: 错误上下文信息
        """
        error_type = type(error).__name__

        # 构建错误信息
        if error_context:
            error_msg = f"{error_context} 错误: {error_type} - {str(error)}"
        else:
            error_msg = f"{error_type} - {str(error)}"

        # 根据错误类型提供更友好的提示
        user_friendly_msg = self._get_user_friendly_error_msg(error, error_context)
        
        # 替换特定错误信息为更友好的提示
        if "QMetaObject.invokeMethod() call failed" in user_friendly_msg:
            user_friendly_msg = f"{error_context} 错误: Ollama Cloud API 认证失败：无效的 API 密钥"

        # 记录错误日志
        logger.error(f"[{self.__class__.__name__}] {error_msg}")

        # 发送错误信号
        self.error_signal.emit(user_friendly_msg)

        # 更新状态
        self.status_signal.emit(f"{error_context} 失败")

    def _get_user_friendly_error_msg(
        self, error: Exception, error_context: str = ""
    ) -> str:
        """
        获取用户友好的错误提示信息

        Args:
            error: 捕获到的异常
            error_context: 错误上下文信息

        Returns:
            str: 用户友好的错误提示
        """
        error_type = type(error).__name__

        # 根据不同的错误类型提供不同的提示
        if isinstance(error, ConnectionError):
            return f"网络连接错误: {str(error)}\n请检查网络连接或服务是否正常运行"
        elif isinstance(error, TimeoutError):
            return f"请求超时: {str(error)}\n请检查网络连接或稍后重试"
        elif isinstance(error, ValueError):
            return f"参数错误: {str(error)}\n请检查输入参数或配置"
        elif isinstance(error, RuntimeError):
            return f"运行时错误: {str(error)}\n请稍后重试或检查服务状态"
        elif isinstance(error, requests.exceptions.HTTPError):
            if hasattr(error, "response") and error.response.status_code == 401:
                return f"认证失败: {str(error)}\n请检查 API 密钥是否正确"
            elif hasattr(error, "response") and error.response.status_code == 429:
                return f"请求过于频繁: {str(error)}\n请稍后重试"
            elif hasattr(error, "response") and error.response.status_code == 503:
                return f"服务不可用: {str(error)}\n请稍后重试"
            else:
                return f"服务请求错误: {str(error)}\n请检查配置或稍后重试"
        else:
            return f"未知错误: {str(error)}\n请检查日志获取详细信息"

    def __del__(self):
        """
        析构函数，确保资源被正确清理
        """
        self._cleanup_resources()


class ChatThread(BaseAITaskThread):
    """
    聊天线程类，用于处理聊天消息的发送和接收

    信号:
        update_signal: 更新聊天历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
    """

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
        super().__init__(
            api_settings_widget=api_settings_widget, temperature=temperature
        )
        self.model_name = model_name
        self.api = api
        self.message = message
        self.messages = messages
        self.stream = stream

    def _cleanup_resources(self):
        """
        清理线程资源
        """
        super()._cleanup_resources()
        # 清理消息历史
        self.messages = []
        self.message = ""

    def run(self):
        """
        线程运行函数，处理聊天消息的发送和接收

        该方法是聊天线程的核心执行逻辑，负责：
        1. 创建AI服务实例
        2. 根据配置发送聊天请求（支持流式和非流式响应）
        3. 处理响应并发送信号更新UI
        4. 处理可能出现的异常

        信号输出：
        - update_signal: 用于更新聊天历史，参数为(发送者, 内容)
        - status_signal: 用于更新状态信息
        - error_signal: 用于报告错误信息
        """
        try:
            full_response = ""  # 存储完整响应

            # 根据API类型创建相应的AI服务实例
            ai_service = None
            try:
                ai_service = self._create_ai_service(self.api, self.model_name)
            except ValueError as e:
                # 处理不支持的API类型错误
                error_msg = f"不支持的API类型: {self.api}"
                self.update_signal.emit("AI", error_msg)
                self.status_signal.emit("AI回复完成")
                return

            # 使用统一接口发送请求，支持流式和非流式响应
            if self.stream:
                # 处理流式响应
                response_generator = ai_service.chat_completion(
                    self.messages,
                    self.model_name,
                    temperature=self.temperature,
                    stream=True,
                )

                # 逐块处理流式响应
                for chunk in response_generator:
                    if self.is_stopped():
                        break  # 检查线程是否被停止
                    full_response = chunk  # 更新完整响应
                    self.update_signal.emit("AI", full_response)  # 发送更新信号
            else:
                # 处理非流式响应，等待完整响应返回
                full_response = ai_service.chat_completion(
                    self.messages,
                    self.model_name,
                    temperature=self.temperature,
                    stream=False,
                )

            # 非流式响应需要单独发送更新信号
            if not self.stream:
                self.update_signal.emit("AI", full_response)

            # 发送完成状态信号
            self.status_signal.emit(i18n.translate("ai_reply_completed"))

        except Exception as e:
            # 统一处理所有异常
            self._handle_error(e, "聊天")


class SummaryThread(BaseAITaskThread):
    """
    总结线程类，用于处理讨论总结

    信号:
        update_signal: 更新讨论历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
        stream_update_signal: 流式更新信号，参数为(发送者, 内容片段, 模型名称)
        finished_signal: 总结结束信号
    """

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
        super().__init__(
            api_settings_widget=api_settings_widget, temperature=temperature
        )
        self.model_name = model_name
        self.model_api = model_api
        self.messages = messages
        self.config_panel = config_panel
        self.full_response = ""  # 存储完整的总结结果

    def _cleanup_resources(self):
        """
        清理线程资源
        """
        super()._cleanup_resources()
        # 清理消息列表
        self.messages = []
        # 清理总结结果
        self.full_response = ""
    
    def get_summary(self):
        """
        获取总结结果

        Returns:
            str: 完整的总结内容
        """
        return self.full_response

    def run(self):
        """
        线程运行函数，处理总结

        该方法是总结线程的核心执行逻辑，负责：
        1. 确定总结者类型（专家AI3或裁判AI3）
        2. 发送总结请求
        3. 处理流式响应并更新UI
        4. 处理可能出现的异常

        信号输出：
        - status_signal: 用于更新状态信息
        - stream_update_signal: 用于流式更新总结内容
        - finished_signal: 用于通知总结完成
        - error_signal: 用于报告错误信息
        """
        try:
            # 确定发送者名称（专家AI3或裁判AI3）
            sender_name = "专家AI3"  # 默认使用专家AI3

            # 1. 检查系统提示词内容，确定总结者类型
            for msg in self.messages:
                if msg["role"] == "system":
                    content = msg["content"]
                    if "辩论裁判AI" in content:
                        sender_name = "裁判AI3"
                        break
                    elif "学术讨论分析师" in content:
                        sender_name = "专家AI3"
                        break

            # 2. 进一步检查系统提示词内容，确认总结者类型
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

            # 发送开始总结的状态信号
            self.status_signal.emit(
                f"{sender_name}开始总结，模型: {self.model_name} (API: {self.model_api})"
            )

            # 发送总结响应
            full_response = ""

            # 实时获取最新温度值（支持动态调整）
            temperature = self.temperature
            if self.config_panel:
                temperature = self.config_panel.get_temperature()

            # 使用统一的AI服务接口发送请求
            ai_service = self._create_ai_service(self.model_api, self.model_name)
            response_generator = ai_service.chat_completion(
                self.messages,
                self.model_name,
                temperature=temperature,
                stream=True,  # 总结始终使用流式响应
                yield_full_response=False  # 使用增量内容
            )

            # 处理流式响应，逐块更新总结内容
            for chunk in response_generator:
                if self.is_stopped():
                    break  # 检查线程是否被停止
                full_response += chunk  # 累加增量内容
                self.full_response = full_response  # 保存到实例变量
                # 发送流式更新信号
                self.stream_update_signal.emit(
                    sender_name, full_response, self.model_name
                )

            # 发送总结完成的状态信号和结束信号
            self.status_signal.emit(i18n.translate("summary_completed"))
            self.finished_signal.emit()

        except Exception as e:
            # 统一处理所有异常
            self._handle_error(e, "总结")
            self.finished_signal.emit()


class DebateThread(BaseAITaskThread):
    """
    辩论线程类，用于处理双AI辩论

    信号:
        update_signal: 更新辩论历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
        stream_update_signal: 流式更新信号，参数为(发送者, 内容片段, 模型名称)
        finished_signal: 辩论结束信号
    """

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
        super().__init__(
            api_settings_widget=api_settings_widget, temperature=temperature
        )
        self.topics = topics
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.model3_name = model3_name
        self.model1_api = model1_api
        self.model2_api = model2_api
        self.model3_api = model3_api
        self.rounds = rounds
        self.time_limit = time_limit
        self.debate_history_messages = []
        self.start_time = None

    def get_debate_history(self):
        """
        获取辩论历史

        Returns:
            list: 辩论历史列表
        """
        return self.debate_history_messages
        
    def _cleanup_debate_history(self):
        """
        清理辩论历史，只保留最新的消息
        
        保留系统提示词和最新的消息，删除中间的旧消息，防止内存溢出
        """
        # 设置最大辩论历史长度
        max_history_length = 50
        
        if len(self.debate_history_messages) > max_history_length:
            # 保留系统提示词
            system_prompts = [msg for msg in self.debate_history_messages if msg['role'] == 'system']
            # 保留最新的消息
            latest_messages = self.debate_history_messages[-max_history_length+len(system_prompts):]
            # 合并系统提示词和最新消息
            self.debate_history_messages = system_prompts + latest_messages
            logger.info(f"辩论历史已清理，当前长度: {len(self.debate_history_messages)}")

    def _cleanup_resources(self):
        """
        清理线程资源
        """
        super()._cleanup_resources()
        # 清理辩论历史消息
        self.debate_history_messages = []

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
            # 限制对方观点的长度，防止消息过长导致AI模型无法处理
            max_previous_length = 2000
            if len(previous_response) > max_previous_length:
                previous_response = previous_response[:max_previous_length] + "...（内容过长，已截断）"
            message += f"对方观点: {previous_response}\n"
        message += "请根据你的立场进行辩论，逻辑清晰，论点明确。"

        # 构建消息历史
        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": message},
        ]

        # 使用统一的AI服务接口发送请求
        try:
            ai_service = self._create_ai_service(api, model_name)
            full_response = ""

            if stream:
                # 处理流式响应，使用yield_full_response=False只获取增量内容
                response_generator = ai_service.chat_completion(
                    messages, model_name, temperature=temperature, 
                    stream=True, yield_full_response=False
                )

                for chunk in response_generator:
                    if self.is_stopped():
                        break
                    full_response += chunk
                    # 发送流式更新信号
                    self.stream_update_signal.emit(
                        f"{sender_prefix}{model_name}",
                        full_response,
                        model_name,
                    )
            else:
                # 处理非流式响应
                full_response = ai_service.chat_completion(
                    messages, model_name, temperature=temperature, stream=False
                )

            return full_response
        except Exception as e:
            self._handle_error(e, "发送辩论消息")
            return ""

    def run(self):
        """
        线程运行函数，处理双AI辩论

        该方法是辩论线程的核心执行逻辑，负责：
        1. 初始化辩论环境和历史
        2. 遍历辩论主题
        3. 执行多轮辩论
        4. 处理正方和反方的发言
        5. 更新辩论历史和UI
        6. 处理时间限制和线程停止
        7. 处理可能出现的异常

        信号输出：
        - update_signal: 用于更新辩论历史
        - status_signal: 用于更新辩论状态
        - stream_update_signal: 用于流式更新发言内容
        - finished_signal: 用于通知辩论结束
        - error_signal: 用于报告错误信息
        """
        self.start_time = time.time()  # 记录辩论开始时间

        try:
            # 获取辩论系统提示词（从配置文件读取，确保使用最新的设置）
            debate_common_prompt = config_manager.get("debate.system_prompt", "").strip()
            debate_ai1_prompt = config_manager.get("debate.ai1_prompt", "").strip()
            debate_ai2_prompt = config_manager.get("debate.ai2_prompt", "").strip()

            # 初始化辩论历史
            self.debate_history_messages = []

            # 开始辩论，遍历所有辩论主题
            for i, topic in enumerate(self.topics):
                if self.is_stopped():
                    break  # 检查线程是否被停止

                # 检查时间限制
                if (
                    self.time_limit > 0
                    and (time.time() - self.start_time) > self.time_limit
                ):
                    self.status_signal.emit(i18n.translate("debate_timed_out"))
                    break

                # 将主题添加到辩论历史
                self.debate_history_messages.append(
                    {"role": "system", "content": f"{i18n.translate('debate_topic')}: {topic}"}
                )

                # 进行辩论轮次
                for round_num in range(1, self.rounds + 1):
                    if self.is_stopped():
                        break  # 检查线程是否被停止

                    # 发送轮次信息
                    self.update_signal.emit("系统", f"=== {i18n.translate('debate_round', round_num=round_num)} ===")
                    # 将轮次信息添加到辩论历史
                    self.debate_history_messages.append(
                        {"role": "system", "content": f"{i18n.translate('debate_round', round_num=round_num)}"}
                    )

                    # 正方发言阶段
                    self.status_signal.emit(i18n.translate("pro_speaking", model_name=self.model1_name))
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
                        break  # 检查线程是否被停止

                    # 将正方发言添加到辩论历史
                    self.debate_history_messages.append(
                        {"role": f"正方{self.model1_name}", "content": model1_response}
                    )

                    if self.is_stopped():
                        break  # 检查线程是否被停止

                    # 清理辩论历史，防止内存溢出
                    self._cleanup_debate_history()

                    # 反方发言阶段
                    self.status_signal.emit(i18n.translate("con_speaking", model_name=self.model2_name))
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
                        break  # 检查线程是否被停止

                    # 将反方发言添加到辩论历史
                    self.debate_history_messages.append(
                        {"role": f"反方{self.model2_name}", "content": model2_response}
                    )

                    if self.is_stopped():
                        break  # 检查线程是否被停止

            # 计算辩论总耗时
            total_time = time.time() - self.start_time
            self.status_signal.emit(i18n.translate('debate_ended_with_time', total_time=f'{total_time:.2f}'))

            # 发送辩论结束消息
            self.update_signal.emit("系统", f"=== {i18n.translate('debate_ended')} ===")
            self.debate_history_messages.append(
                {"role": "system", "content": i18n.translate('debate_ended')}
            )

            # 发送辩论结束信号
            self.finished_signal.emit()

        except Exception as e:
            # 统一处理所有异常
            self._handle_error(e, "辩论")
            self.finished_signal.emit()


class DiscussionThread(BaseAITaskThread):
    """
    讨论线程类，用于处理双AI讨论

    信号:
        update_signal: 更新讨论历史信号，参数为(发送者, 内容)
        status_signal: 更新状态信号，参数为状态信息
        error_signal: 错误信号，参数为错误信息
        stream_update_signal: 流式更新信号，参数为(发送者, 内容片段, 模型名称)
        finished_signal: 讨论结束信号
    """

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
        super().__init__(
            api_settings_widget=api_settings_widget, temperature=temperature
        )
        self.topic = topic
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.model1_api = model1_api
        self.model2_api = model2_api
        self.model3_name = model3_name
        self.model3_api = model3_api
        self.rounds = rounds
        self.time_limit = time_limit
        self.config_panel = config_panel

        # 讨论历史存储
        self.discussion_history = []
        # 讨论历史最大长度，超过后将清理旧消息
        self.max_discussion_history = 50

        # 时间管理
        self.start_time = None

    def get_discussion_history(self):
        """
        获取讨论历史

        Returns:
            list: 讨论历史列表
        """
        return self.discussion_history

    def _cleanup_discussion_history(self):
        """
        清理讨论历史，只保留最新的消息
        
        保留系统提示词和最新的消息，删除中间的旧消息
        """
        if len(self.discussion_history) > self.max_discussion_history:
            # 保留系统提示词
            system_prompts = [msg for msg in self.discussion_history if msg['role'] == 'system']
            # 保留最新的消息
            latest_messages = self.discussion_history[-self.max_discussion_history+len(system_prompts):]
            # 合并系统提示词和最新消息
            self.discussion_history = system_prompts + latest_messages
            logger.info(f"讨论历史已清理，当前长度: {len(self.discussion_history)}")
    
    def _cleanup_resources(self):
        """
        清理线程资源
        """
        super()._cleanup_resources()
        # 清理讨论历史消息
        self.discussion_history = []

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
        try:
            # 实时获取最新温度值
            current_temperature = self.temperature
            if self.config_panel:
                current_temperature = self.config_panel.get_temperature()

            # 使用统一的AI服务接口发送请求
            ai_service = self._create_ai_service(api, model_name)
            full_response = ""

            if stream:
                # 处理流式响应，使用yield_full_response=False只获取增量内容
                response_generator = ai_service.chat_completion(
                    messages, model_name, temperature=current_temperature, 
                    stream=True, yield_full_response=False
                )

                for chunk in response_generator:
                    if self.is_stopped():
                        break
                    full_response += chunk
                    # 发送流式更新信号
                    self.stream_update_signal.emit(
                        f"{sender_prefix} {model_name}", full_response, model_name
                    )
            else:
                # 处理非流式响应
                full_response = ai_service.chat_completion(
                    messages, model_name, temperature=current_temperature, stream=False
                )

            return full_response
        except Exception as e:
            self._handle_error(e, "获取AI响应")
            return ""

    def run(self):
        """
        线程运行函数，处理双AI讨论

        该方法是讨论线程的核心执行逻辑，负责：
        1. 初始化讨论环境和历史
        2. 设置讨论主题和参数
        3. 执行多轮讨论
        4. 处理AI1和AI2的交替发言
        5. 构建发言上下文和系统提示词
        6. 更新讨论历史和UI
        7. 处理时间限制和线程停止
        8. 处理可能出现的异常

        信号输出：
        - update_signal: 用于更新讨论历史
        - status_signal: 用于更新讨论状态
        - stream_update_signal: 用于流式更新发言内容
        - finished_signal: 用于通知讨论结束
        - error_signal: 用于报告错误信息
        """
        self.start_time = time.time()  # 记录讨论开始时间

        try:
            # 获取讨论系统提示词（从配置文件读取，确保使用最新的设置）
            discussion_common_prompt = config_manager.get("discussion.system_prompt", "").strip()
            discussion_ai1_prompt = config_manager.get(
                "discussion.ai1_prompt", ""
            ).strip()
            discussion_ai2_prompt = config_manager.get(
                "discussion.ai2_prompt", ""
            ).strip()

            # 初始化讨论历史
            self.discussion_history = []
            # 添加系统提示词到讨论历史
            self.discussion_history.append(
                {"role": "system", "content": discussion_common_prompt}
            )

            # 发送讨论开始的状态信息
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
                    self.status_signal.emit(i18n.translate("discussion_timed_out"))
                    logger.info(f"{i18n.translate('discussion_timed_out')}，当前轮次: {round_num}")
                    break

                # 更新状态信号，显示当前轮次
                self.status_signal.emit(
                    i18n.translate("discussion_round_start", round_num=round_num, total_rounds=self.rounds)
                )

                # 发送轮次信息
                self.update_signal.emit("系统", f"=== {i18n.translate('discussion_round', round_num=round_num)} ===")

                # ============================ AI1发言阶段 ============================
                try:
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
                        for msg in self.discussion_history[1:]:
                            # 直接使用消息中的role作为发言者标识
                            speaker = msg['role']
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
                    
                    # 清理讨论历史，只保留最新的消息
                    self._cleanup_discussion_history()
                except Exception as e:
                    logger.error(f"AI1发言阶段出错: {str(e)}")
                    self._handle_error(e, "AI1发言")
                    break

                # ============================ AI2发言阶段 ============================
                try:
                    # 更新状态，显示AI2正在发言
                    self.status_signal.emit(f"学者AI2 {self.model2_name} 正在发言...")

                    # 构建AI2的系统提示词，合并公共提示词和AI2专用提示词
                    ai2_system_prompt = discussion_common_prompt
                    if discussion_ai2_prompt:
                        ai2_system_prompt += "\n" + discussion_ai2_prompt

                    # 构建AI2的上下文，包含主题和之前的讨论内容
                    ai2_context = f"主题：{self.topic}。\n\n"
                    if self.discussion_history:
                        # 添加之前的讨论内容，跳过系统提示词
                        for msg in self.discussion_history[1:]:
                            # 直接使用消息中的role作为发言者标识
                            speaker = msg['role']
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
                    
                    # 清理讨论历史，只保留最新的消息
                    self._cleanup_discussion_history()
                except Exception as e:
                    logger.error(f"AI2发言阶段出错: {str(e)}")
                    self._handle_error(e, "AI2发言")
                    break

                # ============================ 本轮讨论结束 ============================

            # 计算讨论总耗时
            total_time = time.time() - self.start_time
            self.status_signal.emit(i18n.translate('discussion_ended_with_time', total_time=f'{total_time:.2f}'))

            # 添加讨论结束消息到讨论历史
            self.update_signal.emit("系统", f"=== {i18n.translate('discussion_ended')} ===")
            self.finished_signal.emit()
        except Exception as e:
            # 统一处理所有异常
            logger.error(f"讨论线程主循环出错: {str(e)}")
            self._handle_error(e, "讨论")
            self.finished_signal.emit()
