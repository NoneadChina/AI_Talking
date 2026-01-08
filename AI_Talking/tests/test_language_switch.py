#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言切换功能测试程序
用于测试讨论功能和辩论功能中的气泡按钮在语言切换时是否正常工作
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QComboBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

# 导入项目中的必要模块
sys.path.append('src')
from utils.i18n_manager import i18n
from ui.discussion.chat_history_panel import ChatHistoryPanel
from ui.debate.chat_history_panel import DebateChatHistoryPanel

class LanguageSwitchTest(QMainWindow):
    """
    语言切换测试窗口
    """
    
    def __init__(self):
        """初始化测试窗口"""
        super().__init__()
        self.setWindowTitle("语言切换功能测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化UI
        self.init_ui()
        
        # 记录测试结果
        self.test_results = []
        
    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 测试控制面板
        control_layout = QVBoxLayout()
        
        # 测试日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        control_layout.addWidget(self.log_text)
        
        # 语言选择下拉框
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh-CN", "zh-TW", "en", "ja", "ko", "de", "es", "fr", "ar", "ru"])
        control_layout.addWidget(self.language_combo)
        
        # 测试按钮
        self.test_switch_button = QPushButton("测试语言切换")
        self.test_switch_button.clicked.connect(self.test_language_switch)
        control_layout.addWidget(self.test_switch_button)
        
        self.test_discussion_button = QPushButton("测试讨论功能按钮")
        self.test_discussion_button.clicked.connect(self.test_discussion_buttons)
        control_layout.addWidget(self.test_discussion_button)
        
        self.test_debate_button = QPushButton("测试辩论功能按钮")
        self.test_debate_button.clicked.connect(self.test_debate_buttons)
        control_layout.addWidget(self.test_debate_button)
        
        self.run_all_tests_button = QPushButton("运行所有测试")
        self.run_all_tests_button.clicked.connect(self.run_all_tests)
        control_layout.addWidget(self.run_all_tests_button)
        
        main_layout.addLayout(control_layout)
        
        # 创建测试容器
        test_container = QWidget()
        test_layout = QVBoxLayout(test_container)
        
        # 添加讨论功能面板
        self.log("初始化讨论功能面板...")
        self.discussion_panel = ChatHistoryPanel()
        test_layout.addWidget(self.discussion_panel.chat_history_group)
        
        # 添加辩论功能面板
        self.log("初始化辩论功能面板...")
        self.debate_panel = DebateChatHistoryPanel()
        test_layout.addWidget(self.debate_panel.history_group)
        
        main_layout.addWidget(test_container)
        
        # 设置中心窗口
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
    def log(self, message):
        """记录测试日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
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
            
            # 等待UI更新
            QTimer.singleShot(1000, lambda: self.on_language_switch_completed(selected_lang, start_time))
            
        except Exception as e:
            self.log(f"语言切换测试失败: {str(e)}")
            self.test_results.append(("语言切换", selected_lang, "失败", str(e)))
    
    def on_language_switch_completed(self, lang, start_time):
        """语言切换完成后的回调"""
        try:
            # 记录结束时间
            end_time = time.time()
            elapsed = round(end_time - start_time, 2)
            
            self.log(f"语言切换到 {lang} 完成，耗时: {elapsed}秒")
            self.log(f"当前语言: {i18n.current_language}")
            
            # 验证UI组件是否正常
            self.log("验证UI组件是否正常...")
            
            # 检查讨论面板标题
            discussion_title = self.discussion_panel.chat_history_group.title()
            self.log(f"讨论面板标题: {discussion_title}")
            
            # 检查辩论面板标题
            debate_title = self.debate_panel.history_group.title()
            self.log(f"辩论面板标题: {debate_title}")
            
            # 验证按钮功能是否正常
            self.verify_buttons_functionality()
            
            self.test_results.append(("语言切换", lang, "成功", f"耗时: {elapsed}秒"))
            self.log("语言切换测试通过！")
            
        except Exception as e:
            self.log(f"语言切换后验证失败: {str(e)}")
            self.test_results.append(("语言切换", lang, "失败", str(e)))
    
    def verify_buttons_functionality(self):
        """验证按钮功能是否正常"""
        try:
            # 测试讨论功能按钮
            self.log("验证讨论功能按钮...")
            js_code = """
            (function() {
                const buttons = document.querySelectorAll('.action-button');
                console.log('讨论功能按钮数量:', buttons.length);
                return buttons.length;
            })();
            """
            
            def on_discussion_buttons_count(count):
                self.log(f"讨论功能按钮数量: {count}")
                if count > 0:
                    self.log("讨论功能按钮存在")
                else:
                    self.log("讨论功能按钮不存在")
            
            self.discussion_panel.chat_history_text.page().runJavaScript(js_code, on_discussion_buttons_count)
            
            # 测试辩论功能按钮
            self.log("验证辩论功能按钮...")
            js_code = """
            (function() {
                const buttons = document.querySelectorAll('.action-button');
                console.log('辩论功能按钮数量:', buttons.length);
                return buttons.length;
            })();
            """
            
            def on_debate_buttons_count(count):
                self.log(f"辩论功能按钮数量: {count}")
                if count > 0:
                    self.log("辩论功能按钮存在")
                else:
                    self.log("辩论功能按钮不存在")
            
            self.debate_panel.debate_history_text.page().runJavaScript(js_code, on_debate_buttons_count)
            
        except Exception as e:
            self.log(f"按钮验证失败: {str(e)}")
    
    def test_discussion_buttons(self):
        """测试讨论功能按钮"""
        try:
            self.log("开始测试讨论功能按钮...")
            
            # 添加测试消息
            self.discussion_panel.append_to_discussion_history("系统", "这是一条测试消息")
            self.discussion_panel.append_to_discussion_history("学者AI1", "这是AI1的测试消息")
            
            # 等待消息添加完成
            QTimer.singleShot(500, self._test_discussion_buttons_after_delay)
            
        except Exception as e:
            self.log(f"讨论功能按钮测试失败: {str(e)}")
            self.test_results.append(("讨论按钮", "", "失败", str(e)))
    
    def _test_discussion_buttons_after_delay(self):
        """延迟后测试讨论功能按钮"""
        try:
            # 测试按钮事件绑定
            js_code = """
            (function() {
                // 检查initMessageActions函数是否存在
                const has_init_function = typeof initMessageActions === 'function';
                console.log('initMessageActions函数存在:', has_init_function);
                
                // 调用initMessageActions函数
                if (has_init_function) {
                    initMessageActions();
                    console.log('调用initMessageActions成功');
                }
                
                // 检查按钮事件
                const translate_btn = document.querySelector('.translate-btn');
                const has_translate_event = translate_btn && typeof translate_btn.onclick === 'function';
                
                return {
                    has_init_function: has_init_function,
                    has_translate_event: has_translate_event
                };
            })();
            """
            
            def on_test_result(result):
                if result["has_init_function"]:
                    self.log("✓ initMessageActions函数存在")
                else:
                    self.log("✗ initMessageActions函数不存在")
                
                if result["has_translate_event"]:
                    self.log("✓ 翻译按钮事件已绑定")
                else:
                    self.log("✗ 翻译按钮事件未绑定")
                
                if result["has_init_function"] and result["has_translate_event"]:
                    self.log("讨论功能按钮测试通过！")
                    self.test_results.append(("讨论按钮", "", "成功", "按钮事件正常绑定"))
                else:
                    self.log("讨论功能按钮测试失败！")
                    self.test_results.append(("讨论按钮", "", "失败", "按钮事件未正常绑定"))
            
            self.discussion_panel.chat_history_text.page().runJavaScript(js_code, on_test_result)
            
        except Exception as e:
            self.log(f"讨论功能按钮测试失败: {str(e)}")
            self.test_results.append(("讨论按钮", "", "失败", str(e)))
    
    def test_debate_buttons(self):
        """测试辩论功能按钮"""
        try:
            self.log("开始测试辩论功能按钮...")
            
            # 添加测试消息
            self.debate_panel.append_to_debate_history("系统", "这是一条辩论测试消息")
            self.debate_panel.append_to_debate_history("正方AI", "这是正方AI的测试消息")
            
            # 等待消息添加完成
            QTimer.singleShot(500, self._test_debate_buttons_after_delay)
            
        except Exception as e:
            self.log(f"辩论功能按钮测试失败: {str(e)}")
            self.test_results.append(("辩论按钮", "", "失败", str(e)))
    
    def _test_debate_buttons_after_delay(self):
        """延迟后测试辩论功能按钮"""
        try:
            # 测试按钮事件绑定
            js_code = """
            (function() {
                // 检查initMessageActions函数是否存在
                const has_init_function = typeof initMessageActions === 'function';
                console.log('initMessageActions函数存在:', has_init_function);
                
                // 调用initMessageActions函数
                if (has_init_function) {
                    initMessageActions();
                    console.log('调用initMessageActions成功');
                }
                
                // 检查按钮事件
                const translate_btn = document.querySelector('.translate-btn');
                const has_translate_event = translate_btn && typeof translate_btn.onclick === 'function';
                
                return {
                    has_init_function: has_init_function,
                    has_translate_event: has_translate_event
                };
            })();
            """
            
            def on_test_result(result):
                if result["has_init_function"]:
                    self.log("✓ initMessageActions函数存在")
                else:
                    self.log("✗ initMessageActions函数不存在")
                
                if result["has_translate_event"]:
                    self.log("✓ 翻译按钮事件已绑定")
                else:
                    self.log("✗ 翻译按钮事件未绑定")
                
                if result["has_init_function"] and result["has_translate_event"]:
                    self.log("辩论功能按钮测试通过！")
                    self.test_results.append(("辩论按钮", "", "成功", "按钮事件正常绑定"))
                else:
                    self.log("辩论功能按钮测试失败！")
                    self.test_results.append(("辩论按钮", "", "失败", "按钮事件未正常绑定"))
            
            self.debate_panel.debate_history_text.page().runJavaScript(js_code, on_test_result)
            
        except Exception as e:
            self.log(f"辩论功能按钮测试失败: {str(e)}")
            self.test_results.append(("辩论按钮", "", "失败", str(e)))
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("\n=== 开始运行所有测试 ===")
        self.test_results.clear()
        
        # 测试初始状态
        self.log("测试初始状态...")
        self.test_discussion_buttons()
        self.test_debate_buttons()
        
        # 测试各种语言切换
        languages = ["zh-CN", "en", "ja", "ko", "de", "zh-TW"]
        
        def run_language_tests(index=0):
            if index < len(languages):
                lang = languages[index]
                self.language_combo.setCurrentText(lang)
                self.test_language_switch()
                QTimer.singleShot(2000, lambda: run_language_tests(index + 1))
            else:
                self.log("\n=== 所有测试完成 ===")
                self.log_test_results()
        
        QTimer.singleShot(1000, run_language_tests)
    
    def log_test_results(self):
        """记录测试结果"""
        self.log("\n=== 测试结果汇总 ===")
        
        passed = 0
        failed = 0
        
        for test_type, lang, status, message in self.test_results:
            if lang:
                test_desc = f"{test_type} ({lang})"
            else:
                test_desc = test_type
            
            if status == "成功":
                self.log(f"✓ {test_desc}: {status} - {message}")
                passed += 1
            else:
                self.log(f"✗ {test_desc}: {status} - {message}")
                failed += 1
        
        total = passed + failed
        self.log(f"\n总计: {total} 个测试，通过: {passed} 个，失败: {failed} 个")
        
        if failed == 0:
            self.log("🎉 所有测试通过！")
        else:
            self.log("❌ 部分测试失败，请检查日志！")

if __name__ == "__main__":
    """主函数"""
    import traceback
    
    try:
        app = QApplication(sys.argv)
        
        # 设置应用程序样式
        app.setStyle("Fusion")
        
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
            with open("test_crash.log", "w", encoding="utf-8") as f:
                f.write(f"崩溃时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"错误类型: {exctype.__name__}\n")
                f.write(f"错误信息: {value}\n")
                f.write(f"错误堆栈:\n{error_msg}\n")
            
            # 调用原始异常处理器
            sys.__excepthook__(exctype, value, tb)
        
        sys.excepthook = handle_exception
        
        # 创建测试窗口
        window = LanguageSwitchTest()
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec_())
    except Exception as e:
        print(f"启动程序时出错: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
