# -*- coding: utf-8 -*-
"""
辩论聊天历史面板组件，用于显示辩论历史记录
"""

import time
import json
import markdown
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ui.ui_utils import create_group_box, get_default_styles
from utils.logger_config import get_logger
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class DebateChatHistoryPanel(QWidget):
    """
    辩论聊天历史面板组件

    属性:
        debate_history_text: 聊天历史显示区域
    """

    def __init__(self):
        """初始化辩论聊天历史面板"""
        super().__init__()
        self.styles = get_default_styles()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 辩论历史区域
        self.history_group = create_group_box(
            i18n.translate("debate_history"), self.styles["group_box"]
        )
        history_layout = QVBoxLayout()
        history_layout.setContentsMargins(10, 5, 10, 10)

        # 初始化聊天历史显示区域
        self.debate_history_text = QWebEngineView()
        self._init_web_content()

        history_layout.addWidget(self.debate_history_text)
        self.history_group.setLayout(history_layout)
        layout.addWidget(self.history_group)

        self.setLayout(layout)

    def _init_web_content(self):
        """
        初始化浏览器控件的HTML内容
        """
        initial_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.js"></script>
            <style>
                body {
                    font-family: SimHei, Arial, sans-serif;
                    font-size: 13pt;
                    background-color: #fafafa;
                    margin: 0;
                    padding: 10px;
                }
                .message-container {
                    margin-bottom: 20px;
                    position: relative;
                    display: flex;
                }
                .placement-right {
                    justify-content: flex-end;
                }
                .placement-left {
                    justify-content: flex-start;
                }
                .placement-center {
                    justify-content: center;
                }
                .message-wrapper {
                    display: flex;
                    align-items: flex-start;
                    max-width: 80%;
                }
                .icon {
                    font-size: 36px;
                    margin-right: 14px;
                    margin-top: 4px;
                    flex-shrink: 0;
                }
                .content-wrapper {
                    flex: 1;
                }
                .sender-info {
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                    font-size: 16px;
                }
                .sender {
                    font-weight: bold;
                    margin-right: 14px;
                }
                .timestamp {
                    color: #999;
                }
                .message {
                    border-radius: 20px;
                padding: 18px;
                margin: 5px 0;
                text-align: left;
                word-wrap: break-word;
                font-size: 13pt;
                }
                .pro-message {
                    background-color: #e8f5e8;
                    border: 2px solid #4caf50;
                    margin: 5px 10px 5px 10px;
                }
                .con-message {
                    background-color: #ffebee;
                    border: 2px solid #f44336;
                    margin: 5px 10px 5px 10px;
                }
                .judge-message {
                    background-color: #e3f2fd;
                    border: 2px solid #1565c0;
                    margin: 5px 10px 5px 10px;
                }
                .system-message {
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0e0;
                    border-radius: 12px;
                    padding: 14px 20px;
                    margin: 12px auto;
                    text-align: center;
                    font-weight: bold;
                    white-space: nowrap;
                    max-width: none;
                    min-width: 200px;
                    font-size: 13pt;
                }
                .message-actions {
                    display: none;
                    margin-top: 5px;
                    margin-left: 45px;
                }
                .message-container:hover .message-actions {
                    display: flex;
                    gap: 10px;
                }
                .action-button {
                    background-color: transparent;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 16px;
                    cursor: pointer;
                    color: #666;
                }
                .action-button:hover {
                    background-color: #f0f0f0;
                }
            </style>
        </head>
        <body id="debate-body">
            <script>
                // 智能滚动控制变量
                let autoScrollEnabled = true;
                const SCROLL_TOLERANCE = 10;
                
                // 检查是否在底部附近
                function isNearBottom() {
                    const scrollPosition = window.scrollY + window.innerHeight;
                    const documentHeight = document.body.scrollHeight;
                    return scrollPosition >= documentHeight - SCROLL_TOLERANCE;
                }
                
                // 自动滚动到底部（如果启用）
                function autoScrollToBottom() {
                    if (autoScrollEnabled) {
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                }
                
                // 监听滚动事件，控制自动滚动状态
                window.addEventListener('scroll', function() {
                    // 如果不在底部附近，禁用自动滚动
                    if (!isNearBottom()) {
                        autoScrollEnabled = false;
                    } else {
                        // 如果回到底部附近，启用自动滚动
                        autoScrollEnabled = true;
                    }
                });
                
                // 初始化时启用自动滚动
            autoScrollEnabled = true;
        </script>
        <script>
            // 复制消息内容到剪贴板
            function copyMessage(event) {
                // 找到包含消息内容的元素
                const messageContainer = event.target.closest('.message-container');
                if (messageContainer) {
                    const messageContent = messageContainer.querySelector('.message');
                    if (messageContent) {
                        // 获取纯文本内容
                        const textContent = messageContent.innerText;
                        
                        // 复制到剪贴板，使用兼容方案
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            // 现代浏览器方案
                            navigator.clipboard.writeText(textContent).then(function() {
                                // 显示复制成功提示
                                showMessage('复制成功');
                            }).catch(function(err) {
                                console.error('复制失败:', err);
                                // 使用传统方案作为备选
                                fallbackCopyTextToClipboard(textContent);
                            });
                        } else {
                            // 传统方案作为备选
                            fallbackCopyTextToClipboard(textContent);
                        }
                    }
                }
                event.stopPropagation();
            }
            
            // 传统复制方案，作为剪贴板 API 的备选
            function fallbackCopyTextToClipboard(text) {
                try {
                    // 创建临时 textarea 元素
                    const textArea = document.createElement('textarea');
                    textArea.value = text;
                    textArea.style.top = '0';
                    textArea.style.left = '0';
                    textArea.style.position = 'fixed';
                    textArea.style.opacity = '0';
                    
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    
                    // 执行复制命令
                    const successful = document.execCommand('copy');
                    
                    // 清理临时元素
                    document.body.removeChild(textArea);
                    
                    // 显示结果提示
                    if (successful) {
                        showMessage('复制成功');
                    } else {
                        showMessage('复制失败');
                    }
                } catch (err) {
                    console.error('复制失败:', err);
                    showMessage('复制失败');
                }
            }
            
            // 删除消息
            function deleteMessage(event) {
                // 找到消息容器
                const messageContainer = event.target.closest('.message-container');
                if (messageContainer) {
                    // 确认删除
                    if (confirm('确定要删除这条消息吗？')) {
                        // 从DOM中删除消息
                        messageContainer.remove();
                        
                        // 显示删除成功提示
                        showMessage('删除成功');
                    }
                }
                event.stopPropagation();
            }
            
            /**
         * 编辑消息内容函数
         * 当用户点击编辑按钮时触发，弹出模态对话框让用户编辑消息内容
         * @param {Event} event - 点击事件对象
         */
        function editMessage(event) {
            // 阻止事件冒泡，避免影响其他元素
            event.stopPropagation();
            
            // 找到当前点击按钮对应的消息容器
            const messageContainer = event.target.closest('.message-container');
            if (messageContainer) {
                // 获取消息内容元素
                const messageContent = messageContainer.querySelector('.message');
                if (messageContent) {
                    // 获取当前消息的HTML内容，用于编辑
                    const currentHTML = messageContent.innerHTML;
                    
                    // 创建模态对话框容器，用于覆盖整个页面
                    const modal = document.createElement('div');
                    modal.style.cssText = `
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background-color: rgba(0, 0, 0, 0.5);
                        z-index: 2000;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    `;
                    
                    // 创建对话框内容容器
                    const modalContent = document.createElement('div');
                    modalContent.style.cssText = `
                        background-color: white;
                        padding: 20px;
                        border-radius: 12px;
                        width: 80%;
                        max-width: 800px;
                        max-height: 80%;
                        overflow-y: auto;
                    `;
                    
                    // 创建对话框标题
                    const title = document.createElement('h3');
                    title.textContent = '请输入编辑后的内容:';
                    title.style.cssText = 'margin-top: 0; margin-bottom: 15px; font-size: 18px;';
                    modalContent.appendChild(title);
                    
                    // 创建Quill编辑器容器
                    const editorContainer = document.createElement('div');
                    editorContainer.style.cssText = `
                        margin-bottom: 15px;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    `;
                    modalContent.appendChild(editorContainer);
                    
                    // 创建工具栏容器
                    const toolbarContainer = document.createElement('div');
                    toolbarContainer.style.cssText = `
                        background-color: #f9fafb;
                        border-bottom: 1px solid #e5e7eb;
                        padding: 8px;
                        border-radius: 8px 8px 0 0;
                    `;
                    editorContainer.appendChild(toolbarContainer);
                    
                    // 创建编辑器内容容器
                    const editorContent = document.createElement('div');
                    editorContent.style.cssText = `
                        height: 250px;
                        overflow-y: auto;
                    `;
                    editorContainer.appendChild(editorContent);
                    
                    // 初始化Quill编辑器
                    const quill = new Quill(editorContent, {
                        theme: 'snow',
                        modules: {
                            toolbar: {
                                container: toolbarContainer,
                                handlers: {}
                            }
                        },
                        placeholder: '请输入内容...',
                    });
                    
                    // 设置初始内容
                    quill.root.innerHTML = currentHTML;
                    
                    // 创建按钮容器，用于放置取消和保存按钮
                    const buttonContainer = document.createElement('div');
                    buttonContainer.style.cssText = 'display: flex; justify-content: flex-end; gap: 10px;';
                    modalContent.appendChild(buttonContainer);
                    
                    // 创建取消按钮
                    const cancelButton = document.createElement('button');
                    cancelButton.textContent = '取消';
                    cancelButton.style.cssText = `
                        padding: 8px 16px;
                        background-color: #f0f0f0;
                        border: 1px solid #ddd;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: all 0.2s ease;
                    `;
                    // 取消按钮点击事件：关闭模态对话框
                    cancelButton.onclick = function() {
                        document.body.removeChild(modal);
                    };
                    buttonContainer.appendChild(cancelButton);
                    
                    // 创建保存按钮
                    const saveButton = document.createElement('button');
                    saveButton.textContent = '保存';
                    saveButton.style.cssText = `
                        padding: 8px 16px;
                        background-color: #2196f3;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: all 0.2s ease;
                    `;
                    // 保存按钮点击事件：更新消息内容
                    saveButton.onclick = function() {
                        // 获取编辑器中的新内容
                        const newHTML = quill.root.innerHTML;
                        // 检查内容是否为空
                        if (newHTML.trim() !== '') {
                            // 更新原消息内容
                            messageContent.innerHTML = newHTML;
                            
                            // 显示编辑成功提示
                            showMessage('编辑成功');
                            
                            // 关闭模态对话框
                            document.body.removeChild(modal);
                        }
                    };
                    buttonContainer.appendChild(saveButton);
                    
                    // 将对话框内容添加到模态容器中
                    modal.appendChild(modalContent);
                    // 将模态容器添加到文档中
                    document.body.appendChild(modal);
                }
            }
        }
            
            // 显示临时消息提示
            function showMessage(text) {
                // 创建提示元素
                const messageDiv = document.createElement('div');
                messageDiv.textContent = text;
                messageDiv.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background-color: rgba(0, 0, 0, 0.7);
                    color: white;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    z-index: 1000;
                    animation: fadeInOut 2s ease-in-out;
                `;
                
                // 添加动画样式
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes fadeInOut {
                        0% { opacity: 0; }
                        20% { opacity: 1; }
                        80% { opacity: 1; }
                        100% { opacity: 0; }
                    }
                `;
                document.head.appendChild(style);
                
                // 添加到文档
                document.body.appendChild(messageDiv);
                
                // 2秒后移除
                setTimeout(() => {
                    messageDiv.remove();
                    style.remove();
                }, 2000);
            }
            
            /**
             * 初始化消息操作按钮事件函数
             * 为所有消息操作按钮添加事件监听器，包括编辑、复制和删除按钮
             * 当DOM发生变化时，会重新调用此函数为新添加的按钮添加事件监听
             */
            function initMessageActions() {
                // 为所有编辑按钮添加事件监听器
                document.querySelectorAll('.action-button.edit-btn').forEach(button => {
                    button.onclick = editMessage;  // 绑定编辑消息函数
                    button.textContent = '编辑';   // 设置按钮文本
                });
                
                // 为所有复制按钮添加事件监听器
                document.querySelectorAll('.action-button.copy-btn').forEach(button => {
                    button.onclick = copyMessage;  // 绑定复制消息函数
                    button.textContent = '复制';   // 设置按钮文本
                });
                
                // 为所有删除按钮添加事件监听器
                document.querySelectorAll('.action-button.delete-btn').forEach(button => {
                    button.onclick = deleteMessage;  // 绑定删除消息函数
                    button.textContent = '删除';     // 设置按钮文本
                });
            }
            
            // 监听DOM变化，为新添加的消息按钮添加事件
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        initMessageActions();
                    }
                });
            });
            
            // 配置观察器
            const config = {
                childList: true,
                subtree: true
            };
            
            // 开始观察
            const chatBody = document.getElementById('debate-body');
            if (chatBody) {
                observer.observe(chatBody, config);
            }
            
            // 初始初始化
            initMessageActions();
        </script>
        </body>
        </html>
        """
        self.debate_history_text.setHtml(initial_html)

    def append_to_debate_history(self, sender, content=""):
        """
        将消息添加到辩论历史中

        Args:
            sender: 发送者(用户, AI或系统)
            content: 消息内容
        """
        # 获取当前时间戳
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # 渲染Markdown内容
        rendered_content = self._render_markdown_content(content)

        # 根据发送者设置不同的样式和位置
        if sender == "系统":
            # 系统消息样式
            message_class = "system-message"
            icon_char = "📢"
            sender_color = "#616161"
            placement = "center"
        else:
            # AI消息样式
            if sender.startswith("正方"):
                message_class = "pro-message"
                sender_color = "#2e7d32"
                placement = "right"
            elif sender.startswith("反方"):
                message_class = "con-message"
                sender_color = "#c62828"
                placement = "left"
            elif sender.startswith("专家AI3") or sender.startswith("裁判AI3"):
                message_class = "judge-message"
                sender_color = "#1565c0"
                placement = "center"

        # 构建HTML内容
        html_content = f"<div class='message-container placement-{placement}'>"
        html_content += "<div class='message-wrapper'>"
        html_content += f"<span class='icon'>{icon_char}</span>"
        html_content += "<div class='content-wrapper'>"
        html_content += "<div class='sender-info'>"
        html_content += (
            f"<span class='sender' style='color: {sender_color};'>{sender}</span>"
        )
        html_content += f"<span class='timestamp'>{timestamp}</span>"
        html_content += "</div>"
        if content:
            html_content += (
                f"<div class='message {message_class}'>{rendered_content}</div>"
            )
        html_content += "<div class='message-actions'>"
        html_content += "<button class='action-button edit-btn'>编辑</button>"
        html_content += "<button class='action-button copy-btn'>复制</button>"
        html_content += "<button class='action-button delete-btn'>删除</button>"
        html_content += "</div>"
        html_content += "</div>"
        html_content += "</div>"
        html_content += "</div>"

        # 更新聊天历史
        escaped_html = json.dumps(html_content)
        rendered_content_js = json.dumps(rendered_content)

        # 构建JavaScript代码，添加MathJax渲染
        js = (
            "(function() {\n"
            "    const chatBody = document.getElementById('debate-body');\n"
            "    chatBody.innerHTML += " + escaped_html + ";\n"
            "    \n"
            "    // 重新渲染MathJax公式\n"
            "    if (window.MathJax) {\n"
            "        MathJax.typesetPromise();\n"
            "    }\n"
            "    \n"
            "    autoScrollToBottom();\n"
            "})();"
        )

        self.debate_history_text.page().runJavaScript(js)

    def on_stream_update(self, sender, chunk, model_name):
        """
        处理流式更新信号

        Args:
            sender: 发送者
            chunk: 流式输出的内容块
            model_name: 模型名称
        """
        # 渲染Markdown内容
        rendered_content = self._render_markdown_content(chunk)

        # 更新聊天历史
        rendered_content_js = json.dumps(rendered_content)

        # 根据发送者设置不同的样式和位置
        if sender.startswith("正方"):
            message_class = "pro-message"
            placement = "right"  # 正方AI1的输出气泡靠右侧
            sender_color = "#2e7d32"
        elif sender.startswith("反方"):
            message_class = "con-message"
            placement = "left"  # 反方AI2的输出气泡靠左侧
            sender_color = "#c62828"
        elif sender.startswith("专家AI3") or sender.startswith("裁判AI3"):
            message_class = "judge-message"
            placement = "center"  # 裁判AI3的输出气泡居中
            sender_color = "#1565c0"

        # 构建HTML内容
        message_html = f"<div class='message-container placement-{placement}'>"
        message_html += "<div class='message-wrapper'>"
        message_html += "<span class='icon'>🤖</span>"
        message_html += "<div class='content-wrapper'>"
        message_html += "<div class='sender-info'>"
        message_html += (
            f"<span class='sender' style='color: {sender_color};'>{sender}</span>"
        )
        message_html += (
            f"<span class='timestamp'>{time.strftime('%Y-%m-%d %H:%M:%S')}</span>"
        )
        message_html += "</div>"
        message_html += f"<div class='message {message_class}'>{rendered_content}</div>"
        message_html += "<div class='message-actions'>"
        message_html += "<button class='action-button edit-btn'>编辑</button>"
        message_html += "<button class='action-button copy-btn'>复制</button>"
        message_html += "<button class='action-button delete-btn'>删除</button>"
        message_html += "</div>"
        message_html += "</div>"
        message_html += "</div>"
        message_html += "</div>"

        escaped_html = json.dumps(message_html)

        # 同一轮辩论中更新最后一条相同AI的消息，新一轮辩论时创建新消息
        js = (
            "(function() {\n"
            "    const chatBody = document.getElementById('debate-body');\n"
            "    const messages = chatBody.querySelectorAll('.message-container');\n"
            "    let found = false;\n"
            "    let lastAiMessage = null;\n"
            "    let lastAiMessageIndex = -1;\n"
            "    \n"
            "    // 1. 查找最后一条对应AI的消息\n"
            "    for (let i = messages.length - 1; i >= 0; i--) {\n"
            "        const message = messages[i];\n"
            "        const sender = message.querySelector('.sender');\n"
            "        if (sender && sender.textContent === '" + sender + "') {\n"
            "            lastAiMessage = message;\n"
            "            lastAiMessageIndex = i;\n"
            "            break;\n"
            "        }\n"
            "    }\n"
            "    \n"
            "    // 2. 检查是否有新的轮次提示在这条AI消息之后\n"
            "    let isSameRound = true;\n"
            "    if (lastAiMessage) {\n"
            "        for (let i = lastAiMessageIndex + 1; i < messages.length; i++) {\n"
            "            const message = messages[i];\n"
            "            const messageContent = message.querySelector('.message');\n"
            "            if (messageContent) {\n"
            "                const content = messageContent.textContent || messageContent.innerText;\n"
            "                // 检查是否是轮次提示\n"
            "                if (content && content.startsWith('=== 第 ') && content.endsWith('轮辩论 ===')) {\n"
            "                    isSameRound = false;\n"
            "                    break;\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "    \n"
            "    // 3. 根据检查结果决定是更新还是添加新消息\n"
            "    if (lastAiMessage && isSameRound) {\n"
            "        // 同一轮，更新现有消息\n"
            "        const messageContent = lastAiMessage.querySelector('.message');\n"
            "        if (messageContent) {\n"
            "            messageContent.innerHTML = " + rendered_content_js + ";\n"
            "            // 重新渲染MathJax公式\n"
            "            if (window.MathJax) {\n"
            "                MathJax.typesetPromise();\n"
            "            }\n"
            "        }\n"
            "    } else {\n"
            "        // 新一轮，添加新消息\n"
            "        chatBody.innerHTML += " + escaped_html + ";\n"
            "        // 重新渲染MathJax公式\n"
            "        if (window.MathJax) {\n"
            "            MathJax.typesetPromise();\n"
            "        }\n"
            "    }\n"
            "    \n"
            "    // 滚动到底部\n"
            "    autoScrollToBottom();\n"
            "})();"
        )

        self.debate_history_text.page().runJavaScript(js)

    def _render_markdown_content(self, content):
        """
        将Markdown内容渲染为HTML

        Args:
            content: Markdown格式的内容

        Returns:
            str: HTML格式的内容
        """
        try:
            return markdown.markdown(content)
        except Exception as e:
            logger.error(f"Markdown渲染失败: {str(e)}")
            return content

    def clear(self):
        """
        清空聊天历史
        """
        # 使用JavaScript直接清空聊天内容，包装在IIFE中避免变量重复声明
        js = """
        (function() {
            const chatBody = document.getElementById('debate-body');
            if (chatBody) {
                chatBody.innerHTML = '';
            }
            window.scrollTo(0, 0);
        })();
        """

        self.debate_history_text.page().runJavaScript(js)

    def clear_debate_history(self):
        """
        清空辩论历史
        """
        self.clear()

    def get_html_content(self, callback):
        """
        获取当前HTML内容

        Args:
            callback: 回调函数，用于处理HTML内容
        """
        self.debate_history_text.page().toHtml(callback)

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新历史组标题
        self.history_group.setTitle(i18n.translate("debate_history"))

        # 保存当前聊天内容
        current_content = None

        def save_content(html):
            nonlocal current_content
            current_content = html

        # 获取当前内容
        self.debate_history_text.page().toHtml(save_content)

        # 重新初始化web内容，更新HTML中的翻译文本
        self._init_web_content()

        # 如果有保存的内容，恢复它
        if current_content:

            def restore_content(html):
                # 找到body标签的开始和结束位置
                body_start = html.find("<body")
                if body_start != -1:
                    body_end = html.find(">", body_start) + 1
                    body_close = html.rfind("</body>")
                    if body_close != -1:
                        # 构建新的HTML，保留头部，替换body内容
                        new_html = (
                            html[:body_end]
                            + current_content[body_end:body_close]
                            + html[body_close:]
                        )
                        self.debate_history_text.setHtml(new_html)
                        # 显式调用initMessageActions()重新绑定按钮事件
                        self.debate_history_text.page().runJavaScript("initMessageActions();")

            # 先获取新初始化的HTML结构
            self.debate_history_text.page().toHtml(restore_content)
