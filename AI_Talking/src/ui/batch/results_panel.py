# -*- coding: utf-8 -*-
"""
批量处理结果面板组件，负责显示处理结果
"""

import json
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QFileDialog,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from utils.i18n_manager import i18n


class BatchResultsPanel(QWidget):
    """
    批量处理结果面板组件

    信号:
        clear_results: 清空结果信号
    """

    # 定义信号
    clear_results = pyqtSignal()

    def __init__(self):
        """初始化批量处理结果面板"""
        super().__init__()
        self.batch_history_html = ""
        self.init_ui()
        self._init_web_content()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 结果显示区域
        self.result_group = QGroupBox(i18n.translate("batch_processing_results"))
        self.result_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
        result_layout = QVBoxLayout()
        result_layout.setContentsMargins(10, 15, 10, 10)  # 调整内边距，顶部增加到15px
        result_layout.setSpacing(0)  # 去除间距

        self.result_text = QWebEngineView()
        result_layout.addWidget(self.result_text, 1)  # 设置权重为1，占据所有空间
        self.result_group.setLayout(result_layout)
        layout.addWidget(self.result_group, 1)  # 设置权重为1，占据剩余空间

        self.setLayout(layout)

    def update_result_title(self, batch_type):
        """
        根据批量类型更新结果标题

        Args:
            batch_type: 批量类型（翻译后的字符串）
        """
        if batch_type == i18n.translate("discussion"):
            self.result_group.setTitle(i18n.translate("batch_discussion_history"))
        elif batch_type == i18n.translate("debate"):
            self.result_group.setTitle(i18n.translate("batch_debate_history"))
        else:
            self.result_group.setTitle(i18n.translate("batch_processing_results"))

    def _init_web_content(self):
        """
        初始化浏览器控件的HTML内容
        """
        # 获取翻译文本
        batch_results_title = i18n.translate("batch_processing_results")

        # 使用字符串连接方式构建HTML
        initial_html = (
            "<!DOCTYPE html>\n"
            + "<html>\n"
            + "<head>\n"
            + '    <meta charset="utf-8">\n'
            + '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            + "    <title>"
            + batch_results_title
            + "</title>\n"
            + "    <!-- 引入MathJax支持数学公式渲染 -->\n"
            + '    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>\n'
            + "    <!-- 引入Marked.js支持Markdown渲染 -->\n"
            + '    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>\n'
            + "    <style>\n"
            + "        /* 全局样式 */\n"
            + "        body {\n"
            + "            font-family: 'SimHei', 'Microsoft YaHei', Arial, sans-serif;\n"
            + "            font-size: 13pt;\n"
            + "            line-height: 1.6;\n"
            + "            background-color: #f5f7fa;\n"
            + "            margin: 0;\n"
            + "            padding: 20px;\n"
            + "            color: #333;\n"
            + "        }\n"
            + "        \n"
            + "        /* 批量处理标题 */\n"
            + "        .batch-title {\n"
            + "            text-align: center;\n"
            + "            font-size: 18pt;\n"
            + "            font-weight: bold;\n"
            + "            margin-bottom: 20px;\n"
            + "            color: #2c3e50;\n"
            + "        }\n"
            + "        \n"
            + "        /* 信息容器 */\n"
            + "        .info-container {\n"
            + "            background-color: #fff;\n"
            + "            border-radius: 8px;\n"
            + "            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);\n"
            + "            padding: 20px;\n"
            + "            margin-bottom: 20px;\n"
            + "        }\n"
            + "        \n"
            + "        /* 任务信息 */\n"
            + "        .task-info {\n"
            + "            background-color: #e3f2fd;\n"
            + "            border-left: 5px solid #2196f3;\n"
            + "            padding: 15px;\n"
            + "            margin-bottom: 15px;\n"
            + "            border-radius: 4px;\n"
            + "        }\n"
            + "        \n"
            + "        /* 系统消息 */\n"
            + "        .system-message {\n"
            + "            background-color: #f5f5f5;\n"
            + "            padding: 10px;\n"
            + "            margin-bottom: 10px;\n"
            + "            border-radius: 4px;\n"
            + "            font-style: italic;\n"
            + "            color: #666;\n"
            + "        }\n"
            + "        \n"
            + "        /* 进度消息 */\n"
            + "        .progress-message {\n"
            + "            background-color: #fff3cd;\n"
            + "            padding: 10px;\n"
            + "            margin-bottom: 10px;\n"
            + "            border-radius: 4px;\n"
            + "            color: #856404;\n"
            + "        }\n"
            + "        \n"
            + "        /* 成功消息 */\n"
            + "        .success-message {\n"
            + "            background-color: #d4edda;\n"
            + "            padding: 10px;\n"
            + "            margin-bottom: 10px;\n"
            + "            border-radius: 4px;\n"
            + "            color: #155724;\n"
            + "        }\n"
            + "        \n"
            + "        /* 错误消息 */\n"
            + "        .error-message {\n"
            + "            background-color: #f8d7da;\n"
            + "            padding: 10px;\n"
            + "            margin-bottom: 10px;\n"
            + "            border-radius: 4px;\n"
            + "            color: #721c24;\n"
            + "        }\n"
            + "        \n"
            + "        /* 结果内容 */\n"
            + "        .result-content {\n"
            + "            background-color: #f0f8ff;\n"
            + "            padding: 15px;\n"
            + "            margin-bottom: 15px;\n"
            + "            border-radius: 4px;\n"
            + "            border: 1px solid #b3d7ff;\n"
            + "        }\n"
            + "        \n"
            + "        /* 分隔线 */\n"
            + "        .separator {\n"
            + "            border: none;\n"
            + "            height: 1px;\n"
            + "            background-color: #e0e0e0;\n"
            + "            margin: 20px 0;\n"
            + "        }\n"
            + "        \n"
            + "        /* 代码块 */\n"
            + "        pre {\n"
            + "            background-color: #f8f9fa;\n"
            + "            border: 1px solid #dee2e6;\n"
            + "            border-radius: 4px;\n"
            + "            padding: 10px;\n"
            + "            overflow-x: auto;\n"
            + "            font-family: 'Courier New', Courier, monospace;\n"
            + "            font-size: 11pt;\n"
            + "        }\n"
            + "        \n"
            + "        /* 表格样式 */\n"
            + "        table {\n"
            + "            border-collapse: collapse;\n"
            + "            width: 100%;\n"
            + "            margin-bottom: 15px;\n"
            + "        }\n"
            + "        \n"
            + "        th, td {\n"
            + "            border: 1px solid #dee2e6;\n"
            + "            padding: 8px;\n"
            + "            text-align: left;\n"
            + "        }\n"
            + "        \n"
            + "        th {\n"
            + "            background-color: #f8f9fa;\n"
            + "            font-weight: bold;\n"
            + "        }\n"
            + "    </style>\n"
            + "</head>\n"
            + "<body>\n"
            + '    <h1 class="batch-title">'
            + batch_results_title
            + "</h1>\n"
            + "    <div id='batch-results'></div>\n"
            + "    <script>\n"
            + "        // 智能滚动控制变量\n"
            + "        let autoScrollEnabled = true;\n"
            + "        const SCROLL_TOLERANCE = 10;\n"
            + "        \n"
            + "        // 检查是否在底部附近\n"
            + "        function isNearBottom() {\n"
            + "            const scrollPosition = window.scrollY + window.innerHeight;\n"
            + "            const documentHeight = document.body.scrollHeight;\n"
            + "            return scrollPosition >= documentHeight - SCROLL_TOLERANCE;\n"
            + "        }\n"
            + "        \n"
            + "        // 自动滚动到底部（如果启用）\n"
            + "        function autoScrollToBottom() {\n"
            + "            if (autoScrollEnabled) {\n"
            + "                window.scrollTo(0, document.body.scrollHeight);\n"
            + "            }\n"
            + "        }\n"
            + "        \n"
            + "        // 监听滚动事件，控制自动滚动状态\n"
            + "        window.addEventListener('scroll', function() {\n"
            + "            // 如果不在底部附近，禁用自动滚动\n"
            + "            if (!isNearBottom()) {\n"
            + "                autoScrollEnabled = false;\n"
            + "            } else {\n"
            + "                // 如果回到底部附近，启用自动滚动\n"
            + "                autoScrollEnabled = true;\n"
            + "            }\n"
            + "        });\n"
            + "        \n"
            + "        // 初始化时启用自动滚动\n"
            + "        autoScrollEnabled = true;\n"
            + "    </script>\n"
            + "</body>\n"
            + "</html>"
        )

        self.result_text.setHtml(initial_html)
        self.batch_history_html = initial_html

    def append_to_result(self, message, message_type="info"):
        """
        向结果浏览器添加消息，按照讨论历史样式格式化

        Args:
            message: 要添加的消息内容
            message_type: 消息类型，可选值："info", "success", "error", "system", "task", "result"
        """
        # 生成HTML内容
        if message_type == "info":
            # 进度消息
            html_content = f"<div class='progress-message'>{message}</div>"
        elif message_type == "success":
            # 成功消息（任务完成）
            html_content = f"<div class='success-message'>{message}</div>"
        elif message_type == "result":
            # 结果消息
            html_content = f"<div class='result-content'>{message}</div>"
        elif message_type == "system":
            # 系统消息（分隔线）
            html_content = f"<div class='system-message'>{message}</div>"
        elif message_type == "task":
            # 任务信息
            html_content = f"<div class='task-info'>{message}</div>"
        elif message_type == "error":
            # 错误消息
            html_content = f"<div class='error-message'>{message}</div>"
        else:
            # 默认消息类型
            html_content = f"<div class='progress-message'>{message}</div>"

        # 更新批量历史HTML内容（用于保存）
        # 获取batch-results div的开始和结束位置
        batch_results_start = self.batch_history_html.find("<div id='batch-results'>")
        batch_results_end = self.batch_history_html.find("</div>", batch_results_start)

        if batch_results_start != -1 and batch_results_end != -1:
            # 提取现有内容
            existing_content = self.batch_history_html[
                batch_results_start + 24 : batch_results_end
            ]  # 24是"<div id='batch-results'>"的长度

            # 构建新的内容，将新内容添加到现有内容的末尾
            new_batch_results = (
                f"<div id='batch-results'>{existing_content}{html_content}</div>"
            )

            # 替换旧的batch-results div
            self.batch_history_html = (
                self.batch_history_html[:batch_results_start]
                + new_batch_results
                + self.batch_history_html[batch_results_end + 6 :]
            )  # 6是"</div>"的长度
        else:
            # 如果batch-results div不存在，添加它
            self.batch_history_html = self.batch_history_html.replace(
                "</body>", f"<div id='batch-results'>{html_content}</div></body>"
            )

        # 使用JavaScript追加内容，这样不会重置JavaScript状态
        escaped_html = json.dumps(html_content)
        js = (
            "(function() {\n"
            "    const batchResults = document.getElementById('batch-results');\n"
            "    if (batchResults) {\n"
            "        batchResults.innerHTML += " + escaped_html + ";\n"
            "        \n"
            "        // 重新渲染MathJax公式\n"
            "        if (window.MathJax) {\n"
            "            MathJax.typesetPromise();\n"
            "        }\n"
            "        \n"
            "        // 智能滚动到底部\n"
            "        autoScrollToBottom();\n"
            "    }\n"
            "})();"
        )

        # 执行JavaScript来更新UI
        self.result_text.page().runJavaScript(js)

    def clear_results(self):
        """
        清空结果显示
        """
        self._init_web_content()
        self.batch_history_html = ""

    def get_html_content(self, callback):
        """
        获取当前HTML内容

        Args:
            callback: 回调函数，接收HTML内容
        """
        self.result_text.page().toHtml(callback)

    def reinit_ui(self):
        """
        重新初始化UI文本，用于语言切换
        """
        # 更新结果面板标题
        current_title = self.result_group.title()
        if current_title == i18n.translate(
            "batch_discussion_history"
        ) or current_title == i18n.translate("batch_debate_history"):
            # 标题已经是翻译后的，不需要改变
            pass
        else:
            # 更新为默认的处理结果标题
            self.result_group.setTitle(i18n.translate("batch_processing_results"))

        # 重新初始化HTML内容，以更新页面标题和其他文本
        self._init_web_content()
