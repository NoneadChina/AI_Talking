# AI对话系统

这是一个基于TypeScript的AI对话系统，允许两个不同的AI模型进行对话交流。系统使用Python作为外壳，以网页形式嵌入，支持Ollama、OpenAI和DeepSeek三种API接口。

## 功能特点

- 支持多种AI模型对话：可选择不同API和模型进行AI间的对话
- 完整的设置界面：可配置API密钥、系统提示词等
- 自定义对话参数：可设置对话轮数、时间限制、温度等参数
- 聊天历史展示：以Markdown格式显示聊天内容
- PDF导出功能：可将聊天历史导出为PDF
- 响应处理：包含重复段落去除、空行压缩等优化

## 技术栈

### 前端技术
- **TypeScript**：用于编写类型安全的前端代码，提高代码质量和开发效率
- **HTML5**：构建网页结构，实现响应式布局和现代Web特性
- **CSS3**：设计美观的用户界面，实现动画效果和响应式设计
- **i18next**：实现国际化支持，支持多国语言切换

### 后端技术
- **Python**：提供本地HTTP服务器，处理API请求和AI服务交互
- **FastAPI**：构建高性能的RESTful API，支持自动文档生成
- **SQLite**：轻量级关系型数据库，用于存储用户信息和聊天历史
- **SQLAlchemy**：Python ORM框架，简化数据库操作
- **JWT（JSON Web Token）**：基于Token的用户认证机制，实现安全的身份验证

### 认证与权限
- **角色基于访问控制（RBAC）**：实现超级管理员和普通用户的权限管理

### 依赖库
- **axios**：处理HTTP请求，实现前后端通信
- **marked**：Markdown渲染，用于展示聊天内容
- **python-jose**：JWT编码/解码，实现Token生成和验证
- **passlib**：密码哈希处理，确保用户密码安全

### 支持的AI服务
- **Ollama**（本地模型）：支持本地部署的AI模型，无需网络连接
- **OpenAI**（云端API）：提供强大的GPT系列模型，支持多种应用场景
- **DeepSeek**（云端API）：提供高性能的大语言模型，支持多轮对话

## 支持的AI服务

### Ollama（本地模型）
- **类型**：本地部署模型
- **用途**：无需网络连接，支持在本地环境运行AI模型，保护数据隐私
- **特点**：可自定义模型，支持多种开源模型，适合离线使用场景

### OpenAI（云端API）
- **类型**：云端API服务
- **用途**：提供强大的GPT系列模型，支持聊天、生成、翻译等多种任务
- **特点**：模型性能强大，支持多种应用场景，需要API密钥和网络连接

### DeepSeek（云端API）
- **类型**：云端API服务
- **用途**：提供高性能的大语言模型，支持多轮对话和复杂任务
- **特点**：响应速度快，支持长文本生成，适合实时对话场景

## 用户角色与权限

### 超级管理员
- **权限范围**：
  - 完整访问所有功能和页面
  - 用户管理（创建、查看、编辑、删除用户）
  - 系统设置管理
  - 所有聊天、讨论、辩论功能
  - 完整的历史记录管理

### 普通用户
- **权限范围**：
  - 聊天功能：与AI进行单轮或多轮对话
  - 讨论功能：发起和参与AI间的讨论
  - 辩论功能：发起和参与AI间的辩论
  - 历史记录管理：查看、删除自己的聊天历史
  - 关于页面：查看项目信息
  - 个人设置：管理个人信息和偏好
  - 无用户管理和系统设置权限


## 安装步骤

### 1. 安装Node.js依赖

首先，确保您已安装Node.js环境。然后执行以下命令安装项目依赖：

```bash
cd ts_web_app
npm install
```

### 2. 构建应用

安装依赖后，构建TypeScript应用：

```bash
npm run build
```

这将编译TypeScript代码并生成可在浏览器中运行的JavaScript文件。

## 使用方法

### 通过Python启动

最简单的启动方式是使用提供的Python脚本，它会自动启动本地服务器并打开浏览器：

```bash
python start_server.py
```

### 手动启动

如果您不想使用Python脚本，也可以通过以下步骤手动启动：

1. 构建应用：
   ```bash
   npm run build
   ```

2. 启动开发服务器：
   ```bash
   npm run dev
   ```

3. 在浏览器中访问：
   ```
   http://localhost:8000
   ```

## 配置说明

### API设置

在"API设置"标签页中，您可以配置以下内容：

- **OpenAI API**：输入您的OpenAI API密钥
- **DeepSeek API**：输入您的DeepSeek API密钥
- **Ollama API**：设置Ollama服务器的URL（默认为http://ai.corp.nonead.com:11434）

### 系统提示词

您可以为AI设置系统提示词，控制其行为：
- **共同系统提示词**：应用于所有AI
- **AI 1系统提示词**：仅应用于AI 1
- **AI 2系统提示词**：仅应用于AI 2

### 对话参数

在主界面，您可以配置以下对话参数：

- **讨论主题**：两个AI将围绕此主题进行讨论
- **AI 1/AI 2配置**：选择使用的模型和API
- **对话轮数**：设置AI之间的对话轮数
- **时间限制**：设置对话的最大时间（秒），0表示无限制
- **温度**：控制AI输出的随机性，值越高越随机

## 注意事项

1. 使用OpenAI和DeepSeek API需要有效的API密钥
2. 使用Ollama需要您本地已安装并运行Ollama服务器
3. 所有设置都会保存在浏览器的本地存储中
4. 导出PDF功能使用浏览器的打印功能实现

## 开发说明

如果您想修改或扩展代码，可以使用开发模式：

```bash
npm run dev
```

这将启动一个热重载的开发服务器，方便您进行开发和调试。

## 项目结构

```
AI_Talking_Web/
├── backend/            # FastAPI后端
│   ├── src/            # 后端源代码
│   │   └── utils/      # 后端工具类
│   ├── ai_talking.db   # SQLite数据库文件
│   ├── chat_between_ais.py  # AI对话管理
│   ├── error_monitor.py     # 错误监控
│   ├── main.py         # 后端应用入口
│   └── requirements.txt # 后端依赖
├── public/             # 编译后的前端资源
│   ├── js/             # JavaScript文件
│   │   ├── services/   # 前端服务
│   │   ├── types/      # 前端类型定义
│   │   └── main.js     # 前端应用入口
│   └── index.html      # HTML入口文件
├── src/                # TypeScript源代码
│   ├── services/       # 前端服务层
│   ├── types/          # TypeScript类型定义
│   └── main.ts         # 前端应用入口
├── ai_talking.db       # 数据库文件
├── index.html          # 主HTML文件
├── README.md           # 项目说明
├── requirements.txt    # 项目依赖
├── start_all.py        # 启动所有服务脚本
└── start_server.py     # 启动服务器脚本
```