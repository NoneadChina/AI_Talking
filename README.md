# AI Talking


AI Talking 是一个功能强大的AI对话系统，支持单聊、讨论、辩论等多种模式，同时提供桌面应用和Web应用两种部署方式。

## 项目结构

项目分为三个主要部分：

1. **AI_Talking** - 新版桌面应用，采用MVC架构，代码模块化，支持单聊、讨论、辩论和批量处理等多种模式
   - 采用PyQt5框架开发GUI
   - 支持OpenAI、DeepSeek和Ollama API
   - 模块化设计，代码结构清晰
   - 支持多轮对话和历史记录管理

2. **AI_Talking_Web** - Web应用，前后端分离，支持在线使用
   - 前端使用TypeScript开发
   - 后端使用FastAPI框架
   - 支持实时AI对话和讨论
   - 提供完整的API文档

3. **Chat2Chat** - 老版桌面应用，单文件架构，功能完整，适合快速部署和使用
   - 轻量级设计，易于使用
   - 支持基本的AI对话功能
   - 适合简单场景使用

## 功能特点

### 核心功能

- 💬 **单聊模式**：与AI进行一对一聊天，支持多种AI模型和API
- 🔄 **讨论模式**：两个AI围绕指定主题进行深入讨论
- ⚖️ **辩论模式**：两个AI围绕指定主题进行结构化辩论
- 📝 **历史管理**：查看、编辑、复制、删除和管理聊天历史，支持批量操作
- 🔧 **API配置**：统一管理多种API密钥和系统提示词
- 📊 **批量处理**：支持批量处理多个讨论主题，提高效率
- 📋 **关于我们**：查看应用版本和开发团队信息
- 🌐 **国际化支持**：支持多种语言界面，可自由切换

### 技术特点

- 🌟 **现代化架构**：桌面应用采用MVC架构，Web应用采用前后端分离
- 🔌 **多API支持**：支持OpenAI、DeepSeek和Ollama API
- 🎨 **友好界面**：直观易用的图形用户界面，支持多种主题
- 📱 **跨平台**：支持Windows、macOS和Linux
- 🔒 **安全可靠**：完善的错误处理和资源管理
- 📈 **高性能**：优化的API调用和资源管理
- 🧪 **完善测试**：包含单元测试、集成测试和UI测试

## 安装和使用

### 1. AI_Talking（新版桌面应用）

#### 安装依赖

```bash
cd AI_Talking
pip install -r ../requirements.txt
```

#### 运行应用

```bash
cd AI_Talking
python src/main.py
```

#### 快速启动

Windows用户可直接运行 `run_app.bat` 脚本启动应用。

### 2. AI_Talking_Web（Web应用）

#### 启动完整服务

```bash
cd AI_Talking_Web
python start_server.py
```

#### 单独启动后端服务

```bash
cd AI_Talking_Web
python backend/main.py
```

#### 前端开发模式

```bash
cd AI_Talking_Web
npm install
npm run dev
```

#### 前端构建

```bash
cd AI_Talking_Web
npm run build
```

### 3. Chat2Chat（老版桌面应用）

#### 运行应用

```bash
cd Chat2Chat
python chat_gui.py
```

## 配置API密钥

### 桌面应用

1. 启动应用后，点击"API设置"标签页
2. 配置所需的API密钥和系统提示词
3. 点击"保存设置"按钮

### Web应用

1. 访问Web应用
2. 点击"设置"标签页
3. 配置所需的API密钥和系统提示词
4. 点击"保存设置"按钮

## 环境变量配置

您也可以直接编辑`.env`文件来配置API密钥。项目根目录提供了`.env使用说明.md`文件，详细说明了各配置项的使用方法。

```
# Ollama API设置
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI API设置
OPENAI_API_KEY=your_openai_api_key

# DeepSeek API设置
DEEPSEEK_API_KEY=your_deepseek_api_key

# 聊天系统提示词设置
CHAT_SYSTEM_PROMPT=

#讨论系统提示词设置
DISCUSSION_SYSTEM_PROMPT=
DISCUSSION_AI1_SYSTEM_PROMPT=
DISCUSSION_AI2_SYSTEM_PROMPT=

# 辩论系统提示词设置
DEBATE_SYSTEM_PROMPT=
DEBATE_AI1_PROMPT=
DEBATE_AI2_PROMPT=

# 专家AI3系统提示词
EXPERT_AI3_SYSTEM_PROMPT=

# 裁判AI3系统提示词
JUDGE_AI3_SYSTEM_PROMPT=
```

## 使用指南

### 单聊模式

1. 选择"聊天"标签页
2. 选择AI模型和API类型
3. 输入您的问题或消息
4. 点击"发送"按钮
5. 等待AI回复

### 讨论模式

1. 选择"讨论"标签页
2. 输入讨论主题
3. 选择两个AI模型和API类型
4. 设置讨论轮数和温度参数
5. 点击"开始讨论"按钮
6. 查看讨论过程和结果

### 辩论模式

1. 选择"辩论"标签页
2. 输入辩论主题
3. 选择两个AI模型和API类型（正方和反方）
4. 设置辩论轮数和温度参数
5. 点击"开始辩论"按钮
6. 查看辩论过程和结果

### 批量处理

1. 选择"批量处理"标签页
2. 输入多个讨论主题，每行一个
3. 选择AI模型和API类型
4. 设置讨论参数
5. 点击"开始处理"按钮
6. 查看处理结果

### 历史管理

1. 选择"历史管理"标签页
2. 浏览历史记录列表
3. 点击记录查看详情
4. 可以删除选中记录或清空所有记录

### API设置

1. 选择"API设置"标签页
2. 输入API密钥和系统提示词
3. 点击"保存设置"按钮

### 关于我们

1. 选择"关于我们"标签页
2. 查看应用版本和开发团队信息

## 技术栈

### 桌面应用 (AI_Talking)

| 技术 | 用途 |
|------|------|
| Python | 主要编程语言 |
| PyQt5 | GUI框架，构建桌面界面 |
| FastAPI | 后端API服务 |
| requests | HTTP请求处理 |
| python-dotenv | 环境变量管理 |
| markdown | Markdown渲染 |
| pytest | 测试框架 |
| Black | 代码格式化 |

### Web应用 (AI_Talking_Web)

| 技术 | 用途 |
|------|------|
| TypeScript | 前端开发语言 |
| FastAPI | 后端框架 |
| Axios | HTTP请求库 |
| Marked | Markdown渲染 |
| live-server | 开发服务器 |
| Swagger UI | API文档生成 |

## API文档

Web应用提供了完整的API文档，可通过以下方式访问：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 性能优化

### API调用优化

- 🔄 **自动重试**：API调用失败时自动重试，提高可靠性
- ⚡ **限流机制**：根据错误率动态调整请求频率
- 📥 **批量请求**：合并多个API请求，减少网络开销

### 资源管理

- 🧹 **资源清理**：及时清理不再使用的资源
- 🧵 **线程池**：使用线程池管理线程，避免线程过多
- 📦 **上下文管理器**：安全管理资源

## 安全设计

### API安全

- 🔑 **安全存储**：API密钥加密存储
- ✅ **输入验证**：严格验证所有输入
- 🛡️ **CORS配置**：合理配置跨域访问
- 🚦 **请求限流**：防止API滥用

### 数据安全

- 🔒 **数据加密**：敏感数据加密存储
- 📋 **访问控制**：严格的访问控制
- 📝 **安全日志**：日志中不包含敏感信息

## 监控和维护

### 日志系统

- 📊 **分级日志**：支持DEBUG、INFO、WARNING、ERROR、CRITICAL五个级别
- 📝 **详细格式**：包含时间、级别、模块名、消息内容
- 💾 **文件存储**：日志保存到文件，便于分析和调试
- 📦 **日志轮转**：自动管理日志文件大小，防止占用过多磁盘空间

### 错误监控

- 📈 **错误统计**：统计错误类型和数量
- ⚠️ **错误告警**：错误率超过阈值时自动告警
- 🔍 **错误分析**：详细的错误信息，便于定位问题

## 开发指南

### 代码风格

- Python: 使用Black进行代码格式化，遵循PEP8规范
- TypeScript: 使用TypeScript编译器进行类型检查，遵循TypeScript最佳实践
- 使用pre-commit钩子自动检查代码风格

### 测试

- 单元测试：测试单个模块的功能，位于`tests`目录
- 集成测试：测试模块间的交互，确保系统整体功能正常
- UI测试：测试用户界面的交互和响应

### 构建

#### 桌面应用打包

```bash
cd AI_Talking
python -m PyInstaller --onefile --windowed --icon=../resources/icon.ico src/main.py
```

#### Web应用构建

```bash
cd AI_Talking_Web
npm run build
```

### 架构设计

项目采用分层架构设计，详细架构信息请参考 `ARCHITECTURE.md` 文件。

## 版本说明

| 版本 | 说明 |
|------|------|
| v1.0 | 初始版本，支持基本的AI讨论功能 |
| v2.0 | 重构为MVC架构，添加辩论和单聊模式 |
| v3.0 | 添加Web应用，支持前后端分离 |
| v4.0 | 优化性能，添加错误监控和资源管理 |
| v5.0 | 完善测试用例，添加批量处理功能，优化用户界面 |

## 未来规划

1. 🌐 **多语言支持**：支持多种语言界面
2. ☁️ **云同步**：聊天历史云同步，支持多设备访问
3. 🔌 **插件系统**：支持插件扩展，增强功能
4. 📱 **移动端优化**：更好的移动端体验
5. 🎙️ **语音对话**：支持实时语音对话
6. 🎨 **主题定制**：支持自定义主题和样式
7. 📊 **数据分析**：对话数据分析和可视化
8. 🎯 **AI微调**：支持模型微调，提高对话质量

## 贡献

欢迎提交Issue和Pull Request！贡献指南如下：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 许可证

本项目采用MIT许可证。详情请查看 `LICENSE` 文件。

## 联系方式

- 开发团队：NONEAD Corporation
- 联系邮箱：support@nonead.com
- 项目地址：https://github.com/NoneadChina/AI_Talking

## 致谢

感谢所有为该项目做出贡献的开发者和用户！

## 相关文档

- [架构设计文档](ARCHITECTURE.md)
- [变更日志](CHANGELOG.md)
- [环境变量使用说明](.env使用说明.md)
- [代码审查报告](code_review_report.md)