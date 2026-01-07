# -*- coding: utf-8 -*-
"""
聊天消息组件，用于渲染单个聊天消息
"""

import time
import markdown

# 导入国际化管理器
from utils.i18n_manager import i18n


class ChatMessageWidget:
    """
    聊天消息组件，用于渲染单个聊天消息
    """

    @staticmethod
    def render_message(sender, content, model="", timestamp=None):
        """
        渲染聊天消息

        Args:
            sender: 发送者
            content: 消息内容
            model: 模型名称
            timestamp: 时间戳

        Returns:
            str: 渲染后的HTML内容
        """
        if not timestamp:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # 渲染Markdown内容
        rendered_content = markdown.markdown(content)

        # 根据发送者设置不同的样式
        user_text = i18n.translate('user')
        system_text = i18n.translate('system')
        if sender.lower() == "user" or sender == user_text:
            message_class = "user-message"
            icon_char = "👤"
            sender_color = "#0d47a1"
            placement = "right"
        elif sender == system_text:
            message_class = "system-message"
            icon_char = "📢"
            sender_color = "#616161"
            placement = "center"
        else:
            message_class = "ai-message"
            icon_char = "🤖"
            sender_color = "#6a1b9a"
            placement = "left"

        # 格式化发送者信息，将模型名称包含在括号中
        sender_text = sender
        if (
            model
            and sender not in [i18n.translate("user"), i18n.translate("system")]
            and sender.lower() != "user"
        ):
            sender_text = f"{sender} ({model})"

        # 构建HTML内容
        html_content = f"<div class='message-container placement-{placement}'>"
        html_content += "<div class='message-wrapper'>"
        html_content += f"<span class='icon'>{icon_char}</span>"
        html_content += "<div class='content-wrapper'>"
        html_content += "<div class='sender-info'>"
        html_content += (
            f"<span class='sender' style='color: {sender_color};'>{sender_text}</span>"
        )
        # 只对非AI发送者显示单独的模型标签
        if model and not (
            sender not in [i18n.translate("user"), i18n.translate("system")]
            and sender.lower() != "user"
        ):
            html_content += f"<span class='model'>{model}</span>"
        html_content += f"<span class='timestamp'>{timestamp}</span>"
        html_content += "</div>"
        html_content += f"<div class='message {message_class}'>{rendered_content}</div>"
        html_content += "<div class='message-actions'>"
        html_content += (
            f"<button class='action-button'>{i18n.translate('translate')}</button>"
        )
        html_content += (
            f"<button class='action-button'>{i18n.translate('edit')}</button>"
        )
        html_content += (
            f"<button class='action-button'>{i18n.translate('copy')}</button>"
        )
        html_content += (
            f"<button class='action-button'>{i18n.translate('delete')}</button>"
        )
        html_content += "</div>"
        html_content += "</div>"
        html_content += "</div>"
        html_content += "</div>"

        return html_content
