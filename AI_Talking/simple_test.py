#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版语言切换测试程序
用于测试语言切换功能的核心逻辑
"""

import sys
import time
import traceback
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QComboBox
from PyQt5.QtCore import Qt, QTimer

# 导入项目中的必要模块
sys.path.append('src')
from utils.i18n_manager import i18n

class SimpleLanguageTest(QWidget):
    """
    简化版语言切换测试窗口
    """
    
    def __init__(self):
        """初始化测试窗口"""
        super().__init__()
        self.setWindowTitle("简化版语言切换测试")
        self.setGeometry(100, 100, 600, 400)
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化UI组件"""
        layout = QVBoxLayout()
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh-CN", "en", "ja", "ko", "de", "zh-TW"])
        layout.addWidget(self.language_combo)
        
        # 测试按钮
        self.test_button = QPushButton("测试语言切换")
        self.test_button.clicked.connect(self.test_language_switch)
        layout.addWidget(self.test_button)
        
        # 测试按钮功能
        self.test_button_func = QPushButton("测试按钮功能")
        self.test_button_func.clicked.connect(self.test_button_functionality)
        layout.addWidget(self.test_button_func)
        
        self.setLayout(layout)
        
        # 记录初始状态
        self.log(f"初始语言: {i18n.current_language}")
    
    def log(self, message):
        """记录测试日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        print(f"[{timestamp}] {message}")
    
    def test_language_switch(self):
        """测试语言切换功能"""
        try:
            # 获取选择的语言
            selected_lang = self.language_combo.currentText()
            self.log(f"开始测试语言切换到: {selected_lang}")
            
            # 记录开始时间
            start_time = time.time()
            
            # 触发语言切换
            i18n.set_language(selected_lang)
            
            # 记录结束时间
            end_time = time.time()
            elapsed = round(end_time - start_time, 2)
            
            self.log(f"语言切换到 {selected_lang} 完成，耗时: {elapsed}秒")
            self.log(f"当前语言: {i18n.current_language}")
            self.log(f"测试翻译: {i18n.translate('translate')}, {i18n.translate('edit')}, {i18n.translate('copy')}, {i18n.translate('delete')}")
            self.log("语言切换测试通过！")
            
        except Exception as e:
            error_msg = traceback.format_exc()
            self.log(f"语言切换测试失败: {str(e)}")
            self.log(f"错误堆栈: {error_msg}")
    
    def test_button_functionality(self):
        """测试按钮功能"""
        try:
            self.log("开始测试按钮功能...")
            
            # 测试翻译功能
            translate_text = i18n.translate('translate')
            edit_text = i18n.translate('edit')
            copy_text = i18n.translate('copy')
            delete_text = i18n.translate('delete')
            
            self.log(f"按钮文本翻译: {translate_text}, {edit_text}, {copy_text}, {delete_text}")
            
            # 模拟按钮点击逻辑
            self.log("模拟按钮点击事件绑定...")
            
            # 测试多个语言切换
            languages = ["zh-CN", "en", "ja", "zh-TW"]
            for lang in languages:
                i18n.set_language(lang)
                time.sleep(0.5)
                self.log(f"切换到 {lang}: {i18n.translate('translate')}")
            
            self.log("按钮功能测试通过！")
            
        except Exception as e:
            error_msg = traceback.format_exc()
            self.log(f"按钮功能测试失败: {str(e)}")
            self.log(f"错误堆栈: {error_msg}")

if __name__ == "__main__":
    """主函数"""
    try:
        app = QApplication(sys.argv)
        
        # 安装全局异常处理器
        def handle_exception(exctype, value, tb):
            """处理全局异常"""
            error_msg = ''.join(traceback.format_exception(exctype, value, tb))
            print(f"\n=== 程序崩溃 ===")
            print(f"错误类型: {exctype.__name__}")
            print(f"错误信息: {value}")
            print(f"错误堆栈:\n{error_msg}")
            print("================")
            
            # 保存错误日志到文件
            with open("simple_test_crash.log", "w", encoding="utf-8") as f:
                f.write(f"崩溃时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"错误类型: {exctype.__name__}\n")
                f.write(f"错误信息: {value}\n")
                f.write(f"错误堆栈:\n{error_msg}\n")
            
            # 调用原始异常处理器
            sys.__excepthook__(exctype, value, tb)
        
        sys.excepthook = handle_exception
        
        # 创建并显示窗口
        window = SimpleLanguageTest()
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec_())
    except Exception as e:
        print(f"启动程序时出错: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
