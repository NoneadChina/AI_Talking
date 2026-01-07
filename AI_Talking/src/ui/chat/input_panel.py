# -*- coding: utf-8 -*-
"""
聊天输入组件，支持文本输入、文件上传和快捷键
"""

import os
import base64
from io import BytesIO
from PIL import Image
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QMenu,
    QAction,
    QActionGroup,
    QStyle,
    QApplication,
)

# 导入国际化管理器
from utils.i18n_manager import i18n
# 导入资源管理器
from utils.resource_manager import ResourceManager
# 导入文件解析器
from utils.file_parser import file_parser_manager


class ChatInputWidget(QWidget):
    """
    聊天输入组件，支持文本输入、文件上传和快捷键

    信号:
        send_message: 发送消息信号，参数为消息内容
        search_mode_changed: 搜索模式变化信号，参数为搜索模式（"off"或"auto"）
        voice_input_toggled: 语音输入状态变化信号，参数为是否开启语音输入
    """

    send_message = pyqtSignal(str, str)  # 参数1: 原始消息（用于显示）, 参数2: 完整消息（用于传给模型）
    search_mode_changed = pyqtSignal(str)
    voice_input_toggled = pyqtSignal(bool)

    def __init__(self):
        """
        初始化聊天输入组件
        """
        super().__init__()
        # 当前搜索模式
        self.search_mode = "auto"  # 默认智能搜索
        # 解析的文件内容缓存字典 {文件名: 解析内容}
        self.parsed_files_cache = {}  # 存储已解析的文件内容
        self.init_ui()

        # 连接语言变化信号
        i18n.language_changed.connect(self.reinit_ui)

    def init_ui(self):
        """
        初始化聊天输入UI
        """
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 输入区域
        self.input_text_edit = QTextEdit()
        self.input_text_edit.setPlaceholderText(
            i18n.translate("chat_input_placeholder")
        )
        self.input_text_edit.setMaximumHeight(100)
        self.input_text_edit.textChanged.connect(self.update_height)
        self.input_text_edit.keyPressEvent = self.key_press_event
        self.input_text_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-size: 10pt;
                background-color: #ffffff;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            QTextEdit:focus {
                border-color: #4caf50;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
                outline: none;
            }
        """
        )

        layout.addWidget(self.input_text_edit)

        # 操作栏
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        # 创建左侧工具按钮布局
        left_tools_layout = QHBoxLayout()
        left_tools_layout.setSpacing(8)
        
        # 1. 文件上传按钮（使用自定义PNG图标）
        self.upload_button = QPushButton()
        self.upload_button.setIcon(ResourceManager.load_icon("upload_file.png"))  # 使用自定义上传PNG图标
        self.upload_button.setToolTip(i18n.translate("upload_file_tooltip"))
        self.upload_button.setStyleSheet(
            """
            QPushButton {
                padding: 2px;
                border: 1px solid transparent;
                border-radius: 4px;
                background-color: transparent;
                transition: all 0.2s ease;
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
                icon-size: 24px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
                border-color: rgba(0, 0, 0, 0.1);
            }
            QPushButton:active {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        
        # 创建上传按钮下拉菜单
        upload_menu = QMenu(self.upload_button)
        
        # 上传图片选项
        upload_image_action = QAction(i18n.translate("upload_image"), upload_menu)
        upload_image_action.triggered.connect(self.upload_image)
        upload_menu.addAction(upload_image_action)
        
        # 上传文件选项
        upload_file_action = QAction(i18n.translate("upload_file"), upload_menu)
        upload_file_action.triggered.connect(self.upload_file)
        upload_menu.addAction(upload_file_action)
        
        # 上传文件夹选项
        upload_folder_action = QAction(i18n.translate("upload_folder"), upload_menu)
        upload_folder_action.triggered.connect(self.upload_folder)
        upload_menu.addAction(upload_folder_action)
        
        # 设置菜单
        self.upload_button.setMenu(upload_menu)
        left_tools_layout.addWidget(self.upload_button)

        # 2. 智能搜索按钮（使用自定义PNG图标）
        self.search_button = QPushButton()
        self.search_button.setIcon(ResourceManager.load_icon("Internet_Search.png"))  # 使用自定义搜索PNG图标
        self.search_button.setToolTip(i18n.translate("smart_search_tooltip"))
        self.search_button.setStyleSheet(
            """
            QPushButton {
                padding: 2px;
                border: 1px solid transparent;
                border-radius: 4px;
                background-color: transparent;
                transition: all 0.2s ease;
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
                icon-size: 24px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
                border-color: rgba(0, 0, 0, 0.1);
            }
            QPushButton:active {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        
        # 创建搜索按钮下拉菜单
        search_menu = QMenu(self.search_button)
        
        # 创建搜索模式动作组
        self.search_mode_group = QActionGroup(search_menu)
        self.search_mode_group.setExclusive(True)
        
        # 关闭搜索选项
        search_off_action = QAction(i18n.translate("search_mode_off"), self.search_mode_group)
        search_off_action.setCheckable(True)
        search_off_action.setData("off")
        search_off_action.triggered.connect(lambda: self.set_search_mode("off"))
        search_menu.addAction(search_off_action)
        
        # 智能搜索选项
        search_auto_action = QAction(i18n.translate("search_mode_auto"), self.search_mode_group)
        search_auto_action.setCheckable(True)
        search_auto_action.setData("auto")
        search_auto_action.triggered.connect(lambda: self.set_search_mode("auto"))
        search_menu.addAction(search_auto_action)
        
        # 设置当前模式为选中状态
        for action in self.search_mode_group.actions():
            if action.data() == self.search_mode:
                action.setChecked(True)
                break
        
        # 设置菜单
        self.search_button.setMenu(search_menu)
        left_tools_layout.addWidget(self.search_button)

        # 3. 语音输入按钮（使用自定义PNG图标）
        self.voice_button = QPushButton()
        self.voice_button.setIcon(ResourceManager.load_icon("voice.png"))  # 使用自定义语音PNG图标
        self.voice_button.setCheckable(True)  # 可切换状态
        self.voice_button.setToolTip(i18n.translate("voice_input_tooltip"))
        self.voice_button.setStyleSheet(
            """
            QPushButton {
                padding: 2px;
                border: 1px solid transparent;
                border-radius: 4px;
                background-color: transparent;
                transition: all 0.2s ease;
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
                icon-size: 24px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
                border-color: rgba(0, 0, 0, 0.1);
            }
            QPushButton:active {
                background-color: rgba(0, 0, 0, 0.1);
            }
            QPushButton:checked {
                background-color: rgba(33, 150, 243, 0.1);
                border-color: rgba(33, 150, 243, 0.3);
            }
        """)
        self.voice_button.clicked.connect(self.toggle_voice_input)
        left_tools_layout.addWidget(self.voice_button)

        action_layout.addLayout(left_tools_layout)
        action_layout.addStretch(1)

        # 发送按钮
        self.send_button = QPushButton(i18n.translate("chat_send"))
        self.send_button.clicked.connect(self.send_message_handler)
        self.send_button.setStyleSheet(
            """
            QPushButton {
                padding: 9px 24px;
                border: none;
                border-radius: 6px;
                background-color: #4caf50;
                color: white;
                font-size: 10pt;
                font-weight: bold;
                transition: all 0.2s ease;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #43a047;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QPushButton:active {
                background-color: #388e3c;
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
                cursor: not-allowed;
            }
        """)
        action_layout.addWidget(self.send_button)

        layout.addLayout(action_layout)

        self.setLayout(layout)

    def update_height(self):
        """
        自动调整输入框高度
        """
        # 禁用固定高度限制，允许自动调整
        self.input_text_edit.setFixedHeight(0)

        content_height = self.input_text_edit.document().size().height()
        max_height = 200
        min_height = 30

        # 计算合适的高度，添加20px的内边距
        new_height = int(content_height + 20)

        if new_height < min_height:
            new_height = min_height
        elif new_height > max_height:
            new_height = max_height

        # 使用setFixedHeight来设置精确的高度
        self.input_text_edit.setFixedHeight(new_height)

    def key_press_event(self, event):
        """
        处理按键事件：回车发送，Shift+回车换行
        """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if not (event.modifiers() & Qt.ShiftModifier):
                self.send_message_handler()
                return

        QTextEdit.keyPressEvent(self.input_text_edit, event)

    def send_message_handler(self):
        """
        处理发送消息事件，将文件名替换为解析的文件内容
        发送两个参数：原始消息（用于显示）和完整消息（用于传给模型）
        """
        message = self.input_text_edit.toPlainText().strip()
        if message:
            # 保存原始消息（用于显示）
            original_message = message
            
            # 替换原始消息中的图片文件名标记为base64编码的图片（用于显示图片）
            # 只替换图片文件，非图片文件仍显示文件名
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
            for file_name, parsed_content in self.parsed_files_cache.items():
                if file_name.lower().endswith(image_extensions):
                    # 图片文件：显示为图片
                    original_message = original_message.replace(file_name, parsed_content)
            
            # 替换文件名标记为解析的内容（用于传给模型）
            full_message = message
            for file_name, parsed_content in self.parsed_files_cache.items():
                full_message = full_message.replace(file_name, parsed_content)

            # 发送消息：原始消息用于显示，完整消息用于传给模型
            self.send_message.emit(original_message, full_message)

            # 清空输入框和缓存
            self.input_text_edit.clear()
            self.input_text_edit.setFixedHeight(30)
            self.parsed_files_cache = {}

    def upload_file(self):
        """
        处理文件上传，在上传时就解析文件为Markdown并保存到缓存
        所有上传的文件名放在第一行，多个文件用分号隔开
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, i18n.translate("select_file"), "", "Documents (*.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf *.md *.html *.txt);;All Files (*.*)"
        )
        if file_path:
            file_name = os.path.basename(file_path)
            
            # 在上传时就解析文件内容并保存到缓存
            print(f"正在解析文件: {file_name}")
            parsed_content = file_parser_manager.parse_file(file_path)
            self.parsed_files_cache[file_name] = parsed_content
            print(f"文件解析完成: {file_name}")

            # 获取当前输入框内容
            current_text = self.input_text_edit.toPlainText()
            lines = current_text.split('\n')
            
            # 处理文件名行
            if not lines[0].strip():
                # 输入框为空，添加文件名作为第一行
                new_content = f"{file_name}\n\n"
            elif lines[0].strip() and not any(file in lines[0] for file in self.parsed_files_cache.keys()):
                # 第一行有内容但不是文件名行，将其下移
                new_content = f"{file_name}\n\n{current_text}"
            else:
                # 第一行已有文件名，添加新文件名
                existing_files = [f.strip() for f in lines[0].split(';') if f.strip()]
                if file_name not in existing_files:
                    existing_files.append(file_name)
                # 重新构建内容，所有文件名放在第一行，用分号隔开
                new_content = f"{'; '.join(existing_files)}\n\n"
                # 添加剩余内容（如果有）
                if len(lines) > 1:
                    remaining_content = '\n'.join(lines[1:])
                    if remaining_content.strip():
                        new_content += remaining_content
            
            # 设置新内容
            self.input_text_edit.setPlainText(new_content)
            
            # 将光标定位到第二行的最后
            cursor = self.input_text_edit.textCursor()
            cursor.movePosition(cursor.End)
            self.input_text_edit.setTextCursor(cursor)
            
            self.input_text_edit.setFocus()

    def upload_image(self):
        """
        处理图片上传，支持多模态模型
        将图片转换为base64编码，以便模型直接处理
        """
        # 支持的图片类型
        image_filter = "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All Files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, i18n.translate("upload_image"), "", image_filter
        )
        if file_path:
            file_name = os.path.basename(file_path)
            
            # 图片处理：转换为base64编码，用于多模态模型
            print(f"正在处理图片: {file_name}")
            try:
                # 使用PIL打开图片
                with Image.open(file_path) as img:
                    # 调整图片大小（可选，根据模型要求）
                    max_size = 1024
                    img.thumbnail((max_size, max_size))
                    
                    # 转换为base64编码
                    buffered = BytesIO()
                    img_format = img.format if img.format else "PNG"  # 默认使用PNG格式
                    img.save(buffered, format=img_format)
                    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    
                    # 构建多模态模型支持的图片格式
                    # 常见格式：![image](data:image/png;base64,base64_data)
                    image_markdown = f"![{file_name}](data:image/{img_format.lower()};base64,{img_base64})"
                    
                    # 保存图片信息到缓存
                    self.parsed_files_cache[file_name] = image_markdown
                    print(f"图片处理完成: {file_name}")
            except Exception as e:
                print(f"图片处理失败: {e}")
                # 处理失败时，保存原始路径
                self.parsed_files_cache[file_name] = f"[IMAGE:{file_path}]"

            # 获取当前输入框内容
            current_text = self.input_text_edit.toPlainText()
            lines = current_text.split('\n')
            
            # 处理文件名行，图片名和文件名一起显示
            if not lines[0].strip():
                # 输入框为空，添加图片名作为第一行
                new_content = f"{file_name}\n\n"
            elif lines[0].strip() and not any(file in lines[0] for file in self.parsed_files_cache.keys()):
                # 第一行有内容但不是文件名行，将其下移
                new_content = f"{file_name}\n\n{current_text}"
            else:
                # 第一行已有文件名，添加新图片名
                existing_files = [f.strip() for f in lines[0].split(';') if f.strip()]
                if file_name not in existing_files:
                    existing_files.append(file_name)
                # 重新构建内容，所有文件名/图片名放在第一行，用分号隔开
                new_content = f"{'; '.join(existing_files)}\n\n"
                # 添加剩余内容（如果有）
                if len(lines) > 1:
                    remaining_content = '\n'.join(lines[1:])
                    if remaining_content.strip():
                        new_content += remaining_content
            
            # 设置新内容
            self.input_text_edit.setPlainText(new_content)
            
            # 将光标定位到第二行的最后
            cursor = self.input_text_edit.textCursor()
            cursor.movePosition(cursor.End)
            self.input_text_edit.setTextCursor(cursor)
            
            self.input_text_edit.setFocus()

    def upload_folder(self):
        """
        处理文件夹上传
        """
        folder_path = QFileDialog.getExistingDirectory(
            self, i18n.translate("select_folder")
        )
        if folder_path:
            # 这里可以添加文件夹上传逻辑
            self.send_message.emit(f"[文件夹上传] {os.path.basename(folder_path)}")

    def set_search_mode(self, mode):
        """
        设置搜索模式
        
        Args:
            mode: 搜索模式，"off"表示关闭搜索，"auto"表示智能搜索
        """
        self.search_mode = mode
        # 更新菜单中选中的动作
        for action in self.search_mode_group.actions():
            if action.data() == mode:
                action.setChecked(True)
                break
        # 发送搜索模式变化信号
        self.search_mode_changed.emit(mode)
        # 更新按钮提示文本，显示当前模式
        tooltip = f"{i18n.translate('smart_search')} ({i18n.translate(f'search_mode_{mode}')})"
        self.search_button.setToolTip(tooltip)

    def toggle_voice_input(self, checked):
        """
        切换语音输入状态
        
        Args:
            checked: 语音输入是否开启
        """
        # 发送语音输入状态变化信号
        self.voice_input_toggled.emit(checked)
        # 更新按钮提示文本，显示当前状态
        state = i18n.translate('voice_input_on') if checked else i18n.translate('voice_input_off')
        tooltip = f"{i18n.translate('voice_input')} ({state})"
        self.voice_button.setToolTip(tooltip)

    def reinit_ui(self):
        """
        重新初始化UI，用于语言切换时更新界面
        """
        # 更新输入框占位符
        self.input_text_edit.setPlaceholderText(
            i18n.translate("chat_input_placeholder")
        )

        # 更新按钮提示文本
        self.upload_button.setToolTip(i18n.translate("upload_file_tooltip"))
        tooltip = f"{i18n.translate('smart_search_tooltip')} ({i18n.translate(f'search_mode_{self.search_mode}')})"
        self.search_button.setToolTip(tooltip)
        state = i18n.translate('voice_input_on') if self.voice_button.isChecked() else i18n.translate('voice_input_off')
        tooltip = f"{i18n.translate('voice_input_tooltip')} ({state})"
        self.voice_button.setToolTip(tooltip)
        self.send_button.setText(i18n.translate("chat_send"))
        
        # 更新上传菜单文本
        if hasattr(self, 'upload_button') and self.upload_button.menu():
            menu = self.upload_button.menu()
            actions = menu.actions()
            if len(actions) >= 3:
                actions[0].setText(i18n.translate("upload_image"))
                actions[1].setText(i18n.translate("upload_file"))
                actions[2].setText(i18n.translate("upload_folder"))
        
        # 更新搜索菜单文本
        if hasattr(self, 'search_button') and self.search_button.menu():
            menu = self.search_button.menu()
            actions = menu.actions()
            if len(actions) >= 2:
                actions[0].setText(i18n.translate("search_mode_off"))
                actions[1].setText(i18n.translate("search_mode_auto"))
