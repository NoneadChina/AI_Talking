# -*- coding: utf-8 -*-
"""
聊天历史管理模块
负责聊天历史的保存、加载、分页获取和导出功能

该模块实现了聊天历史的完整生命周期管理，包括：
1. 异步加载聊天历史，避免阻塞主线程
2. 分页获取历史记录，优化内存使用
3. 缓存机制，减少文件I/O操作
4. 历史记录的添加、删除、清空等操作
5. 聊天历史导出功能
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Callable, Any, Literal, TypedDict
from .logger_config import get_logger
from .i18n_manager import i18n
from PyQt5.QtCore import QThread, pyqtSignal

# 获取日志记录器
logger = get_logger(__name__)


# 定义聊天历史记录的类型
class ChatHistoryItem(TypedDict):
    """聊天历史记录项的类型定义
    
    每个聊天历史记录包含以下字段：
    - topic: 聊天主题
    - model1: 模型1名称
    - model2: 模型2名称（可选，单聊时为None）
    - api1: 模型1使用的API提供商
    - api2: 模型2使用的API提供商
    - rounds: 聊天轮数
    - chat_content: 聊天内容
    - start_time: 开始时间
    - end_time: 结束时间
    """
    topic: str
    model1: str
    model2: Optional[str]
    api1: str
    api2: str
    rounds: int
    chat_content: str
    start_time: str
    end_time: str


class ChatHistoryLoadWorker(QThread):
    """
    异步加载聊天历史的工作线程
    
    该类用于在后台线程中加载聊天历史，避免阻塞主线程，
    提高应用程序的响应性能。
    """

    # 定义信号 - PyQt5的pyqtSignal不支持List[ChatHistoryItem]这种类型注解格式
    finished = pyqtSignal(list)  # 加载完成信号，传递加载的聊天历史列表
    error = pyqtSignal(str)  # 错误信号，传递错误信息字符串

    def __init__(self, history_file: str):
        """
        初始化工作线程

        Args:
            history_file (str): 聊天历史文件路径
        """
        super().__init__()
        self.history_file = history_file  # 保存聊天历史文件路径

    def run(self):
        """
        线程运行函数，执行异步加载
        
        在线程中执行文件读取和解析操作，
        处理可能出现的各种异常，
        通过信号返回结果或错误信息。
        """
        try:
            logger.info(f"异步加载聊天历史: {self.history_file}")
            if os.path.exists(self.history_file):
                # 文件存在时读取并解析
                with open(self.history_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # 确保 chat_histories 始终是一个列表
                    if isinstance(loaded_data, list):
                        chat_histories = loaded_data
                    else:
                        # 文件格式不正确时，创建空列表
                        chat_histories = []
                        logger.warning(
                            f"{self.history_file} 中的内容不是列表，创建空历史记录列表"
                        )
                logger.info(f"已异步加载 {len(chat_histories)} 条历史记录")
            else:
                # 文件不存在时，创建空列表
                chat_histories = []
                logger.info(f"{self.history_file} 不存在，创建空历史记录列表")

            # 发送加载完成信号，传递聊天历史列表
            self.finished.emit(chat_histories)
        except FileNotFoundError as e:
            # 处理文件未找到异常
            logger.error(f"文件未找到: {str(e)}")
            self.error.emit(f"文件未找到: {str(e)}")
            self.finished.emit([])
        except PermissionError as e:
            # 处理权限错误
            logger.error(
                f"权限错误: 无法读取文件 {self.history_file}，错误信息: {str(e)}"
            )
            self.error.emit(f"权限错误: {str(e)}")
            self.finished.emit([])
        except json.JSONDecodeError as e:
            # 处理JSON解析错误
            logger.error(
                f"JSON解析错误: 文件 {self.history_file} 格式无效，错误信息: {str(e)}"
            )
            self.error.emit(f"JSON解析错误: {str(e)}")
            self.finished.emit([])
        except Exception as e:
            # 处理其他未预期的异常
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
        from .config_manager import get_app_data_dir

        # 确定应用程序的数据目录，使用统一的get_app_data_dir函数
        app_data_dir = get_app_data_dir()

        # 确保应用程序数据目录存在
        os.makedirs(app_data_dir, exist_ok=True)

        # 使用应用程序数据目录作为聊天历史文件的保存位置
        self.history_file: str = os.path.join(app_data_dir, history_file)
        self.max_history_size: int = 1000  # 限制最大历史记录数量，防止内存占用过高
        self._loaded_history_count: int = 0  # 记录已加载的历史记录数量
        
        # 缓存机制 - 优化内存使用
        self._history_cache: List[ChatHistoryItem] = []  # 缓存已加载的历史记录
        self._is_cache_loaded: bool = False  # 标记缓存是否已加载
        self._modified_indices: set[int] = set()  # 标记已修改的记录索引
        
        # 惰性加载标志 - 只有在需要时才加载历史记录
        self._lazy_load_triggered: bool = False
        
        # 初始化聊天历史列表 - 不立即加载，改为惰性加载
        self.chat_histories: List[ChatHistoryItem] = []

    def async_load_history(
        self,
        callback: Callable[[List[ChatHistoryItem]], None],
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

    def _on_async_load_finished(self, chat_histories: List[ChatHistoryItem]) -> None:
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

    def _load_full_history(self) -> List[ChatHistoryItem]:
        """
        从文件加载完整的聊天历史到缓存
        """
        logger.info(f"正在从 {self.history_file} 加载完整聊天历史...")
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # 确保 chat_histories 始终是一个列表
                    if isinstance(loaded_data, list):
                        self._history_cache = loaded_data
                        self._is_cache_loaded = True
                        logger.info(
                            f"已从 {self.history_file} 加载 {len(self._history_cache)} 条历史记录到缓存"
                        )
                    else:
                        self._history_cache = []
                        self._is_cache_loaded = True
                        logger.warning(
                            f"{self.history_file} 中的内容不是列表，创建空历史记录列表"
                        )
            else:
                self._history_cache = []
                self._is_cache_loaded = True
                logger.info(f"{self.history_file} 不存在，创建空历史记录列表")
            return self._history_cache
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
    
    def load_history(self) -> List[ChatHistoryItem]:
        """
        同步从缓存加载聊天历史
        仅用于需要立即获取历史记录的场景

        Returns:
            List[Dict]: 聊天历史列表
        """
        if not self._is_cache_loaded:
            self._load_full_history()
        
        # 标记为已触发惰性加载
        self._lazy_load_triggered = True
        
        # 直接返回缓存引用，避免复制开销
        self.chat_histories = self._history_cache
        logger.info(f"从缓存加载了 {len(self.chat_histories)} 条历史记录")
        return self.chat_histories
    
    def get_history_page(self, page: int = 1, page_size: int = 20) -> List[ChatHistoryItem]:
        """
        分页获取历史记录

        Args:
            page (int): 页码，从1开始
            page_size (int): 每页记录数

        Returns:
            List[Dict]: 分页后的历史记录列表
        """
        if not self._is_cache_loaded:
            self._load_full_history()
        
        # 计算分页范围
        start = (page - 1) * page_size
        end = start + page_size
        
        # 返回分页数据
        paginated = self._history_cache[start:end]
        logger.info(f"返回第 {page} 页历史记录，共 {len(paginated)} 条")
        return paginated
    
    def get_history_count(self) -> int:
        """
        获取历史记录总数

        Returns:
            int: 历史记录总数
        """
        if not self._is_cache_loaded:
            self._load_full_history()
        
        return len(self._history_cache)

    def _prune_old_history(self) -> None:
        """
        修剪旧历史记录，保持在最大限制内
        兼容旧代码，实际已在save_history中直接处理
        """
        if len(self._history_cache) > self.max_history_size:
            # 只保留最新的 max_history_size 条记录
            old_count = len(self._history_cache) - self.max_history_size
            self._history_cache = self._history_cache[-self.max_history_size :]
            # 同步更新chat_histories
            self.chat_histories = self._history_cache
            logger.info(
                f"已修剪 {old_count} 条旧历史记录，当前保留 {len(self._history_cache)} 条"
            )

    def save_history(self, history: Optional[List[ChatHistoryItem]] = None) -> bool:
        """
        保存聊天历史到文件

        Args:
            history (Optional[List[Dict]], optional): 要保存的聊天历史列表. Defaults to None, 表示保存当前管理的历史.

        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            save_force = False
            if history is not None:
                self.chat_histories = history
                self._history_cache = history
                self._is_cache_loaded = True
                # 标记所有记录为已修改
                self._modified_indices.clear()
                # 强制保存，因为传入了新的历史记录
                save_force = True
            
            # 如果没有修改且不是强制保存，跳过保存
            if not save_force and not self._modified_indices and len(self._history_cache) > 0:
                logger.info("没有修改的历史记录，跳过保存")
                return True

            # 修剪旧历史记录 - 直接操作缓存
            if len(self._history_cache) > self.max_history_size:
                old_count = len(self._history_cache) - self.max_history_size
                self._history_cache = self._history_cache[-self.max_history_size :]
                logger.info(
                    f"已修剪 {old_count} 条旧历史记录，当前保留 {len(self._history_cache)} 条"
                )

            # 同步chat_histories和缓存
            self.chat_histories = self._history_cache
            
            # 使用更高效的JSON序列化方式，去掉缩进以减小文件大小
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self._history_cache, f, ensure_ascii=False, separators=(',', ':'))

            logger.info(
                f"已保存 {len(self._history_cache)} 条历史记录到 {self.history_file}"
            )
            
            # 清空已修改标记
            self._modified_indices.clear()
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
        except Exception as e:
            logger.error(f"保存聊天历史失败: {str(e)}")
            return False

    def generate_formatted_topic(
        self, func_type: Literal["聊天", "讨论", "辩论", "批量"], topic: Optional[str] = None
    ) -> str:
        """
        生成格式化的主题名称

        Args:
            func_type (Literal["聊天", "讨论", "辩论", "批量"]): 功能类型
            topic (Optional[str], optional): 原主题内容. Defaults to None.

        Returns:
            str: 格式化的主题名称
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 功能类型到翻译键的映射
        func_type_map = {
            "聊天": "chat",
            "讨论": "discussion",
            "辩论": "debate",
            "批量": "batch"
        }
        
        # 获取翻译后的功能类型
        translated_type = i18n.translate(func_type_map.get(func_type, "unknown"))
        
        # 根据功能类型生成不同格式的主题
        if func_type == "聊天":
            return f"【{translated_type}】{current_time}"
        else:
            return f"【{translated_type}】{topic} {current_time}"

    def add_history(
        self,
        func_type: Literal["聊天", "讨论", "辩论", "批量"],
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
        对于讨论、辩论、批量功能，每次都添加新记录

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
        # 确保缓存已加载
        if not self._is_cache_loaded:
            self._load_full_history()
        
        # 生成格式化的主题名称
        formatted_topic = self.generate_formatted_topic(func_type, topic)

        # 对于聊天功能，同一个模型只保存一条历史记录，更新现有记录
        if func_type == "聊天":
            # 检查是否存在相同模型组合的历史记录
            for i, existing_history in enumerate(self._history_cache):
                # 对于单聊模式，只比较model1和api1
                if existing_history["model1"] == model1_name and existing_history["api1"] == api1:
                    # 更新现有记录 - 优化：只更新必要的字段
                    updated_history = existing_history.copy()
                    updated_history.update({
                        "topic": formatted_topic,
                        "model2": model2_name,
                        "api2": api2,
                        "rounds": rounds,
                        "chat_content": chat_content,
                        "end_time": end_time,  # 更新结束时间
                    })
                    self._history_cache[i] = updated_history
                    
                    # 同步更新chat_histories属性
                    self.chat_histories = self._history_cache
                    
                    # 标记为已修改
                    self._modified_indices.add(i)
                    return self.save_history()
        
        # 对于讨论、辩论、批量功能，每次都添加新记录
        # 或者对于新的聊天模型，添加新记录
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

        self._history_cache.append(history)
        # 同步更新chat_histories属性
        self.chat_histories = self._history_cache
        
        # 标记新添加的记录为已修改
        self._modified_indices.add(len(self._history_cache) - 1)
        return self.save_history()

    def get_history_by_topic(self, topic: str) -> Optional[ChatHistoryItem]:
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
        # 清空缓存和聊天历史列表
        self._history_cache = []
        self.chat_histories = []
        
        # 标记缓存已加载（因为我们已经知道它是空的）
        self._is_cache_loaded = True
        
        # 清空修改列表
        self._modified_indices.clear()
        
        return self.save_history()

    def delete_history(self, index: int) -> bool:
        """
        删除指定索引的聊天历史

        Args:
            index (int): 历史记录索引

        Returns:
            bool: 删除成功返回True，失败返回False
        """
        if not self._is_cache_loaded:
            self._load_full_history()
            
        if 0 <= index < len(self._history_cache):
            # 如果删除的索引在修改列表中，先移除它
            if index in self._modified_indices:
                self._modified_indices.remove(index)
            
            # 删除缓存中的记录
            del self._history_cache[index]
            
            # 更新修改列表中的索引（所有大于删除索引的索引都减1）
            updated_indices = set()
            for i in self._modified_indices:
                if i < index:
                    updated_indices.add(i)
                elif i > index:
                    updated_indices.add(i - 1)
            self._modified_indices = updated_indices
            
            # 更新聊天历史列表
            self.chat_histories = self._history_cache.copy()
            
            # 强制保存，因为删除操作会影响所有后续记录的索引
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
            # 使用缓存数据进行导出
            if not self._is_cache_loaded:
                self._load_full_history()
            
            with open(export_path, "w", encoding="utf-8") as f:
                # 添加default=str参数，将不可序列化的对象转换为字符串
                json.dump(self._history_cache, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"已将聊天历史导出到 {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出聊天历史到JSON失败: {str(e)}")
            return False
