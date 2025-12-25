# -*- coding: utf-8 -*-
"""
讨论模块，包含讨论标签页的各个子组件
"""

# 导出主要组件
from .discussion_tab import DiscussionTabWidget
from .config_panel import ConfigPanel
from .ai_config_panel import AIConfigPanel
from .chat_history_panel import ChatHistoryPanel
from .controls_panel import ControlsPanel

__all__ = [
    "DiscussionTabWidget",
    "ConfigPanel",
    "AIConfigPanel",
    "ChatHistoryPanel",
    "ControlsPanel",
]
