# -*- coding: utf-8 -*-
"""
辩论功能组件，包含辩论配置、AI配置、聊天历史和控制面板
"""

from .debate_tab import DebateTabWidget
from .config_panel import DebateConfigPanel
from .ai_config_panel import AIDebateConfigPanel
from .chat_history_panel import DebateChatHistoryPanel
from .controls_panel import DebateControlsPanel

__all__ = [
    "DebateTabWidget",
    "DebateConfigPanel",
    "AIDebateConfigPanel",
    "DebateChatHistoryPanel",
    "DebateControlsPanel",
]
