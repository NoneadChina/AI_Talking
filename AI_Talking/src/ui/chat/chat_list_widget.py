# -*- coding: utf-8 -*-
"""
聊天列表组件，用于展示聊天历史
"""

import json
import markdown
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot

from utils.i18n_manager import i18n
from .message_widget import ChatMessageWidget


class TranslationHandler(QObject):
    """
    翻译请求处理类，用于处理来自JavaScript的翻译请求
    """
    def __init__(self, chat_list_widget):
        super().__init__()
        self.chat_list_widget = chat_list_widget
    
    @pyqtSlot(str, str, str, str)
    def handle_translation_request(self, text, source_lang, target_lang, callback_id):
        """
        处理来自JavaScript的翻译请求
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言代码
            target_lang: 目标语言代码
            callback_id: JavaScript回调ID，用于返回翻译结果
        """
        self.chat_list_widget.handle_translation_request(text, source_lang, target_lang, callback_id)

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
        
        # 初始化QWebChannel
        self.channel = QWebChannel()
        self.translation_handler = TranslationHandler(self)
        self.channel.registerObject('translationHandler', self.translation_handler)
        self.chat_history_view.page().setWebChannel(self.channel)

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """
        初始化聊天列表UI
        """
        # 创建主布局
        layout = QVBoxLayout()

        # 创建聊天历史浏览器控件
        self.chat_history_view = QWebEngineView()
        # 禁用右键菜单
        from PyQt5.QtCore import Qt
        self.chat_history_view.setContextMenuPolicy(Qt.NoContextMenu)
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
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
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
                    overflow-x: hidden;
                    width: 100%;
                    box-sizing: border-box;
                }
                
                /* 图片样式 */
                .message img {
                    max-width: 300px;
                    height: auto;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
                
                /* 点击放大后的图片样式 */
                .message img.zoomed {
                    max-width: 100%;
                    max-height: 80vh;
                    position: relative;
                    z-index: 100;
                    border: 2px solid #4caf50;
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
                    margin-left: 0;
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
                // 智能滚动控制变量 - 暴露到全局作用域
                window.autoScrollEnabled = true;
                window.SCROLL_TOLERANCE = 10;
                
                // 检查是否在底部附近 - 暴露到全局作用域
                window.isNearBottom = function() {
                    const scrollPosition = window.scrollY + window.innerHeight;
                    const documentHeight = document.body.scrollHeight;
                    return scrollPosition >= documentHeight - window.SCROLL_TOLERANCE;
                };
                
                // 自动滚动到底部（如果启用） - 暴露到全局作用域
                window.autoScrollToBottom = function() {
                    if (window.autoScrollEnabled) {
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                };
                
                // 监听滚动事件，控制自动滚动状态
                window.addEventListener('scroll', function() {
                    // 如果不在底部附近，禁用自动滚动
                    if (!window.isNearBottom()) {
                        window.autoScrollEnabled = false;
                    } else {
                        // 如果回到底部附近，启用自动滚动
                        window.autoScrollEnabled = true;
                    }
                });
                
                // 初始化QWebChannel
                window.translationHandler = null;
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.translationHandler = channel.objects.translationHandler;
                    // QWebChannel初始化完成后，重新初始化消息操作按钮
                    // 确保translationHandler已准备好
                    setTimeout(function() {
                        if (typeof initMessageActions === 'function') {
                            initMessageActions();
                        }
                    }, 100);
                });
                
                // 初始化时启用自动滚动
                window.autoScrollEnabled = true;
                
                // 图片点击缩放功能
                // 使用事件委托处理所有图片点击事件，包括动态添加的图片
                document.addEventListener('click', function(event) {
                    if (event.target.tagName === 'IMG') {
                        // 切换图片的zoomed类，实现缩放效果
                        event.target.classList.toggle('zoomed');
                        // 阻止事件冒泡，避免触发其他事件
                        event.stopPropagation();
                    }
                });
                
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
                    
                    // 找到按钮元素，即使event.target是按钮的子元素
                    const button = event.target.closest('.action-button');
                    if (!button) {
                        console.error('无法找到按钮元素');
                        return;
                    }
                    
                    // 找到当前点击按钮对应的消息容器
                    const messageContainer = button.closest('.message-container');
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
                            title.textContent = window.i18n_texts.edit_content;
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
                            
                            // 设置初始内容，使用setText方法确保纯文本内容正确显示
                            quill.setText(currentText);
                            
                            // 创建按钮容器，用于放置取消和保存按钮
                            const buttonContainer = document.createElement('div');
                            buttonContainer.style.cssText = 'display: flex; justify-content: flex-end; gap: 10px;';
                            modalContent.appendChild(buttonContainer);
                            
                            // 创建取消按钮
                            const cancelButton = document.createElement('button');
                            cancelButton.textContent = window.i18n_texts.cancel;
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
                            saveButton.textContent = window.i18n_texts.save;
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
                                // 获取编辑器中的新内容，使用text方法获取纯文本
                                const newText = quill.getText();
                                // 检查内容是否为空
                                if (newText.trim() !== '') {
                                    // 更新原消息内容，直接设置文本内容
                                    messageContent.innerText = newText;
                                    
                                    // 显示编辑成功提示
                                showMessage(window.i18n_texts.edit_success);
                                    
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
                
                // 检测文本语言
                function detectLanguage(text) {
                    // 简单的语言检测逻辑，基于字符范围和关键词
                    // 实际项目中应使用更专业的语言检测库
                    if (/[\u4e00-\u9fa5]/.test(text)) {
                        // 包含中文字符
                        return 'zh-CN';
                    } else if (/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]/.test(text)) {
                        // 包含日文字符
                        return 'ja';
                    } else if (/[\uac00-\ud7af]/.test(text)) {
                        // 包含韩文字符
                        return 'ko';
                    } else if (/[\u0600-\u06ff]/.test(text)) {
                        // 包含阿拉伯文字符
                        return 'ar';
                    } else if (/[\u0400-\u04ff]/.test(text)) {
                        // 包含俄文字符
                        return 'ru';
                    } else if (/[a-zA-Z]/.test(text)) {
                        // 包含英文字符
                        return 'en';
                    } else if (/[\u00c0-\u017f]/.test(text)) {
                        // 包含拉丁字符（德语、西班牙语、法语等）
                        // 简单区分，实际项目中需要更精确的检测
                        if (/\b(der|die|das|ein|eine)\b/i.test(text)) {
                            return 'de';
                        } else if (/\b(el|la|los|las|un|una)\b/i.test(text)) {
                            return 'es';
                        } else if (/\b(le|la|les|un|une)\b/i.test(text)) {
                            return 'fr';
                        } else {
                            return 'en';
                        }
                    } else {
                        // 默认返回英文
                        return 'en';
                    }
                }
                
                // 显示翻译语言选择菜单
                function showTranslateMenu(event) {
                    // 阻止事件冒泡
                    event.stopPropagation();
                    
                    // 移除已存在的翻译菜单
                    const existingMenu = document.querySelector('.translate-menu');
                    if (existingMenu) {
                        existingMenu.remove();
                    }
                    
                    // 获取当前按钮和消息容器
                    const button = event.target;
                    const messageContainer = button.closest('.message-container');
                    if (!messageContainer) return;
                    
                    // 获取消息内容
                    const messageContent = messageContainer.querySelector('.message');
                    if (!messageContent) return;
                    
                    // 检测源语言
                    const sourceText = messageContent.innerText;
                    const sourceLang = detectLanguage(sourceText);
                    
                    // 支持的语言列表，使用固定语言名称
                const languages = {
                    'zh-CN': '简体中文',
                    'zh-TW': '繁体中文',
                    'en': '英语',
                    'ja': '日本語',
                    'ko': '한국어',
                    'de': 'Deutsch',
                    'es': 'Español',
                    'fr': 'Français',
                    'ar': 'العربية',
                    'ru': 'Русский'
                };
                    
                    // 创建翻译菜单
                    const menu = document.createElement('div');
                    menu.className = 'translate-menu';
                    menu.style.cssText = `
                        position: absolute;
                        background-color: white;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                        z-index: 2000;
                        min-width: 120px;
                        max-height: 300px;
                        overflow-y: auto;
                    `;
                    
                    // 获取按钮位置
                    const buttonRect = button.getBoundingClientRect();
                    const chatBody = document.getElementById('chat-body');
                    const chatRect = chatBody.getBoundingClientRect();
                    
                    // 计算菜单位置
                    menu.style.left = `${buttonRect.left - chatRect.left}px`;
                    menu.style.top = `${buttonRect.bottom - chatRect.top}px`;
                    
                    // 添加语言选项，跳过源语言
                    Object.entries(languages).forEach(([code, name]) => {
                        // 跳过源语言
                        if (code === sourceLang) {
                            return;
                        }
                        
                        const option = document.createElement('div');
                        option.className = 'translate-option';
                        option.textContent = name;
                        option.dataset.langCode = code;
                        option.style.cssText = `
                            padding: 8px 12px;
                            cursor: pointer;
                            font-size: 14px;
                            transition: background-color 0.2s;
                        `;
                        
                        // 添加悬停效果
                        option.addEventListener('mouseenter', () => {
                            option.style.backgroundColor = '#f5f5f5';
                        });
                        
                        option.addEventListener('mouseleave', () => {
                            option.style.backgroundColor = 'white';
                        });
                        
                        // 添加点击事件
                        option.addEventListener('click', () => {
                            translateMessage(messageContainer, sourceLang, code, name);
                            menu.remove();
                        });
                        
                        menu.appendChild(option);
                    });
                    
                    // 添加到消息容器
                    chatBody.appendChild(menu);
                    
                    // 点击其他地方关闭菜单
                    document.addEventListener('click', function closeMenu(e) {
                        if (!menu.contains(e.target) && e.target !== button) {
                            menu.remove();
                            document.removeEventListener('click', closeMenu);
                        }
                    });
                }
                
                // 翻译请求计数器，用于生成唯一的回调ID
                let translationRequestId = 0;
                
                // 翻译请求队列，存储待处理的翻译请求
                const translationRequests = new Map();
                
                // 执行消息翻译
                function translateMessage(messageContainer, sourceLangCode, targetLangCode, targetLangName) {
                    // 获取消息内容
                    const messageContent = messageContainer.querySelector('.message');
                    if (!messageContent) return;
                    
                    const textToTranslate = messageContent.innerText;
                    
                    // 显示加载状态
                    const button = messageContainer.querySelector('.action-button:nth-child(1)');
                    if (button) {
                        const originalText = button.textContent;
                        button.textContent = window.i18n_texts.translating;
                        button.disabled = true;
                    }
                    
                    // 创建加载中的翻译气泡
                    const loadingBubble = createLoadingBubble(messageContainer, targetLangName);
                    
                    // 生成唯一的回调ID
                    const requestId = 'trans_' + (translationRequestId++);
                    
                    // 存储翻译请求信息
                    translationRequests.set(requestId, {
                        messageContainer: messageContainer,
                        loadingBubble: loadingBubble,
                        button: button,
                        targetLangName: targetLangName,
                        targetLangCode: targetLangCode,
                        sourceLangCode: sourceLangCode
                    });
                    
                    // 调用Python的翻译方法
                    // 多次检查translationHandler，确保它已初始化
                    function tryCallTranslation() {
                        if (window.translationHandler && window.translationHandler.handle_translation_request) {
                            window.translationHandler.handle_translation_request(textToTranslate, sourceLangCode, targetLangCode, requestId);
                        } else {
                            // 如果handler还没准备好，等待一小段时间后重试
                            setTimeout(tryCallTranslation, 50);
                        }
                    }
                    
                    // 延迟调用翻译方法，确保QWebChannel已初始化
                    setTimeout(tryCallTranslation, 100);
                }
                
                // 处理翻译结果
                window.handleTranslationResult = function(translatedText, targetLang, requestId) {
                    // 获取翻译请求信息
                    const request = translationRequests.get(requestId);
                    if (!request) return;
                    
                    try {
                        // 移除加载气泡
                        if (request.loadingBubble) {
                            request.loadingBubble.remove();
                        }
                        
                        // 支持的语言名称映射
                        const languageNames = {
                            'zh-CN': '简体中文',
                            'zh-TW': '繁体中文',
                            'en': '英语',
                            'ja': '日语',
                            'ko': '韩语',
                            'de': '德语',
                            'es': '西班牙语',
                            'fr': '法语',
                            'ar': '阿拉伯语',
                            'ru': '俄语'
                        };
                        
                        // 获取目标语言名称
                        const targetLangName = languageNames[targetLang] || targetLang;
                        
                        // 创建新的翻译气泡
                        createTranslationBubble(
                            request.messageContainer, 
                            translatedText, 
                            targetLangName, 
                            targetLang, 
                            request.sourceLangCode
                        );
                    } catch (error) {
                        // 显示错误信息
                        showMessage('翻译结果处理失败: ' + error.message);
                    } finally {
                        // 恢复按钮状态
                        if (request.button) {
                            request.button.textContent = '翻译';
                            request.button.disabled = false;
                        }
                        
                        // 从请求队列中移除
                        translationRequests.delete(requestId);
                    }
                };
                
                // 处理翻译失败
                window.handleTranslationError = function(error, requestId) {
                    // 获取翻译请求信息
                    const request = translationRequests.get(requestId);
                    if (!request) return;
                    
                    try {
                        // 移除加载气泡
                        if (request.loadingBubble) {
                            request.loadingBubble.remove();
                        }
                        
                        // 显示错误信息
                        showMessage('翻译失败: ' + error);
                    } catch (innerError) {
                        console.error('处理翻译错误时发生错误:', innerError);
                    } finally {
                        // 恢复按钮状态
                        if (request.button) {
                            request.button.textContent = '翻译';
                            request.button.disabled = false;
                        }
                        
                        // 从请求队列中移除
                        translationRequests.delete(requestId);
                    }
                };
                
                // 创建加载中的翻译气泡
                function createLoadingBubble(originalContainer, targetLangName) {
                    const chatBody = document.getElementById('chat-body');
                    
                    // 获取原气泡的位置类（placement-left, placement-right, placement-center）
                    let placementClass = 'placement-left';
                    if (originalContainer.classList.contains('placement-right')) {
                        placementClass = 'placement-right';
                    } else if (originalContainer.classList.contains('placement-center')) {
                        placementClass = 'placement-center';
                    }
                    
                    // 获取原气泡的消息样式类（user-message, ai-message, system-message）
                    let messageClass = 'ai-message';
                    const originalMessage = originalContainer.querySelector('.message');
                    if (originalMessage) {
                        if (originalMessage.classList.contains('user-message')) {
                            messageClass = 'user-message';
                        } else if (originalMessage.classList.contains('system-message')) {
                            messageClass = 'system-message';
                        }
                    }
                    
                    // 创建加载气泡
                    const loadingContainer = document.createElement('div');
                    loadingContainer.className = `message-container ${placementClass}`;
                    loadingContainer.style.cssText = `
                        margin-top: 10px;
                    `;
                    
                    // 构建加载气泡HTML
                    loadingContainer.innerHTML = `
                        <div class="message-wrapper">
                            <span class="icon">🌐</span>
                            <div class="content-wrapper">
                                <div class="sender-info">
                                    <span class="sender" style="color: #009688;">${window.i18n_texts.translation_result} (${targetLangName})</span>
                                    <span class="timestamp">${new Date().toLocaleString()}</span>
                                </div>
                                <div class="message ${messageClass}">
                                    <div class="typing-indicator">
                                        <div class="typing-dot"></div>
                                        <div class="typing-dot"></div>
                                        <div class="typing-dot"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // 插入到原气泡之后
                    chatBody.insertBefore(loadingContainer, originalContainer.nextSibling);
                    
                    // 自动滚动到底部
                    window.autoScrollToBottom();
                    
                    return loadingContainer;
                }
                
                // 创建翻译结果气泡
                function createTranslationBubble(originalContainer, translatedText, targetLangName, targetLangCode, sourceLangCode) {
                    const chatBody = document.getElementById('chat-body');
                    
                    // 获取原气泡的位置类（placement-left, placement-right, placement-center）
                    let placementClass = 'placement-left';
                    if (originalContainer.classList.contains('placement-right')) {
                        placementClass = 'placement-right';
                    } else if (originalContainer.classList.contains('placement-center')) {
                        placementClass = 'placement-center';
                    }
                    
                    // 获取原气泡的消息样式类（user-message, ai-message, system-message）
                    let messageClass = 'ai-message';
                    const originalMessage = originalContainer.querySelector('.message');
                    if (originalMessage) {
                        if (originalMessage.classList.contains('user-message')) {
                            messageClass = 'user-message';
                        } else if (originalMessage.classList.contains('system-message')) {
                            messageClass = 'system-message';
                        }
                    }
                    
                    // 创建翻译气泡
                    const translationContainer = document.createElement('div');
                    translationContainer.className = `message-container ${placementClass}`;
                    translationContainer.style.cssText = `
                        margin-top: 10px;
                        opacity: 0;
                        animation: fadeIn 0.3s ease-in-out forwards;
                    `;
                    
                    // 添加淡入动画
                    const style = document.createElement('style');
                    style.textContent = `
                        @keyframes fadeIn {
                            from { opacity: 0; transform: translateY(10px); }
                            to { opacity: 1; transform: translateY(0); }
                        }
                    `;
                    document.head.appendChild(style);
                    
                    // 构建翻译气泡HTML
                    translationContainer.innerHTML = `
                        <div class="message-wrapper">
                            <span class="icon">🌐</span>
                            <div class="content-wrapper">
                                <div class="sender-info">
                                    <span class="sender" style="color: #009688;">${window.i18n_texts.translation_result} (${targetLangName})</span>
                                    <span class="timestamp">${new Date().toLocaleString()}</span>
                                </div>
                                <div class="message ${messageClass}" data-translation="true" data-source-lang="${sourceLangCode}" data-target-lang="${targetLangCode}">
                                    ${translatedText}
                                </div>
                                <div class="message-actions">
                                    <button class="action-button">翻译</button>
                                    <button class="action-button">编辑</button>
                                    <button class="action-button">复制</button>
                                    <button class="action-button">删除</button>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // 插入到原气泡之后
                    chatBody.insertBefore(translationContainer, originalContainer.nextSibling);
                    
                    // 重新初始化消息操作按钮
                    initMessageActions();
                    
                    // 自动滚动到底部
                    window.autoScrollToBottom();
                }
                

                
                /**
                 * 初始化消息操作按钮事件函数
                 * 为所有消息操作按钮添加事件监听器，包括翻译、编辑、复制和删除按钮
                 * 当DOM发生变化时，会重新调用此函数为新添加的按钮添加事件监听
                 */
                function initMessageActions() {
                    // 获取所有消息操作按钮容器
                    document.querySelectorAll('.message-actions').forEach(container => {
                        // 根据类名获取按钮，确保功能正确绑定
                        // 翻译按钮
                        const translateBtn = container.querySelector('.translate-btn') || container.querySelectorAll('.action-button')[0];
                        if (translateBtn) {
                            translateBtn.onclick = showTranslateMenu;  // 绑定翻译菜单显示函数
                            translateBtn.className = 'action-button translate-btn';
                        }
                        
                        // 编辑按钮
                        const editBtn = container.querySelector('.edit-btn') || container.querySelectorAll('.action-button')[1];
                        if (editBtn) {
                            editBtn.onclick = editMessage;  // 绑定编辑消息函数
                            editBtn.className = 'action-button edit-btn';
                        }
                        
                        // 复制按钮
                        const copyBtn = container.querySelector('.copy-btn') || container.querySelectorAll('.action-button')[2];
                        if (copyBtn) {
                            copyBtn.onclick = copyMessage;  // 绑定复制消息函数
                            copyBtn.className = 'action-button copy-btn';
                        }
                        
                        // 删除按钮
                        const deleteBtn = container.querySelector('.delete-btn') || container.querySelectorAll('.action-button')[3];
                        if (deleteBtn) {
                            deleteBtn.onclick = deleteMessage;  // 绑定删除消息函数
                            deleteBtn.className = 'action-button delete-btn';
                        }
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
        
        # 准备国际化文本
        translation_result_text = i18n.translate('translation_result')
        edit_content_text = i18n.translate('edit_content')
        cancel_text = i18n.translate('cancel')
        save_text = i18n.translate('save')
        edit_success_text = i18n.translate('edit_success')
        translating_text = i18n.translate('translating')
        
        # 准备国际化文本字典
        i18n_texts = {
            'translation_result': translation_result_text,
            'edit_content': edit_content_text,
            'cancel': cancel_text,
            'save': save_text,
            'edit_success': edit_success_text,
            'translating': translating_text
        }
        
        # 导入json模块
        import json
        
        # 将字典转换为JSON字符串，确保语法正确
        i18n_json = json.dumps(i18n_texts)
        
        # 注入国际化文本到JavaScript全局变量
        initial_html = initial_html + f"""
        <script>
            // 国际化文本，在页面加载时注入
            window.i18n_texts = {i18n_json};
        </script>
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
        from utils.i18n_manager import i18n
        thinking_text = i18n.translate('thinking')
        if sender == "AI" and content != thinking_text:
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
                f"        if (messageContent && (sender && sender.textContent === 'AI' || messageContent.textContent === '{thinking_text}')) {{\n"
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
                "    if (window.autoScrollToBottom) window.autoScrollToBottom();\n"
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
                "if (window.autoScrollToBottom) window.autoScrollToBottom();"
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
        """重新初始化UI，用于语言切换时更新界面"""
        # 直接使用JavaScript更新所有消息按钮的文本，避免重新加载整个HTML
        # 准备翻译后的按钮文本
        translate_text = i18n.translate("translate")
        edit_text = i18n.translate("edit")
        copy_text = i18n.translate("copy")
        delete_text = i18n.translate("delete")
        
        # 构建JavaScript代码，直接更新所有按钮文本
        js_template = """
        (function() {
            // 更新所有消息按钮的文本
            document.querySelectorAll('.message-actions').forEach(container => {
                // 根据索引获取按钮，确保功能正确绑定
                const buttons = container.querySelectorAll('.action-button');
                if (buttons.length > 0) {
                    buttons[0].textContent = '__TRANSLATE__';
                    buttons[0].className = 'action-button translate-btn';
                }
                if (buttons.length > 1) {
                    buttons[1].textContent = '__EDIT__';
                    buttons[1].className = 'action-button edit-btn';
                }
                if (buttons.length > 2) {
                    buttons[2].textContent = '__COPY__';
                    buttons[2].className = 'action-button copy-btn';
                }
                if (buttons.length > 3) {
                    buttons[3].textContent = '__DELETE__';
                    buttons[3].className = 'action-button delete-btn';
                }
            });
            
            // 重新初始化消息操作事件
            if (typeof initMessageActions === 'function') {
                initMessageActions();
            }
        })();
        """
        
        # 替换占位符为实际的翻译文本
        js_update_buttons = js_template.replace('__TRANSLATE__', translate_text)
        js_update_buttons = js_update_buttons.replace('__EDIT__', edit_text)
        js_update_buttons = js_update_buttons.replace('__COPY__', copy_text)
        js_update_buttons = js_update_buttons.replace('__DELETE__', delete_text)
        
        # 执行JavaScript更新按钮文本
        self.chat_history_view.page().runJavaScript(js_update_buttons)
        
        # 重新注入最新的国际化文本到JavaScript全局变量
        translation_result_text = i18n.translate('translation_result')
        edit_content_text = i18n.translate('edit_content')
        cancel_text = i18n.translate('cancel')
        save_text = i18n.translate('save')
        edit_success_text = i18n.translate('edit_success')
        translating_text = i18n.translate('translating')
        
        # 准备国际化文本字典
        i18n_texts = {
            'translation_result': translation_result_text,
            'edit_content': edit_content_text,
            'cancel': cancel_text,
            'save': save_text,
            'edit_success': edit_success_text,
            'translating': translating_text
        }
        
        # 导入json模块
        import json
        
        # 将字典转换为JSON字符串，确保语法正确
        i18n_json = json.dumps(i18n_texts)
        
        # 注入国际化文本到JavaScript全局变量
        js_inject_i18n = f"window.i18n_texts = {i18n_json};"
        self.chat_history_view.page().runJavaScript(js_inject_i18n)
        
    def translate_message(self, text, source_lang, target_lang):
        """
        翻译消息内容
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            str: 翻译后的文本
        """
        from utils.config_manager import config_manager
        from utils.ai_service import AIServiceFactory
        from utils.logger_config import get_logger
        
        logger = get_logger(__name__)
        
        try:
            # 从系统配置中读取翻译设置
            translation_provider = config_manager.get('translation.provider', 'Ollama')
            translation_model = config_manager.get('translation.default_model', 'llama3')
            
            logger.info(f"使用 {translation_provider} 提供商的 {translation_model} 模型进行翻译")
            logger.info(f"源语言: {source_lang}, 目标语言: {target_lang}, 文本: {text[:50]}...")
            
            # 创建AI服务实例
            if translation_provider.lower() == 'ollama':
                # Ollama只需要base_url，不需要api_key
                ai_service = AIServiceFactory.create_ai_service(
                    translation_provider.lower(),
                    base_url=config_manager.get(f'api.{translation_provider.lower()}_base_url', '')
                )
            else:
                # 其他服务提供商需要api_key和base_url
                ai_service = AIServiceFactory.create_ai_service(
                    translation_provider.lower(),
                    api_key=config_manager.get(f'api.{translation_provider.lower()}_key', ''),
                    base_url=config_manager.get(f'api.{translation_provider.lower()}_base_url', '')
                )
            
            # 构建翻译提示词
            translation_prompt = config_manager.get('translation.system_prompt', '你是一个好用的翻译助手。请将我输入的任何一种语言，翻译我需要的语言，请直接翻译成例子里的语言即可，我们不做任何的问答，我发给你所有的话都是需要翻译的内容，你只需要回答翻译结果。')
            
            # 构建聊天消息
            messages = [
                {"role": "system", "content": translation_prompt},
                {"role": "user", "content": f"请将以下{source_lang}文本翻译成{target_lang}：\n{text}"}
            ]
            
            # 调用AI服务进行翻译
            translated_text = ai_service.chat_completion(
                messages=messages,
                model=translation_model,
                temperature=0.1,
                stream=False
            )
            
            logger.info(f"翻译完成: {translated_text[:50]}...")
            
            return translated_text
        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            raise
            
    def handle_translation_request(self, text, source_lang, target_lang, callback_id):
        """
        处理来自JavaScript的翻译请求
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言代码
            target_lang: 目标语言代码
            callback_id: JavaScript回调ID，用于返回翻译结果
        """
        from PyQt5.QtCore import QThread, pyqtSignal
        from utils.logger_config import get_logger
        
        logger = get_logger(__name__)
        logger.info(f"收到翻译请求: 源语言={source_lang}, 目标语言={target_lang}, 文本长度={len(text)}, callback_id={callback_id}")
        
        # 创建一个线程来处理翻译请求，避免阻塞UI
        class TranslationThread(QThread):
            translation_done = pyqtSignal(str, str, str)
            translation_failed = pyqtSignal(str, str)
            
            def __init__(self, parent, text, source_lang, target_lang, callback_id):
                super().__init__(parent)
                self.parent = parent
                self.text = text
                self.source_lang = source_lang
                self.target_lang = target_lang
                self.callback_id = callback_id
            
            def run(self):
                try:
                    logger.info(f"翻译线程启动: callback_id={self.callback_id}")
                    translated_text = self.parent.translate_message(
                        self.text, self.source_lang, self.target_lang
                    )
                    logger.info(f"翻译线程完成: callback_id={self.callback_id}, 翻译结果长度={len(translated_text)}")
                    self.translation_done.emit(translated_text, self.target_lang, self.callback_id)
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"翻译线程失败: callback_id={self.callback_id}, 错误={error_msg}")
                    self.translation_failed.emit(error_msg, self.callback_id)
        
        # 创建并启动翻译线程
        thread = TranslationThread(self, text, source_lang, target_lang, callback_id)
        thread.translation_done.connect(self.on_translation_done)
        thread.translation_failed.connect(self.on_translation_failed)
        thread.start()
        logger.info(f"翻译线程已启动: callback_id={callback_id}")
        
    def on_translation_done(self, translated_text, target_lang, callback_id):
        """
        翻译完成回调
        
        Args:
            translated_text: 翻译后的文本
            target_lang: 目标语言代码
            callback_id: JavaScript回调ID
        """
        from utils.logger_config import get_logger
        import json
        
        logger = get_logger(__name__)
        logger.info(f"翻译完成: callback_id={callback_id}, 目标语言={target_lang}, 翻译结果长度={len(translated_text)}")
        
        # 使用json.dumps进行字符串转义，处理换行符、引号等特殊字符
        escaped_text = json.dumps(translated_text)
        escaped_target_lang = json.dumps(target_lang)
        escaped_callback_id = json.dumps(callback_id)
        
        # 将翻译结果返回给JavaScript
        js = f"window.handleTranslationResult({escaped_text}, {escaped_target_lang}, {escaped_callback_id});"
        logger.info(f"执行JavaScript回调: {js[:100]}...")
        self.chat_history_view.page().runJavaScript(js)
        
    def on_translation_failed(self, error, callback_id):
        """
        翻译失败回调
        
        Args:
            error: 错误信息
            callback_id: JavaScript回调ID
        """
        from utils.logger_config import get_logger
        import json
        
        logger = get_logger(__name__)
        logger.error(f"翻译失败: callback_id={callback_id}, 错误={error}")
        
        # 使用json.dumps进行字符串转义，处理换行符、引号等特殊字符
        escaped_error = json.dumps(str(error))
        escaped_callback_id = json.dumps(callback_id)
        
        # 将错误信息返回给JavaScript
        js = f"window.handleTranslationError({escaped_error}, {escaped_callback_id});"
        logger.info(f"执行JavaScript错误回调: {js}")
        self.chat_history_view.page().runJavaScript(js)
