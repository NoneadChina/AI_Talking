# -*- coding: utf-8 -*-
"""
聊天列表组件，用于展示聊天历史
"""

import json
import markdown
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

from .message_widget import ChatMessageWidget


class ChatListWidget(QWidget):
    """
    聊天列表组件，用于展示聊天历史
    """

    def __init__(self):
        """
        初始化聊天列表组件
        """
        super().__init__()
        self.init_ui()

        # 连接语言变化信号
        from utils.i18n_manager import i18n

        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """
        初始化聊天列表UI
        """
        # 创建主布局
        layout = QVBoxLayout()

        # 创建聊天历史浏览器控件
        self.chat_history_view = QWebEngineView()
        self._init_web_content()

        layout.addWidget(self.chat_history_view)
        self.setLayout(layout)

    def _init_web_content(self):
        """
        初始化浏览器控件的HTML内容
        """
        initial_html = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.js"></script>
            <style>
                /* 全局样式 */
                body {
                    font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                    font-size: 13pt;
                    line-height: 1.6;
                    background-color: #f5f7fa;
                    margin: 0;
                    padding: 15px;
                }
                
                /* 消息容器 */
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
                
                /* 消息包装器 */
                .message-wrapper {
                    display: flex;
                    align-items: flex-start;
                    max-width: 75%;
                }
                
                /* 图标 */
                .icon {
                    font-size: 32px;
                    margin-right: 12px;
                    margin-top: 4px;
                    flex-shrink: 0;
                }
                
                /* 内容包装器 */
                .content-wrapper {
                    flex: 1;
                }
                
                /* 发送者信息 */
                .sender-info {
                    display: flex;
                    align-items: center;
                    margin-bottom: 8px;
                    font-size: 11pt;
                }
                
                .sender {
                    font-weight: bold;
                    margin-right: 10px;
                }
                
                .model {
                    color: #666;
                    margin-right: 10px;
                    background-color: #f0f0f0;
                    padding: 4px 12px;
                    border-radius: 16px;
                    font-size: 8pt;
                    font-weight: normal;
                }
                
                .timestamp {
                    color: #999;
                    font-size: 8pt;
                }
                
                /* 消息样式 */
                .message {
                    border-radius: 18px;
                    padding: 15px;
                    margin: 4px 0;
                    text-align: left;
                    word-wrap: break-word;
                    font-size: 12pt;
                }
                
                /* 用户消息 */
                .user-message {
                    background-color: #e8f5e8;
                    border: 1px solid #c8e6c9;
                    border-bottom-right-radius: 4px;
                }
                
                /* AI消息 */
                .ai-message {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-bottom-left-radius: 4px;
                }
                
                /* 系统消息 */
                .system-message {
                    background-color: #e3f2fd;
                    border: 1px solid #bbdefb;
                    border-radius: 12px;
                    padding: 12px;
                    margin: 15px auto;
                    text-align: center;
                    font-weight: bold;
                    max-width: 60%;
                    font-size: 11pt;
                    color: #1565c0;
                }
                
                /* 消息操作按钮 */
                .message-actions {
                    display: none;
                    margin-top: 6px;
                    margin-left: 42px;
                    gap: 8px;
                }
                
                .message-container:hover .message-actions {
                    display: flex;
                }
                
                .action-button {
                    background-color: transparent;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 9pt;
                    cursor: pointer;
                    color: #666;
                    transition: all 0.2s ease;
                }
                
                .action-button:hover {
                    background-color: #f0f0f0;
                    border-color: #bbb;
                    color: #333;
                }
                
                /* Markdown支持 */
                .message h1, .message h2, .message h3, 
                .message h4, .message h5, .message h6 {
                    margin-top: 0;
                    margin-bottom: 8px;
                    font-weight: bold;
                    line-height: 1.3;
                }
                
                .message h1 { font-size: 18pt; }
                .message h2 { font-size: 16pt; }
                .message h3 { font-size: 14pt; }
                .message h4, .message h5, .message h6 { font-size: 12pt; }
                
                .message p {
                    margin: 0 0 8px 0;
                }
                
                .message ul, .message ol {
                    margin: 0 0 8px 20px;
                    padding: 0;
                }
                
                .message li {
                    margin-bottom: 4px;
                }
                
                .message blockquote {
                    border-left: 3px solid #4caf50;
                    margin: 0 0 8px 0;
                    padding-left: 12px;
                    color: #666;
                    font-style: italic;
                }
                
                .message code {
                    background-color: rgba(0, 0, 0, 0.05);
                    padding: 2px 5px;
                    border-radius: 4px;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 11pt;
                }
                
                .message pre {
                    background-color: rgba(0, 0, 0, 0.05);
                    padding: 12px;
                    border-radius: 8px;
                    overflow-x: auto;
                    margin: 0 0 8px 0;
                }
                
                .message pre code {
                    background-color: transparent;
                    padding: 0;
                    border-radius: 0;
                }
                
                /* 进度指示器 */
                .typing-indicator {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
                
                .typing-dot {
                    width: 6px;
                    height: 6px;
                    background-color: #666;
                    border-radius: 50%;
                    animation: typing 1.4s infinite;
                }
                
                .typing-dot:nth-child(2) {
                    animation-delay: 0.2s;
                }
                
                .typing-dot:nth-child(3) {
                    animation-delay: 0.4s;
                }
                
                @keyframes typing {
                    0%, 60%, 100% {
                        transform: translateY(0);
                        opacity: 0.5;
                    }
                    30% {
                        transform: translateY(-10px);
                        opacity: 1;
                    }
                }
            </style>
        </head>
        <body id="chat-body">
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
                
                // 消息操作功能
                
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
                    // 获取当前消息的文本内容，用于编辑
                    const currentText = messageContent.innerText;
                    
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
                    quill.root.innerHTML = messageContent.innerHTML;
                    
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
                    // 为所有编辑按钮添加事件监听器（第1个按钮）
                    document.querySelectorAll('.action-button:nth-child(1)').forEach(button => {
                        button.onclick = editMessage;  // 绑定编辑消息函数
                        button.textContent = '编辑';   // 设置按钮文本
                    });
                    
                    // 为所有复制按钮添加事件监听器（第2个按钮）
                    document.querySelectorAll('.action-button:nth-child(2)').forEach(button => {
                        button.onclick = copyMessage;  // 绑定复制消息函数
                        button.textContent = '复制';   // 设置按钮文本
                    });
                    
                    // 为所有删除按钮添加事件监听器（第3个按钮）
                    document.querySelectorAll('.action-button:nth-child(3)').forEach(button => {
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
                const chatBody = document.getElementById('chat-body');
                if (chatBody) {
                    observer.observe(chatBody, config);
                }
                
                // 初始初始化
                initMessageActions();
            </script>
        </body>
        </html>
        """
        self.chat_history_view.setHtml(initial_html)

    def append_message(self, sender, content, model=""):
        """
        添加聊天消息

        Args:
            sender: 发送者
            content: 消息内容
            model: 模型名称
        """
        # 渲染消息
        message_html = ChatMessageWidget.render_message(sender, content, model)

        # 更新聊天历史
        escaped_html = json.dumps(message_html)
        rendered_content = json.dumps(markdown.markdown(content))

        # 如果是AI回复且不是"正在思考..."，则处理流式更新
        if sender == "AI" and content != "正在思考...":
            js = (
                "(function() {\n"
                "    const chatBody = document.getElementById('chat-body');\n"
                "    const messages = chatBody.querySelectorAll('.message-container');\n"
                "    let found = false;\n"
                "    \n"
                "    // 查找最后一条AI消息\n"
                "    for (let i = messages.length - 1; i >= 0; i--) {\n"
                "        const message = messages[i];\n"
                "        const messageContent = message.querySelector('.message');\n"
                "        const sender = message.querySelector('.sender');\n"
                "        \n"
                "        if (messageContent && (sender && sender.textContent === 'AI' || messageContent.textContent === '正在思考...')) {\n"
                "            // 更新现有消息内容\n"
                "            messageContent.innerHTML = " + rendered_content + ";\n"
                "            const senderInfo = message.querySelector('.sender-info');\n"
                "            if (senderInfo && '"
                + model
                + "' && !senderInfo.querySelector('.model')) {\n"
                "                senderInfo.innerHTML += '<span class=\"model\">' + '"
                + model
                + "' + '</span>';\n"
                "            }\n"
                "            found = true;\n"
                "            break;\n"
                "        }\n"
                "    }\n"
                "    \n"
                "    if (!found) {\n"
                "        chatBody.innerHTML += " + escaped_html + ";\n"
                "    }\n"
                "    \n"
                "    // 重新渲染MathJax公式\n"
                "    if (window.MathJax) {\n"
                "        MathJax.typesetPromise();\n"
                "    }\n"
                "    \n"
                "    autoScrollToBottom();\n"
                "})();"
            )
        else:
            js = (
                "document.getElementById('chat-body').innerHTML += "
                + escaped_html
                + ";\n"
                "\n"
                "// 重新渲染MathJax公式\n"
                "if (window.MathJax) {\n"
                "    MathJax.typesetPromise();\n"
                "}\n"
                "\n"
                "autoScrollToBottom();"
            )

        self.chat_history_view.page().runJavaScript(js)

    def clear(self):
        """
        清空聊天历史
        """
        # 使用JavaScript直接清空聊天内容，避免异步冲突
        js = """
        document.getElementById('chat-body').innerHTML = '';
        window.scrollTo(0, 0);
        """

        self.chat_history_view.page().runJavaScript(js)

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 重新初始化Web内容，更新翻译文本
        self._init_web_content()
