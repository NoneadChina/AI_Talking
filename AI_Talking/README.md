# AI Talking

AI Talking 是一个基于 Python 和 PyQt5 开发的多功能 AI 交互应用，支持多种 AI 模型和交互模式，包括聊天、讨论、辩论和批量处理等功能。

## 功能特性

### 🔹 聊天功能
- 支持与多种 AI 模型进行单轮和多轮对话
- 实时显示对话内容和模型响应
- 支持切换不同的 AI 服务提供商
- 支持修改、复制和删除聊天历史消息
- 提供富文本编辑功能，支持格式化文本
- 支持消息翻译功能，可将消息翻译为多种语言
- 智能滚动功能，支持手动滚动暂停和滚动到底部恢复自动滚动

### 🔹 讨论功能
- 支持多 AI 模型之间的协作讨论
- 可以配置多个 AI 服务和模型参与讨论
- 实时显示讨论进程和结果
- 支持修改、复制和删除讨论历史消息
- 提供富文本编辑功能，支持格式化文本
- 支持消息翻译功能，可将讨论内容翻译为多种语言
- 智能滚动功能，支持手动滚动暂停和滚动到底部恢复自动滚动

### 🔹 辩论功能
- 支持设置正反方 AI 模型进行辩论
- 可配置辩论主题、规则和评判标准
- 实时显示辩论过程和结果
- 支持修改、复制和删除辩论历史消息
- 提供富文本编辑功能，支持格式化文本
- 支持消息翻译功能，可将辩论内容翻译为多种语言
- 智能滚动功能，支持手动滚动暂停和滚动到底部恢复自动滚动

### 🔹 国际化支持
- 支持 10 种语言：简体中文、繁体中文、英语、日语、韩语、德语、西班牙语、法语、阿拉伯语、俄语
- 所有 UI 元素和提示信息均可随语言切换
- 支持自动检测系统语言并应用

### 🔹 API 设置
- 支持配置多种 AI 服务提供商的 API 密钥
- 可设置默认模型和系统提示词
- 支持 API 请求参数的自定义配置
- 支持 API 密钥的安全存储

### 🔹 历史记录管理
- 自动保存所有对话和交互历史
- 支持历史记录的搜索、查看和删除
- 支持历史记录的导出和导入
- 实现了"一个模型一条历史"的逻辑，避免重复记录

### 🔹 自动更新
- 支持应用程序的自动检查更新
- 可配置更新频率和更新方式
- 支持下载和安装更新包

### 🔹 用户体验优化
- 启动画面，提升用户体验
- 友好的错误提示和处理机制
- 响应式设计，适配不同屏幕尺寸
- 流畅的动画效果，提升交互体验

### 🔹 安全和可靠性
- API 密钥的安全存储
- 完善的错误监控和处理机制
- 线程安全的设计，避免并发问题
- 资源自动清理，避免内存泄漏

## 技术栈

| 分类 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 开发语言 | Python | 3.12+ | 后端和桌面应用开发 |
| GUI 框架 | PyQt5 | 5.x | 桌面GUI开发 |
| 配置管理 | PyYAML | 6.x | 应用配置管理 |
| 配置管理 | python-dotenv | 1.x | 环境变量管理 |
| 日志系统 | logging | 内置 | 日志记录 |
| HTTP 客户端 | requests | 2.31+ | API 请求处理 |
| Markdown 渲染 | markdown | 3.5+ | Markdown 内容渲染 |
| 富文本编辑 | Quill | 2.0+ | 富文本编辑功能 |
| 国际化 | 自定义 i18n 系统 | - | 多语言支持 |
| 安全存储 | 自定义 secure_storage | - | API 密钥安全存储 |
| 线程管理 | ThreadPoolExecutor | 内置 | 线程池管理 |
| 测试框架 | pytest | 8.x | 单元测试和集成测试 |
| 类型检查 | mypy | 1.x | 类型检查 |
| 代码格式化 | Black | 23.x | 代码格式化 |

### 支持的 AI 服务

| AI 服务 | 类型 | 用途 |
|--------|------|------|
| Ollama | 本地模型 | 本地部署的 AI 模型 |
| OpenAI | 云端 API | 云端 AI 服务 |
| DeepSeek | 云端 API | 云端 AI 服务 |
| Google Gemini | 云端 API | 云端 AI 服务 |
| Anthropic | 云端 API | 云端 AI 服务 |

## 安装说明

### 前置要求

- Python 3.10 或更高版本
- pip 包管理器

### 安装步骤

1. 克隆项目仓库
   ```bash
   git clone http://git.corp.nonead.com/tonyke/ai_talking.git
   cd ai_talking
   ```

2. 安装依赖包
   ```bash
   pip install -r requirements.txt
   ```

3. **启动应用**
   ```bash
   python src/main.py
   ```
   或使用批处理文件
   ```bash
   run_app.bat
   ```

## 使用方法

### 基本使用

1. **启动应用程序**
   - 双击 `run_app.bat` 文件或运行 `python src/main.py`

2. **配置 API 设置**
   - 点击 "设置" 标签页
   - 输入您的 AI 服务 API 密钥
   - 选择默认模型和系统提示词
   - 点击 "保存设置"

3. **开始聊天**
   - 点击 "聊天" 标签页
   - 输入您的问题或消息
   - 选择 AI 服务和模型
   - 点击 "发送" 按钮

4. **参与讨论**
   - 点击 "讨论" 标签页
   - 配置参与讨论的 AI 服务和模型
   - 输入讨论主题
   - 点击 "开始讨论"

5. **观看辩论**
   - 点击 "辩论" 标签页
   - 配置正反方 AI 模型
   - 输入辩论主题
   - 点击 "开始辩论"

### 高级功能

- **历史记录管理**
  - 点击 "历史" 标签页查看所有历史记录
  - 使用搜索功能查找特定对话
  - 可删除或导出历史记录

- **更新应用**
  - 应用启动时会自动检查更新
  - 也可以在 "关于" 标签页手动检查更新

## 项目结构

```
ai_talking/
├── releases/           # 版本发布目录
│   ├── v0.1.6/          # 历史版本发布记录
│   ├── v0.1.7/
│   ├── v0.1.8/
│   ├── v0.3.0/          # 0.3.x 版本发布记录
│   ├── v0.3.1/
│   ├── v0.3.2/
│   ├── v0.3.3/
│   ├── v0.3.4/
│   ├── v0.3.5/
│   ├── v0.3.6/
│   ├── v0.3.7/
│   ├── v0.3.8/
│   ├── v0.3.9/
│   ├── v0.3.10/
│   ├── v0.4.0/          # 0.4.x 版本发布记录
│   ├── v0.4.1/
│   └── v1.0.0/          # 1.0.0 正式版发布记录
├── resources/          # 资源文件目录
│   └── icon.ico        # 应用程序图标
├── scripts/            # 脚本文件目录
│   └── update_version.py  # 版本更新脚本
├── src/                # 主源代码目录
│   ├── i8n/             # 国际化翻译文件
│   │   ├── ar.json      # 阿拉伯语
│   │   ├── de.json      # 德语
│   │   ├── en.json      # 英语
│   │   ├── es.json      # 西班牙语
│   │   ├── fr.json      # 法语
│   │   ├── ja.json      # 日语
│   │   ├── ko.json      # 韩语
│   │   ├── ru.json      # 俄语
│   │   ├── zh-CN.json   # 简体中文
│   │   └── zh-TW.json   # 繁体中文
│   ├── resources/       # 应用内部资源
│   │   └── icon.ico     # 应用图标
│   ├── ui/              # UI 组件目录
│   │   ├── chat/        # 聊天功能相关组件
│   │   │   ├── __init__.py
│   │   │   ├── ai_config_panel.py  # AI 配置面板
│   │   │   ├── chat_list_widget.py  # 聊天列表组件
│   │   │   ├── config_panel.py      # 聊天配置面板
│   │   │   ├── controls_panel.py    # 聊天控制面板
│   │   │   ├── input_panel.py       # 输入面板
│   │   │   └── message_widget.py    # 消息组件
│   │   ├── debate/      # 辩论功能相关组件
│   │   │   ├── __init__.py
│   │   │   ├── ai_config_panel.py  # AI 配置面板
│   │   │   ├── chat_history_panel.py  # 聊天历史面板
│   │   │   ├── config_panel.py      # 辩论配置面板
│   │   │   ├── controls_panel.py    # 辩论控制面板
│   │   │   └── debate_tab.py        # 辩论标签页
│   │   ├── discussion/  # 讨论功能相关组件
│   │   │   ├── __init__.py
│   │   │   ├── ai_config_panel.py  # AI 配置面板
│   │   │   ├── chat_history_panel.py  # 聊天历史面板
│   │   │   ├── config_panel.py      # 讨论配置面板
│   │   │   ├── controls_panel.py    # 讨论控制面板
│   │   │   └── discussion_tab.py    # 讨论标签页
│   │   ├── about_tab.py             # 关于标签页
│   │   ├── api_settings.py          # API 设置页面
│   │   ├── chat_tab.py              # 聊天标签页
│   │   ├── debate_tab.py            # 辩论标签页
│   │   ├── discussion_tab.py        # 讨论标签页
│   │   ├── history_management_tab.py  # 历史记录管理标签页
│   │   ├── splash_screen.py         # 启动画面
│   │   └── ui_utils.py              # UI 工具函数
│   ├── utils/          # 工具类目录
│   │   ├── __init__.py
│   │   ├── ai_service.py            # AI 服务封装
│   │   ├── chat_history_manager.py  # 聊天历史管理
│   │   ├── config_manager.py        # 配置管理
│   │   ├── error_monitor.py         # 错误监控
│   │   ├── i18n_manager.py          # 国际化管理
│   │   ├── logger_config.py         # 日志配置
│   │   ├── model_manager.py         # 模型管理
│   │   ├── resource_manager.py      # 资源管理
│   │   ├── secure_storage.py        # 安全存储
│   │   ├── thread_manager.py        # 线程管理
│   │   └── update_service.py        # 更新服务
│   ├── __init__.py     # 项目初始化文件，包含版本信息
│   ├── config.yaml     # 应用配置文件
│   └── main.py         # 主应用程序入口
├── tests/              # 测试文件目录
│   ├── __init__.py
│   ├── test_ai_service.py           # AI 服务测试
│   ├── test_chat_history_manager.py  # 聊天历史管理测试
│   ├── test_error_monitor.py        # 错误监控测试
│   ├── test_integration.py          # 集成测试
│   ├── test_thread_manager.py       # 线程管理测试
│   └── test_thread_manager_extended.py  # 线程管理扩展测试
├── .gitignore          # Git 忽略文件
├── AI_CHAT_DELAY_OPTIMIZATION.md  # AI 聊天延迟优化说明
├── ARCHITECTURE.md     # 架构设计文档
├── AUTO_UPDATE_README.md  # 自动更新说明
├── CHANGELOG.md        # 版本变更记录
├── INSTALL_README.md   # 安装说明
├── README.md          # 项目说明文档
├── requirements.txt   # 依赖包列表
├── run_app.bat        # 应用程序启动脚本
└── check_i18n.py      # 国际化检查脚本
```

## 配置说明

### 配置文件说明

AI Talking 使用 `config.yaml` 文件进行配置管理，该文件位于应用程序根目录下的 `src` 文件夹中。配置文件采用 YAML 格式，包含以下主要配置项：

```yaml
# API 配置
api:
  deepseek_key: your_deepseek_api_key  # DeepSeek API 密钥
  max_retries: 3  # API 请求最大重试次数
  ollama_base_url: http://localhost:11434  # Ollama 本地服务 URL
  ollama_cloud_base_url: https://ollama.com  # Ollama 云端服务 URL
  ollama_cloud_key: your_ollama_cloud_key  # Ollama 云端 API 密钥
  openai_key: your_openai_api_key  # OpenAI API 密钥
  retry_delay: 2.0  # API 请求重试延迟（秒）
  timeout: 300  # API 请求超时时间（秒）

# 应用程序基本配置
app:
  debug: false  # 是否启用调试模式
  language: auto  # 应用语言（auto: 自动检测系统语言）
  name: AI Talking  # 应用名称
  version: 0.4.0  # 应用版本
  window:  # 窗口设置
    height: 1000  # 窗口高度
    width: 900  # 窗口宽度
    x: 100  # 窗口初始 X 坐标
    y: 100  # 窗口初始 Y 坐标

# 聊天功能配置
chat:
  auto_save: true  # 是否自动保存聊天历史
  max_history_length: 50  # 最大聊天历史长度
  save_interval: 30  # 自动保存间隔（秒）
  system_prompt: "你的聊天系统提示词..."  # 聊天系统提示词

# 辩论功能配置
debate:
  ai1_prompt: "正方辩手提示词..."  # 正方辩手提示词
  ai2_prompt: "反方辩手提示词..."  # 反方辩手提示词
  judge_ai3_prompt: "裁判AI提示词..."  # 裁判AI提示词
  system_prompt: "辩论系统提示词..."  # 辩论系统提示词

# 讨论功能配置
discussion:
  ai1_prompt: "分析型学者提示词..."  # 分析型学者提示词
  ai2_prompt: "综合型学者提示词..."  # 综合型学者提示词
  expert_ai3_prompt: "专家AI提示词..."  # 专家AI提示词
  system_prompt: "讨论系统提示词..."  # 讨论系统提示词

# 翻译功能配置
translation:
  default_model: deepseek-v3.1:671b-cloud  # 默认翻译模型
  provider: Ollama  # 翻译服务提供商
  system_prompt: "翻译系统提示词..."  # 翻译系统提示词

# 更新功能配置
update:
  auto_check: true  # 是否自动检查更新
  auto_update: false  # 是否自动更新
  check_interval: 24  # 自动检查更新间隔（小时）
```

### 配置管理

应用程序首次运行时会自动生成 `config.yaml` 文件，并使用默认配置。您可以通过以下方式修改配置：

1. **通过应用界面修改**：在应用程序的 "设置" 标签页中可以直观地修改各项配置，修改后会自动保存到 `config.yaml` 文件。
2. **手动编辑配置文件**：直接编辑 `src/config.yaml` 文件，修改后重启应用程序即可生效。

### 安全说明

- API 密钥在配置文件中会被加密存储，确保安全性
- 建议定期备份 `config.yaml` 文件，以防数据丢失
- 不要将包含敏感信息的 `config.yaml` 文件分享给他人

### 应用程序配置

在应用程序的 "设置" 标签页中可以配置：

- 默认 AI 服务提供商
- 默认 AI 模型
- 系统提示词
- API 请求参数
- 更新设置

## 开发指南

### 开发环境搭建

1. 克隆项目仓库
2. 安装依赖包
3. 配置开发环境变量
4. 运行开发版本
   ```bash
   python src/main.py
   ```

### 代码结构

- **UI 组件**: 位于 `src/ui/` 目录，每个标签页对应一个 Python 文件
- **工具类**: 位于 `src/utils/` 目录，提供各种服务和功能封装
- **主程序**: `src/main.py` 整合所有组件，启动应用程序

### 测试

运行测试用例：
```bash
pytest tests/
```

## 构建和发布

### 打包应用程序

使用 PyInstaller 打包应用程序：
```bash
pyinstaller AI_Talking.spec
```

### 生成安装程序

使用 Inno Setup 生成 Windows 安装程序：
```bash
ISCC AI_Talking_Setup.iss
```

## 贡献指南

1. Fork 项目仓库
2. 创建特性分支
   ```bash
   git checkout -b feature/your-feature
   ```
3. 提交更改
   ```bash
   git commit -m "Add your feature"
   ```
4. 推送分支
   ```bash
   git push origin feature/your-feature
   ```
5. 创建合并请求

## 许可证

本项目采用 MIT 许可证。详情请查看 LICENSE 文件。

## 联系信息

- 项目负责人: Tony Ke
- 公司: NONEAD Corporation
- 邮箱: tony.ke@nonead.com

## 版本历史

- v1.0.0 (2026-01-05): 正式版发布
  - 修复讨论和辩论功能中按钮文字不随语言变化的问题
  - 优化按钮功能和语言同步机制
  - 完善国际化支持

- v0.4.1 (2026-01-02): 修复bug与功能优化
  - 修复辩论功能中AI1和AI2输出重复气泡的问题
  - 实现系统提示词环境变量在保存API配置时立即生效
  - 修复其他一些小问题

- v0.4.0 (2025-12-31): 重大功能更新与优化
  - 根据不同操作系统优化logo图片加载方法
  - 将配置文件、log文件和api加密txt文件存入用户目录
  - 删除批量标签页及相关功能代码
  - 修复点击关于标签页显示历史标签页内容的bug
  - 优化PyQt5 tab widget管理
  - 增强资源路径处理和错误处理

- v0.3.10 (2025-12-28): 版本更新
  - 更新版本号从0.3.9到0.3.10

- v0.3.9 (2025-12-28): 版本更新
  - 更新版本号从0.3.8到0.3.9

- v0.3.8 (2025-12-28): 版本更新
  - 更新版本号从0.3.7到0.3.8

- v0.3.7 (2025-12-26): 讨论功能增强与国际化优化
  - 在讨论历史气泡中添加了"修改"按钮，按钮顺序调整为：修改、复制、删除
  - 实现了修改气泡内容的功能，支持自动保存
  - 修复了按钮功能失效问题，确保修改、复制、删除功能正常工作
  - 优化了所有国际化语言包（ar.json, de.json, es.json, fr.json, ko.json, ru.json）
  - 确保翻译准确、简洁，符合短语或短句形式
  - 以英文语言包为基准，保持翻译一致性

- v0.3.6 (2025-12-25): 国际化支持增强
  - 支持韩语、德语、西班牙语、法语、阿拉伯语和俄罗斯语
  - 修复讨论历史按钮功能
  - 修复语言切换问题
  - 确保状态信息随语言变化
  - 更新AI_Talking.spec文件，优化打包配置

- v0.3.5 (2025-12-24): 版本更新
  - 更新版本号从0.3.4到0.3.5

- v0.3.4 (2025-12-23): 功能优化
  - 优化聊天历史消息管理
  - 增强富文本编辑功能
  - 改进API设置界面

- v0.1.0 (2025-12-18): 初始版本发布
  - 实现聊天、讨论、辩论和批量处理功能
  - 支持多种 AI 服务提供商
  - 实现 API 设置和历史记录管理
  - 添加自动更新功能

## 未来计划

- [ ] 支持更多 AI 服务提供商
- [ ] 实现语音交互功能
- [ ] 添加更多 AI 交互模式
- [ ] 优化用户界面和用户体验
- [ ] 增强数据安全和隐私保护
- [ ] 支持更多语言和地区

---

**AI Talking** - 让 AI 交互更加智能、高效、有趣！