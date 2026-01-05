# -*- coding: utf-8 -*-
"""
聊天历史面板组件，负责显示聊天历史
"""

import time
import json
import markdown
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ui.ui_utils import create_group_box, get_default_styles
from utils.logger_config import get_logger
from utils.i18n_manager import i18n

logger = get_logger(__name__)


class TranslationHandler(QWidget):
    """
    翻译处理器，用于处理JavaScript发送的翻译请求
    """
    def __init__(self, parent):
        """初始化翻译处理器"""
        super().__init__()
        self.parent = parent
    
    @pyqtSlot(str, str, str, str)
    def handle_translation_request(self, text, source_lang, target_lang, callback_id):
        """处理翻译请求，转发给父类的对应方法"""
        self.parent.handle_translation_request(text, source_lang, target_lang, callback_id)


class ChatHistoryPanel(QWidget):
    """
    聊天历史面板组件
    """

    def __init__(self):
        """初始化聊天历史面板"""
        super().__init__()
        self.styles = get_default_styles()
        self.init_ui()
        
        # 初始化QWebChannel
        from PyQt5.QtWebChannel import QWebChannel
        self.channel = QWebChannel()
        
        # 创建翻译处理器对象
        self.translation_handler = TranslationHandler(self)
        # 注册翻译处理器到WebChannel
        self.channel.registerObject('main', self.translation_handler)
        self.chat_history_text.page().setWebChannel(self.channel)
        
        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 讨论历史区域
        self.chat_history_group = create_group_box(
            i18n.translate("discussion_history"), self.styles["group_box"]
        )
        chat_history_layout = QVBoxLayout()
        chat_history_layout.setContentsMargins(10, 5, 10, 10)

        self.chat_history_text = QWebEngineView()
        # 禁用右键菜单
        self.chat_history_text.setContextMenuPolicy(Qt.NoContextMenu)
        self._init_web_content()

        chat_history_layout.addWidget(self.chat_history_text)
        self.chat_history_group.setLayout(chat_history_layout)
        layout.addWidget(self.chat_history_group, 1)  # 设置权重为1，占据剩余空间

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
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.js"></script>
            <style>
                html, body {
                    font-family: SimHei, Arial, sans-serif;
                    font-size: 13pt;
                    background-color: #fafafa;
                    margin: 0;
                    padding: 10px;
                    overflow-x: hidden;
                    max-width: 100%;
                }
                .message-container {
                    margin-bottom: 20px;
                    position: relative;
                    display: flex;
                    overflow-x: hidden;
                    max-width: 100%;
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
                    overflow-x: hidden;
                }
                .icon {
                    font-size: 36px;
                    margin-right: 14px;
                    margin-top: 4px;
                    flex-shrink: 0;
                }
                .content-wrapper {
                    flex: 1;
                    overflow-x: hidden;
                    max-width: 100%;
                }
                .sender-info {
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                    font-size: 16px;
                    overflow-x: hidden;
                    max-width: 100%;
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
                    overflow-x: hidden;
                    max-width: 100%;
                }
                .ai1-message {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    margin: 5px 10px 5px 10px;
                }
                .ai2-message {
                    background-color: #f3e5f5;
                    border: 2px solid #9c27b0;
                    margin: 5px 10px 5px 10px;
                }
                .ai3-message {
                    background-color: #e8f5e8;
                    border: 2px solid #2e7d32;
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
                    white-space: normal;
                    max-width: 100%;
                    min-width: 200px;
                    font-size: 13pt;
                    overflow-x: hidden;
                }
                .message-actions {
                    display: none;
                    margin-top: 5px;
                    margin-left: 3px;
                    overflow-x: hidden;
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
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    position: relative;
                }
                .action-button:hover {
                    background-color: #f0f0f0;
                }
                .action-button.loading {
                    cursor: not-allowed;
                }
                .action-button.loading::after {
                    content: '';
                    width: 12px;
                    height: 12px;
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #666;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    display: inline-block;
                }
                .message.loading {
                    position: relative;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 60px;
                }
                .message.loading::after {
                    content: '';
                    width: 20px;
                    height: 20px;
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #666;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    display: inline-block;
                    margin-left: 10px;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            </style>
        </head>
        <body id="discussion-body">
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
                
                // 初始化时启用自动滚动
                window.autoScrollEnabled = true;
                
                // 初始化WebChannel连接
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.pywebchannel = { objects: channel.objects };
                    // 将main对象附加到window上，方便访问
                    window.main = channel.objects.main;
                });
        </script>
        <script>
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
                        // 获取当前消息的纯文本内容，用于编辑，避免HTML标签问题
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
                        
                        // 设置初始内容，使用setText方法确保纯文本内容正确显示
                        quill.setText(currentText);
                        
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
                            // 获取编辑器中的新内容，使用text方法获取纯文本
                            const newText = quill.getText();
                            // 检查内容是否为空
                            if (newText.trim() !== '') {
                                // 更新原消息内容，直接设置文本内容
                                messageContent.innerText = newText;
                                
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
            
            // 简单的语言检测函数
            function detectLanguage(text) {
                // 中文检测：包含中文字符
                if (/[\u4e00-\u9fa5]/.test(text)) {
                    return 'zh-CN';
                }
                // 日语检测：包含日语假名
                if (/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]/.test(text)) {
                    return 'ja';
                }
                // 韩语检测：包含韩文字符
                if (/[\uac00-\ud7af]/.test(text)) {
                    return 'ko';
                }
                // 俄语检测：包含俄文字母
                if (/[\u0400-\u04ff]/.test(text)) {
                    return 'ru';
                }
                // 阿拉伯语检测：包含阿拉伯字母
                if (/[\u0600-\u06ff]/.test(text)) {
                    return 'ar';
                }
                // 法语检测：包含法语常见字符
                if (/[àâäçéèêëîïôöùûüÿ]/.test(text)) {
                    return 'fr';
                }
                // 西班牙语检测：包含西班牙语常见字符
                if (/[áéíóúüñ]/.test(text)) {
                    return 'es';
                }
                // 德语检测：包含德语常见字符
                if (/[äöüß]/.test(text)) {
                    return 'de';
                }
                // 默认英语
                return 'en';
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
                
                // 获取消息文本
                const messageText = messageContent.innerText;
                
                // 检测当前语言
                const currentLangCode = detectLanguage(messageText);
                
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
                const chatBody = document.getElementById('discussion-body');
                const chatRect = chatBody.getBoundingClientRect();
                
                // 计算菜单位置
                menu.style.left = `${buttonRect.left - chatRect.left}px`;
                menu.style.top = `${buttonRect.bottom - chatRect.top}px`;
                
                // 添加语言选项，排除当前语言
                Object.entries(languages).forEach(([code, name]) => {
                    // 跳过当前语言
                    if (code === currentLangCode) {
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
                        translateMessage(messageContainer, code, name);
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
            
            // 翻译请求队列，用于处理多个翻译请求
            let translationCallbacks = {};
            let translationRequestId = 0;
            
            // 执行消息翻译
            function translateMessage(messageContainer, targetLangCode, targetLangName) {
                // 获取消息内容
                const messageContent = messageContainer.querySelector('.message');
                if (!messageContent) return;
                
                const textToTranslate = messageContent.innerText;
                
                // 检测源语言
                const sourceLangCode = detectLanguage(textToTranslate);
                
                // 生成唯一的请求ID
                const requestId = ++translationRequestId;
                
                // 创建加载中的翻译气泡
                const loadingBubble = createLoadingTranslationBubble(messageContainer, targetLangName);
                
                // 保存回调信息
                translationCallbacks[requestId] = {
                    messageContainer: messageContainer,
                    targetLangName: targetLangName,
                    loadingBubble: loadingBubble
                };
                
                // 调用Python端的翻译功能（使用正确的QWebChannel方式）
                if (window.pywebchannel && window.pywebchannel.objects && window.pywebchannel.objects.main) {
                    window.pywebchannel.objects.main.handle_translation_request(textToTranslate, sourceLangCode, targetLangCode, requestId);
                } else {
                    // 降级方案：使用直接发送方式
                    window.qt.webChannelTransport.send(JSON.stringify({
                        type: 1,
                        object: "main",
                        method: "handle_translation_request",
                        params: [textToTranslate, sourceLangCode, targetLangCode, requestId]
                    }));
                }
            }
            
            // 处理翻译结果
            window.handleTranslationResult = function(translatedText, targetLangCode, callbackId) {
                const callbackInfo = translationCallbacks[callbackId];
                if (!callbackInfo) return;
                
                // 更新翻译气泡内容
                updateTranslationBubble(callbackInfo.loadingBubble, translatedText, callbackInfo.targetLangName);
                
                // 删除回调信息
                delete translationCallbacks[callbackId];
            };
            
            // 处理翻译错误
            window.handleTranslationError = function(errorMessage, callbackId) {
                const callbackInfo = translationCallbacks[callbackId];
                if (!callbackInfo) return;
                
                // 更新翻译气泡为错误状态
                updateTranslationBubbleWithError(callbackInfo.loadingBubble, errorMessage, callbackInfo.targetLangName);
                
                // 删除回调信息
                delete translationCallbacks[callbackId];
            };
            
            // 为所有消息容器添加唯一ID
            function ensureMessageIds() {
                const messages = document.querySelectorAll('.message-container');
                messages.forEach((msg, index) => {
                    if (!msg.dataset.messageId) {
                        msg.dataset.messageId = `msg-${Date.now()}-${index}`;
                    }
                });
            }
            
            // 创建加载中的翻译气泡
            function createLoadingTranslationBubble(originalContainer, targetLangName) {
                const chatBody = document.getElementById('discussion-body');
                
                // 确保所有消息都有唯一ID
                ensureMessageIds();
                
                // 获取原气泡的唯一ID
                const originalId = originalContainer.dataset.messageId;
                
                // 从原气泡获取样式信息
                const originalMessage = originalContainer.querySelector('.message');
                const originalPlacement = originalContainer.className.includes('placement-right') ? 'right' : 
                                         originalContainer.className.includes('placement-left') ? 'left' : 'center';
                
                // 获取原气泡的消息样式类（排除message基类）
                let messageClass = 'system-message';
                if (originalMessage) {
                    const originalClasses = originalMessage.className.split(' ');
                    messageClass = originalClasses.find(cls => cls !== 'message') || 'system-message';
                }
                
                // 创建翻译气泡
                const translationContainer = document.createElement('div');
                translationContainer.className = `message-container placement-${originalPlacement}`;
                // 添加元数据标识：标记为翻译结果，关联原气泡ID和目标语言
                translationContainer.dataset.isTranslation = 'true';
                translationContainer.dataset.originalMessageId = originalId;
                translationContainer.dataset.targetLanguage = targetLangName;
                translationContainer.style.cssText = `
                    margin-top: 10px;
                    opacity: 0;
                    animation: fadeIn 0.3s ease-in-out forwards;
                `;
                
                // 创建翻译气泡HTML
                translationContainer.innerHTML = `
                    <div class="message-wrapper">
                        <span class="icon">🌐</span>
                        <div class="content-wrapper">
                            <div class="sender-info">
                                <span class="sender" style="color: #009688;">翻译结果 (${targetLangName})</span>
                                <span class="timestamp">${new Date().toLocaleString()}</span>
                            </div>
                            <div class="message ${messageClass} loading">翻译中...</div>
                        </div>
                    </div>
                `;
                
                // 插入到原气泡之后
                chatBody.insertBefore(translationContainer, originalContainer.nextSibling);
                
                // 自动滚动到底部
                window.autoScrollToBottom();
                
                return translationContainer;
            }
            
            // 更新翻译气泡内容
            function updateTranslationBubble(loadingBubble, translatedText, targetLangName) {
                // 获取消息元素
                const messageElement = loadingBubble.querySelector('.message');
                if (!messageElement) return;
                
                // 移除加载状态
                messageElement.classList.remove('loading');
                
                // 设置翻译文本
                messageElement.innerHTML = translatedText;
                
                // 添加操作按钮
                const contentWrapper = loadingBubble.querySelector('.content-wrapper');
                if (contentWrapper && !loadingBubble.querySelector('.message-actions')) {
                    const actionsDiv = document.createElement('div');
                    actionsDiv.className = 'message-actions';
                    actionsDiv.innerHTML = `
                        <button class="action-button translate-btn">翻译</button>
                        <button class="action-button edit-btn">编辑</button>
                        <button class="action-button copy-btn">复制</button>
                        <button class="action-button delete-btn">删除</button>
                    `;
                    contentWrapper.appendChild(actionsDiv);
                    
                    // 重新初始化消息操作按钮
                    initMessageActions();
                }
            }
            
            // 更新翻译气泡为错误状态
            function updateTranslationBubbleWithError(loadingBubble, errorMessage, targetLangName) {
                // 获取消息元素
                const messageElement = loadingBubble.querySelector('.message');
                if (!messageElement) return;
                
                // 移除加载状态
                messageElement.classList.remove('loading');
                
                // 设置错误文本
                messageElement.innerHTML = `翻译失败: ${errorMessage}`;
                messageElement.style.color = '#f44336';
                
                // 添加操作按钮
                const contentWrapper = loadingBubble.querySelector('.content-wrapper');
                if (contentWrapper && !loadingBubble.querySelector('.message-actions')) {
                    const actionsDiv = document.createElement('div');
                    actionsDiv.className = 'message-actions';
                    actionsDiv.innerHTML = `
                        <button class="action-button translate-btn">翻译</button>
                        <button class="action-button edit-btn">编辑</button>
                        <button class="action-button copy-btn">复制</button>
                        <button class="action-button delete-btn">删除</button>
                    `;
                    contentWrapper.appendChild(actionsDiv);
                    
                    // 重新初始化消息操作按钮
                    initMessageActions();
                }
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
            const chatBody = document.getElementById('discussion-body');
            if (chatBody) {
                observer.observe(chatBody, config);
            }
            
            // 初始初始化
            initMessageActions();
        </script>
        </body>
        </html>
        """
        self.chat_history_text.setHtml(initial_html)

    def append_to_discussion_history(self, sender: str, content: str):
        """将消息添加到讨论历史中

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
            if sender.startswith("学者AI1"):
                message_class = "ai1-message"
                sender_color = "#0d47a1"
                placement = "right"
            elif sender.startswith("学者AI2"):
                message_class = "ai2-message"
                sender_color = "#6a1b9a"
                placement = "left"
            elif sender.startswith("专家AI3") or sender.startswith("裁判AI3"):
                message_class = "ai3-message"
                sender_color = "#1b5e20"
                placement = "center"
            icon_char = "🤖"

        # 格式化发送者信息
        formatted_sender = sender
        if "学者AI" in sender and " " in sender:
            parts = sender.split(" ")
            if len(parts) >= 3:
                formatted_sender = f"{parts[0]}{parts[1]}({parts[2]})"
            elif len(parts) >= 2:
                formatted_sender = f"{parts[0]}{parts[1]}"

        # 构建HTML内容
        html_content = f"<div class='message-container placement-{placement}'>"
        html_content += "<div class='message-wrapper'>"
        html_content += f"<span class='icon'>{icon_char}</span>"
        html_content += "<div class='content-wrapper'>"
        html_content += "<div class='sender-info'>"
        html_content += f"<span class='sender' style='color: {sender_color};'>{formatted_sender}</span>"
        html_content += f"<span class='timestamp'>{timestamp}</span>"
        html_content += "</div>"
        if content:
            html_content += (
                f"<div class='message {message_class}'>{rendered_content}</div>"
            )
        html_content += "<div class='message-actions'>"
        html_content += f"<button class='action-button translate-btn'>{i18n.translate('translate')}</button>"
        html_content += f"<button class='action-button edit-btn'>{i18n.translate('edit')}</button>"
        html_content += f"<button class='action-button copy-btn'>{i18n.translate('copy')}</button>"
        html_content += f"<button class='action-button delete-btn'>{i18n.translate('delete')}</button>"
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
            "    const chatBody = document.getElementById('discussion-body');\n"
            "    chatBody.innerHTML += " + escaped_html + ";\n"
            "    \n"
            "    // 为新添加的消息分配唯一ID\n"
            "    const messages = document.querySelectorAll('.message-container');\n"
            "    const newMessage = messages[messages.length - 1];\n"
            "    if (newMessage && !newMessage.dataset.messageId) {\n"
            "        newMessage.dataset.messageId = 'msg-' + Date.now() + '-' + (messages.length - 1);\n"
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

        self.chat_history_text.page().runJavaScript(js)

    def _render_markdown_content(self, content: str) -> str:
        """将Markdown内容渲染为HTML

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

    def on_stream_update(self, sender: str, chunk: str, model_name: str):
        """处理流式更新信号，当AI生成响应时实时更新UI

        Args:
            sender: 发送者名称
            chunk: 新生成的内容片段
            model_name: 使用的模型名称
        """
        # 渲染Markdown内容
        rendered_content = self._render_markdown_content(chunk)

        # 更新聊天历史
        rendered_content_js = json.dumps(rendered_content)

        # 根据发送者设置不同的样式和位置
        if sender.startswith("学者AI1"):
            message_class = "ai1-message"
            placement = "right"
            sender_color = "#0d47a1"
        elif sender.startswith("学者AI2"):
            message_class = "ai2-message"
            placement = "left"
            sender_color = "#6a1b9a"
        elif sender.startswith("专家AI3") or sender.startswith("裁判AI3"):
            message_class = "ai3-message"
            placement = "center"
            sender_color = "#1b5e20"

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
        message_html += f"<button class='action-button translate-btn'>{i18n.translate('translate')}</button>"
        message_html += f"<button class='action-button edit-btn'>{i18n.translate('edit')}</button>"
        message_html += f"<button class='action-button copy-btn'>{i18n.translate('copy')}</button>"
        message_html += f"<button class='action-button delete-btn'>{i18n.translate('delete')}</button>"
        message_html += "</div>"
        message_html += "</div>"
        message_html += "</div>"
        message_html += "</div>"

        escaped_html = json.dumps(message_html)

        # 构建JavaScript代码，实现流式更新
        js = (
            "(function() {\n"
            "    const chatBody = document.getElementById('discussion-body');\n"
            "    const messages = chatBody.querySelectorAll('.message-container');\n"
            "    let lastAiMessage = null;\n"
            "    let lastAiMessageIndex = -1;\n"
            "    \n"
            "    // 查找最后一条对应AI的消息\n"
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
            "    // 检查是否有新的轮次提示在这条AI消息之后\n"
            "    let isSameRound = true;\n"
            "    if (lastAiMessage) {\n"
            "        for (let i = lastAiMessageIndex + 1; i < messages.length; i++) {\n"
            "            const message = messages[i];\n"
            "            const messageContent = message.querySelector('.message');\n"
            "            if (messageContent) {\n"
            "                const content = messageContent.textContent || messageContent.innerText;\n"
            "                // 检查是否是轮次提示（以===开头和结尾）\n"
            "                if (content && content.startsWith('===') && content.endsWith('===')) {\n"
            "                    isSameRound = false;\n"
            "                    break;\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "    \n"
            "    // 根据检查结果决定是更新还是添加新消息\n"
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
            "        // 为新添加的消息分配唯一ID\n"
            "        const newMessages = chatBody.querySelectorAll('.message-container');\n"
            "        const newMessage = newMessages[newMessages.length - 1];\n"
            "        if (newMessage && !newMessage.dataset.messageId) {\n"
            "            newMessage.dataset.messageId = 'msg-' + Date.now() + '-' + (newMessages.length - 1);\n"
            "        }\n"
            "        // 重新渲染MathJax公式\n"
            "        if (window.MathJax) {\n"
            "            MathJax.typesetPromise();\n"
            "        }\n"
            "    }\n"
            "    \n"
            "    if (window.autoScrollToBottom) window.autoScrollToBottom();\n"
            "})();"
        )

        self.chat_history_text.page().runJavaScript(js)

    def get_html_content(self, callback):
        """获取当前HTML内容

        Args:
            callback: 回调函数，接收HTML内容
        """
        self.chat_history_text.page().toHtml(callback)

    def clear_history(self):
        """
        清空讨论历史
        """
        # 使用JavaScript直接清空聊天内容，包装在IIFE中避免变量重复声明
        js = """
        (function() {
            const chatBody = document.getElementById('discussion-body');
            if (chatBody) {
                chatBody.innerHTML = '';
            }
        })();
        """
        self.chat_history_text.page().runJavaScript(js)

    def clear_discussion_history(self):
        """清空讨论历史"""
        self.clear_history()

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
            translation_prompt = config_manager.get('translation.system_prompt', i18n.translate('translate_system_prompt'))
            
            # 构建聊天消息
            messages = [
                {"role": "system", "content": translation_prompt},
                {"role": "user", "content": i18n.translate('translate_prompt', source_lang=source_lang, target_lang=target_lang, text=text)}
            ]
            
            # 调用AI服务进行翻译
            translated_text = ai_service.chat_completion(
                messages=messages,
                model=translation_model,
                temperature=0.1,
                stream=False
            )
            
            logger.info(f"翻译完成: {translated_text[:50]}...")
            return translated_text.strip()
        except Exception as e:
            logger.error(f"{i18n.translate('translation_failed')}: {str(e)}")
            raise
    
    def on_translation_done(self, translated_text, target_lang, callback_id):
        """
        处理翻译成功事件
        
        Args:
            translated_text: 翻译后的文本
            target_lang: 目标语言代码
            callback_id: 回调ID
        """
        logger.info(f"翻译成功，回调ID: {callback_id}")
        
        # 使用json.dumps进行字符串转义，处理换行符、引号等特殊字符
        import json
        escaped_text = json.dumps(translated_text)
        escaped_target_lang = json.dumps(target_lang)
        escaped_callback_id = json.dumps(callback_id)
        
        # 将翻译结果返回给JavaScript
        js = f"window.handleTranslationResult({escaped_text}, {escaped_target_lang}, {escaped_callback_id});"
        logger.info(f"执行JavaScript回调: {js[:100]}...")
        self.chat_history_text.page().runJavaScript(js)
    
    def on_translation_failed(self, error_msg, callback_id):
        """
        处理翻译失败事件
        
        Args:
            error_msg: 错误信息
            callback_id: 回调ID
        """
        logger.error(f"翻译失败，回调ID: {callback_id}, 错误: {error_msg}")
        
        # 返回错误信息给JavaScript
        import json
        error_text = i18n.translate('translate_failed', error=error_msg)
        escaped_text = json.dumps(error_text)
        escaped_callback_id = json.dumps(callback_id)
        
        js = f"window.handleTranslationError({escaped_text}, {escaped_callback_id});"
        self.chat_history_text.page().runJavaScript(js)
    
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

    def reinit_ui(self):
        """重新初始化UI，用于语言切换时更新界面"""
        # 更新聊天历史区域标题
        self.chat_history_group.setTitle(i18n.translate("discussion_history"))

        # 保存当前聊天内容并重新初始化web内容
        def save_and_reinit(html):
            # 保存当前内容的body部分，移除旧的script标签
            saved_body_content = None
            body_start = html.find("<body")
            if body_start != -1:
                body_end = html.find(">", body_start) + 1
                body_close = html.rfind("</body>")
                if body_close != -1:
                    body_content = html[body_end:body_close]
                    # 移除所有script标签
                    import re
                    saved_body_content = re.sub(r'<script[^>]*>.*?</script>', '', body_content, flags=re.DOTALL)
            
            # 重新初始化web内容（包含翻译文本）
            self._init_web_content()
            
            # 如果有保存的内容，恢复它
            if saved_body_content:
                # 等待新的web内容初始化完成后再恢复
                def restore_content(new_html):
                    # 找到新HTML的body标签位置
                    new_body_start = new_html.find("<body")
                    if new_body_start != -1:
                        new_body_end = new_html.find(">", new_body_start) + 1
                        new_body_close = new_html.rfind("</body>")
                        if new_body_close != -1:
                            # 构建新的HTML，保留新的头部和script标签，插入保存的body内容
                            final_html = (
                                new_html[:new_body_end] +
                                saved_body_content +
                                new_html[new_body_close:]
                            )
                            self.chat_history_text.setHtml(final_html)
                            
                            # 更新所有消息按钮的文本
                            js_update_buttons = """
                            // 更新所有消息按钮的文本
                            document.querySelectorAll('.message-actions').forEach(container => {
                                // 根据类名获取按钮，确保功能正确绑定
                                // 翻译按钮
                                const translateBtn = container.querySelector('.translate-btn') || container.querySelectorAll('.action-button')[0];
                                if (translateBtn) {
                                    translateBtn.textContent = "__TRANSLATE__";
                                    translateBtn.className = 'action-button translate-btn';
                                }
                                
                                // 编辑按钮
                                const editBtn = container.querySelector('.edit-btn') || container.querySelectorAll('.action-button')[1];
                                if (editBtn) {
                                    editBtn.textContent = "__EDIT__";
                                    editBtn.className = 'action-button edit-btn';
                                }
                                
                                // 复制按钮
                                const copyBtn = container.querySelector('.copy-btn') || container.querySelectorAll('.action-button')[2];
                                if (copyBtn) {
                                    copyBtn.textContent = "__COPY__";
                                    copyBtn.className = 'action-button copy-btn';
                                }
                                
                                // 删除按钮
                                const deleteBtn = container.querySelector('.delete-btn') || container.querySelectorAll('.action-button')[3];
                                if (deleteBtn) {
                                    deleteBtn.textContent = "__DELETE__";
                                    deleteBtn.className = 'action-button delete-btn';
                                }
                            });
                            """
                            
                            # 替换占位符为翻译后的文本
                            js_update_buttons = js_update_buttons.replace("__TRANSLATE__", i18n.translate("translate"))
                            js_update_buttons = js_update_buttons.replace("__EDIT__", i18n.translate("edit"))
                            js_update_buttons = js_update_buttons.replace("__COPY__", i18n.translate("copy"))
                            js_update_buttons = js_update_buttons.replace("__DELETE__", i18n.translate("delete"))
                            
                            # 执行JavaScript更新按钮文本
                            self.chat_history_text.page().runJavaScript(js_update_buttons)
                            
                            # 显式调用initMessageActions()重新绑定按钮事件
                            self.chat_history_text.page().runJavaScript("if (typeof initMessageActions === 'function') { initMessageActions(); }")
                
                # 获取新初始化的HTML结构
                self.chat_history_text.page().toHtml(restore_content)
        
        # 异步获取当前内容，在回调中执行保存和重新初始化
        self.chat_history_text.page().toHtml(save_and_reinit)