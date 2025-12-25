# -*- coding: utf-8 -*-
"""
聊天历史管理模块
负责聊天历史的保存、加载和导出功能
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Callable
from .logger_config import get_logger
from PyQt5.QtCore import QThread, pyqtSignal

# 获取日志记录器
logger = get_logger(__name__)


class ChatHistoryLoadWorker(QThread):
    """
    异步加载聊天历史的工作线程
    """

    # 定义信号
    finished = pyqtSignal(list)  # 加载完成信号，传递加载的聊天历史
    error = pyqtSignal(str)  # 错误信号，传递错误信息

    def __init__(self, history_file: str):
        """
        初始化工作线程

        Args:
            history_file (str): 聊天历史文件路径
        """
        super().__init__()
        self.history_file = history_file

    def run(self):
        """
        线程运行函数，执行异步加载
        """
        try:
            logger.info(f"异步加载聊天历史: {self.history_file}")
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # 确保 chat_histories 始终是一个列表
                    if isinstance(loaded_data, list):
                        chat_histories = loaded_data
                    else:
                        chat_histories = []
                        logger.warning(
                            f"{self.history_file} 中的内容不是列表，创建空历史记录列表"
                        )
                logger.info(f"已异步加载 {len(chat_histories)} 条历史记录")
            else:
                chat_histories = []
                logger.info(f"{self.history_file} 不存在，创建空历史记录列表")

            self.finished.emit(chat_histories)
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {str(e)}")
            self.error.emit(f"文件未找到: {str(e)}")
            self.finished.emit([])
        except PermissionError as e:
            logger.error(
                f"权限错误: 无法读取文件 {self.history_file}，错误信息: {str(e)}"
            )
            self.error.emit(f"权限错误: {str(e)}")
            self.finished.emit([])
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON解析错误: 文件 {self.history_file} 格式无效，错误信息: {str(e)}"
            )
            self.error.emit(f"JSON解析错误: {str(e)}")
            self.finished.emit([])
        except Exception as e:
            logger.error(f"异步加载聊天历史失败: {str(e)}")
            self.error.emit(f"加载失败: {str(e)}")
            self.finished.emit([])


class ChatHistoryManager:
    """
    聊天历史管理类，负责聊天历史的保存、加载和导出功能
    """

    def __init__(self, history_file: str = "chat_histories.json") -> None:
        """
        初始化聊天历史管理器

        Args:
            history_file (str, optional): 聊天历史文件路径. Defaults to 'chat_histories.json'.
        """
        import sys
        import os

        # 确定应用程序的数据目录，使用用户应用程序数据目录
        import os

        if getattr(sys, "frozen", False):
            # 打包后的可执行文件，使用用户应用程序数据目录
            app_data_dir = os.path.join(os.getenv("APPDATA"), "NONEAD", "AI_Talking")
        else:
            # 开发环境下，使用当前目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            current_dir = os.path.dirname(current_dir)  # 向上一级目录
            current_dir = os.path.dirname(current_dir)  # 再向上一级目录
            app_data_dir = current_dir

        # 确保应用程序数据目录存在
        os.makedirs(app_data_dir, exist_ok=True)

        # 使用应用程序数据目录作为聊天历史文件的保存位置
        self.history_file: str = os.path.join(app_data_dir, history_file)
        self.max_history_size: int = 1000  # 限制最大历史记录数量，防止内存占用过高

        # 初始化空的聊天历史列表，不自动加载
        self.chat_histories: List[Dict] = []

    def async_load_history(
        self,
        callback: Callable[[List[Dict]], None],
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        异步加载聊天历史

        Args:
            callback (Callable[[List[Dict]], None]): 加载完成后的回调函数
            error_callback (Optional[Callable[[str], None]], optional): 加载错误时的回调函数. Defaults to None.
        """
        # 创建工作线程
        self.load_worker = ChatHistoryLoadWorker(self.history_file)

        # 连接信号
        self.load_worker.finished.connect(self._on_async_load_finished)
        if error_callback:
            self.load_worker.error.connect(error_callback)

        # 保存回调函数
        self._load_callback = callback

        # 启动线程
        self.load_worker.start()

    def _on_async_load_finished(self, chat_histories: List[Dict]) -> None:
        """
        异步加载完成的槽函数

        Args:
            chat_histories (List[Dict]): 加载的聊天历史
        """
        self.chat_histories = chat_histories
        logger.info(f"异步加载完成: 共 {len(chat_histories)} 条历史记录")

        # 调用回调函数
        if hasattr(self, "_load_callback") and self._load_callback:
            self._load_callback(chat_histories)

    def load_history(self) -> List[Dict]:
        """
        同步从文件加载聊天历史
        仅用于需要立即获取历史记录的场景

        Returns:
            List[Dict]: 聊天历史列表
        """
        logger.info(f"正在从 {self.history_file} 加载聊天历史...")
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # 确保 chat_histories 始终是一个列表
                    if isinstance(loaded_data, list):
                        self.chat_histories = loaded_data
                    else:
                        self.chat_histories = []
                        logger.warning(
                            f"{self.history_file} 中的内容不是列表，创建空历史记录列表"
                        )
                logger.info(
                    f"已从 {self.history_file} 加载 {len(self.chat_histories)} 条历史记录"
                )
            else:
                self.chat_histories = []
                logger.info(f"{self.history_file} 不存在，创建空历史记录列表")
            return self.chat_histories
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {str(e)}")
            return []
        except PermissionError as e:
            logger.error(
                f"权限错误: 无法读取文件 {self.history_file}，错误信息: {str(e)}"
            )
            return []
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON解析错误: 文件 {self.history_file} 格式无效，错误信息: {str(e)}"
            )
            return []
        except Exception as e:
            logger.error(f"加载聊天历史失败: {str(e)}")
            return []

    def _prune_old_history(self) -> None:
        """
        修剪旧历史记录，保持在最大限制内
        """
        if len(self.chat_histories) > self.max_history_size:
            # 只保留最新的 max_history_size 条记录
            old_count = len(self.chat_histories) - self.max_history_size
            self.chat_histories = self.chat_histories[-self.max_history_size :]
            logger.info(
                f"已修剪 {old_count} 条旧历史记录，当前保留 {len(self.chat_histories)} 条"
            )

    def save_history(self, history: Optional[List[Dict]] = None) -> bool:
        """
        保存聊天历史到文件

        Args:
            history (Optional[List[Dict]], optional): 要保存的聊天历史列表. Defaults to None, 表示保存当前管理的历史.

        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            if history is not None:
                self.chat_histories = history

            # 修剪旧历史记录
            self._prune_old_history()

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.chat_histories, f, ensure_ascii=False, indent=2)

            logger.info(
                f"已保存 {len(self.chat_histories)} 条历史记录到 {self.history_file}"
            )
            return True
        except PermissionError as e:
            logger.error(
                f"权限错误: 无法写入文件 {self.history_file}，错误信息: {str(e)}"
            )
            return False
        except IOError as e:
            logger.error(
                f"I/O错误: 写入文件 {self.history_file} 失败，错误信息: {str(e)}"
            )
            return False
        except TypeError as e:
            logger.error(
                f"类型错误: 聊天历史数据包含不可序列化的类型，错误信息: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON编码错误: 无法将聊天历史转换为JSON格式，错误信息: {str(e)}"
            )
            return False
        except Exception as e:
            logger.error(f"保存聊天历史失败: {str(e)}")
            return False

    def generate_formatted_topic(
        self, func_type: str, topic: Optional[str] = None
    ) -> str:
        """
        生成格式化的主题名称

        Args:
            func_type (str): 功能类型，可选值："聊天"、"讨论"、"辩论"、"批量"
            topic (Optional[str], optional): 原主题内容. Defaults to None.

        Returns:
            str: 格式化的主题名称
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if func_type == "聊天":
            return f"【聊天】{current_time}"
        elif func_type == "讨论":
            return f"【讨论】{topic} {current_time}"
        elif func_type == "辩论":
            return f"【辩论】{topic} {current_time}"
        elif func_type == "批量":
            return f"【批量】{topic} {current_time}"
        else:
            return f"【未知】{topic or '无主题'} {current_time}"

    def add_history(
        self,
        func_type: str,
        topic: str,
        model1_name: str,
        model2_name: Optional[str],
        api1: str,
        api2: str,
        rounds: int,
        chat_content: str,
        start_time: str,
        end_time: str,
    ) -> bool:
        """
        添加聊天历史记录
        和同一个模型聊天，只记录一条历史，除非更换了模型

        Args:
            func_type (str): 功能类型，可选值："聊天"、"讨论"、"辩论"、"批量"
            topic (str): 讨论主题
            model1_name (str): 模型1名称
            model2_name (Optional[str]): 模型2名称
            api1 (str): 模型1 API类型
            api2 (str): 模型2 API类型
            rounds (int): 对话轮数
            chat_content (str): 聊天内容
            start_time (str): 开始时间
            end_time (str): 结束时间

        Returns:
            bool: 添加成功返回True，失败返回False
        """
        # 生成格式化的主题名称
        formatted_topic = self.generate_formatted_topic(func_type, topic)

        # 检查是否存在相同模型组合的历史记录
        for i, existing_history in enumerate(self.chat_histories):
            # 对于单聊模式，只比较model1和api1
            if model2_name is None or model2_name == "":
                if (
                    existing_history["model1"] == model1_name
                    and existing_history["api1"] == api1
                ):
                    # 更新现有记录
                    self.chat_histories[i] = {
                        "topic": formatted_topic,
                        "model1": model1_name,
                        "model2": model2_name,
                        "api1": api1,
                        "api2": api2,
                        "rounds": rounds,
                        "chat_content": chat_content,
                        "start_time": start_time,
                        "end_time": end_time,
                    }
                    return self.save_history()
            else:
                # 对于讨论/辩论模式，比较两个模型的组合
                if (
                    existing_history["model1"] == model1_name
                    and existing_history["api1"] == api1
                    and existing_history["model2"] == model2_name
                    and existing_history["api2"] == api2
                ) or (
                    existing_history["model1"] == model2_name
                    and existing_history["api1"] == api2
                    and existing_history["model2"] == model1_name
                    and existing_history["api2"] == api1
                ):
                    # 更新现有记录
                    self.chat_histories[i] = {
                        "topic": formatted_topic,
                        "model1": model1_name,
                        "model2": model2_name,
                        "api1": api1,
                        "api2": api2,
                        "rounds": rounds,
                        "chat_content": chat_content,
                        "start_time": start_time,
                        "end_time": end_time,
                    }
                    return self.save_history()

        # 如果没有相同模型组合的记录，添加新记录
        history = {
            "topic": formatted_topic,
            "model1": model1_name,
            "model2": model2_name,
            "api1": api1,
            "api2": api2,
            "rounds": rounds,
            "chat_content": chat_content,
            "start_time": start_time,
            "end_time": end_time,
        }

        self.chat_histories.append(history)
        return self.save_history()

    def get_history_by_topic(self, topic: str) -> Optional[Dict]:
        """
        根据主题获取聊天历史

        Args:
            topic (str): 讨论主题

        Returns:
            Optional[Dict]: 匹配的聊天历史记录，不存在返回None
        """
        for history in self.chat_histories:
            if history["topic"] == topic:
                return history
        return None

    def clear_history(self) -> bool:
        """
        清空聊天历史

        Returns:
            bool: 清空成功返回True，失败返回False
        """
        self.chat_histories = []
        return self.save_history()

    def delete_history(self, index: int) -> bool:
        """
        删除指定索引的聊天历史

        Args:
            index (int): 历史记录索引

        Returns:
            bool: 删除成功返回True，失败返回False
        """
        if 0 <= index < len(self.chat_histories):
            del self.chat_histories[index]
            return self.save_history()
        return False

    def export_history_to_json(self, export_path: str) -> bool:
        """
        将聊天历史导出为JSON文件

        Args:
            export_path (str): 导出文件路径

        Returns:
            bool: 导出成功返回True，失败返回False
        """
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(self.chat_histories, f, ensure_ascii=False, indent=2)
            logger.info(f"已将聊天历史导出到 {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出聊天历史到JSON失败: {str(e)}")
            return False
