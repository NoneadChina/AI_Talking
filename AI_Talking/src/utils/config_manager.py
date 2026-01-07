# -*- coding: utf-8 -*-
"""
配置文件管理器
支持从YAML配置文件加载配置，并提供默认值和环境变量覆盖功能
"""

import os
import sys
import yaml
from typing import Dict, Any, Optional


def get_app_data_dir():
    """
    获取应用程序数据目录，根据不同操作系统返回不同路径
    
    Returns:
        str: 应用程序数据目录的绝对路径
    """
    # 应用名称，用于创建数据目录
    app_name = "AI_Talking"
    
    if sys.platform.startswith('win'):
        # Windows: C:\Users\用户名\AppData\Roaming\应用名称
        return os.path.join(os.getenv('APPDATA'), app_name)
    elif sys.platform.startswith('darwin'):
        # macOS: ~/Library/Application Support/应用名称
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    else:
        # Linux: ~/.应用名称
        return os.path.join(os.path.expanduser('~'), f'.{app_name}')


class ConfigManager:
    """配置文件管理器类
    
    该类负责处理配置文件的加载、保存和访问，支持从YAML文件加载配置，
    并提供默认值、环境变量覆盖和点号分隔的路径访问功能。
    """
    
    def __init__(self, config_file_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file_path: 配置文件路径，如果不提供则使用默认路径
        """
        # 默认配置文件路径
        if config_file_path is None:
            import sys
            import os
            
            # 根据运行环境选择配置文件路径
            if getattr(sys, "frozen", False):
                # 发布阶段：使用用户目录下的配置文件
                app_data_dir = get_app_data_dir()
                config_file_path = os.path.join(app_data_dir, 'config.yaml')
            else:
                # 调试阶段：使用项目根目录下的配置文件
                current_dir = os.path.dirname(os.path.abspath(__file__))
                current_dir = os.path.dirname(current_dir)  # 向上一级目录到src
                current_dir = os.path.dirname(current_dir)  # 再向上一级目录到项目根目录
                config_file_path = os.path.join(current_dir, 'config.yaml')
        
        self.config_file_path = config_file_path  # 配置文件路径
        self.config: Dict[str, Any] = {}  # 配置数据字典
        self._load_default_config()  # 加载默认配置
        self.load_config()  # 从文件加载配置
    
    def _load_default_config(self) -> None:
        """
        加载默认配置
        
        此方法定义了应用程序的默认配置值，包括应用基本信息、API设置、
        聊天配置、讨论配置、辩论配置、翻译设置、语言设置、日志配置和更新设置。
        """
        # 获取应用数据目录，用于设置日志文件的绝对路径
        app_data_dir = get_app_data_dir()
        
        self.config = {
            'app': {
                'name': 'AI Talking',  # 应用名称
                'version': '0.4.1',  # 应用版本
                'debug': False,  # 调试模式开关
                'language': 'auto',  # 语言设置，'auto'表示自动检测
                'window': {
                    'x': 100,  # 窗口初始X坐标
                    'y': 100,  # 窗口初始Y坐标
                    'width': 900,  # 窗口初始宽度
                    'height': 1000  # 窗口初始高度
                }
            },
            'api': {
                'timeout': 300,  # API调用超时时间（秒）
                'max_retries': 3,  # API调用最大重试次数
                'retry_delay': 2.0,  # 重试间隔（秒）
                'openai_key': '',  # OpenAI API密钥
                'deepseek_key': '',  # DeepSeek API密钥
                'ollama_cloud_key': '',  # Ollama Cloud API密钥
                'ollama_cloud_base_url': 'https://ollama.com',  # Ollama Cloud基础URL
                'ollama_base_url': 'http://localhost:11434'  # Ollama本地基础URL
            },
            'chat': {
                'max_history_length': 50,  # 聊天历史最大消息数
                'auto_save': True,  # 是否自动保存聊天历史
                'save_interval': 30,  # 自动保存间隔（秒）
                'system_prompt': ''  # 聊天系统提示词
            },
            'discussion': {
                'system_prompt': '',  # 讨论共享系统提示词
                'ai1_prompt': '',  # 讨论AI1系统提示词
                'ai2_prompt': '',  # 讨论AI2系统提示词
                'expert_ai3_prompt': ''  # 专家AI3系统提示词
            },
            'debate': {
                'system_prompt': '',  # 辩论共享系统提示词
                'ai1_prompt': '',  # 辩论AI1系统提示词（正方）
                'ai2_prompt': '',  # 辩论AI2系统提示词（反方）
                'judge_ai3_prompt': ''  # 裁判AI3系统提示词
            },
            'translation': {
                'provider': 'openai',  # 翻译服务提供商
                'default_model': 'gpt-4o',  # 默认翻译模型
                'system_prompt': '你是一个好用的翻译助手。请将我输入的任何一种语言（当前气泡内容），翻译我需要的语言(需要的语言从翻译菜单选择的语言获取），请直接翻译成例子里的语言即可，我们不做任何的问答，我发给你所有的话都是需要翻译的内容，你只需要回答翻译结果。'  # 翻译系统提示词
            },
            'language': {
                'selection': '简体中文'  # 默认语言选择
            },
            'logging': {
                'level': 'INFO',  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
                'file_path': os.path.join(app_data_dir, 'logs/app.log'),  # 日志文件路径
                'max_bytes': 10485760,  # 单个日志文件最大字节数（10MB）
                'backup_count': 5  # 保留的备份日志文件数
            },
            'update': {
                'check_interval': 24,  # 更新检查间隔（小时）
                'auto_check': True,  # 是否自动检查更新
                'auto_update': False  # 是否自动下载更新
            }
        }
    
    def load_config(self) -> None:
        """
        从配置文件加载配置
        
        如果配置文件存在，则加载并合并到当前配置中；
        如果配置文件不存在，则创建默认配置文件。
        """
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    
                if user_config:
                    # 使用字典递归合并配置，用户配置会覆盖默认配置
                    self._merge_configs(self.config, user_config)
                    
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        else:
            # 如果配置文件不存在，创建默认配置文件
            self.save_config()
    
    def _merge_configs(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        递归合并两个配置字典
        
        Args:
            base: 基础配置字典，将被更新
            update: 要合并的更新配置字典
        
        注意：如果两个字典中存在相同的键，且值都是字典，则递归合并；
        否则，直接用update中的值覆盖base中的值。
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # 如果都是字典，则递归合并
                self._merge_configs(base[key], value)
            else:
                # 否则直接覆盖
                base[key] = value
    
    def save_config(self) -> None:
        """
        保存配置到文件
        
        确保配置文件所在目录存在，然后将当前配置保存到YAML文件中。
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
        
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取指定键的配置值，支持点号分隔的路径
        
        Args:
            key_path: 配置键路径，如 'api.timeout' 表示获取api配置下的timeout值
            default: 默认值，如果键不存在则返回此值
            
        Returns:
            配置值或默认值
            
        示例:
            config_manager.get('api.timeout')  # 获取API超时时间
            config_manager.get('app.window.width', 800)  # 获取窗口宽度，默认800
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key_path: 配置键路径，如 'api.timeout'
            value: 新的配置值
            
        Returns:
            bool: 是否设置成功
            
        示例:
            config_manager.set('api.timeout', 600)  # 设置API超时时间为600秒
            config_manager.set('app.language', 'zh')  # 设置应用语言为中文
        """
        keys = key_path.split('.')
        config = self.config
        
        # 导航到目标键的父级字典
        for key in keys[:-1]:
            if key not in config:
                # 如果中间键不存在，创建空字典
                config[key] = {}
            elif not isinstance(config[key], dict):
                # 如果中间键不是字典，无法设置子键
                return False
            config = config[key]
        
        # 设置最终键的值
        config[keys[-1]] = value
        return True

# 创建全局配置管理器实例，供其他模块直接使用
config_manager = ConfigManager()
