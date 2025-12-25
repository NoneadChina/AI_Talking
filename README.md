# AI Talking


AI Talking is a powerful AI conversation system that supports single chat, discussion, debate, and other modes, with both desktop and web application deployment options.

## Project Structure

The project consists of three main parts:

1. **AI_Talking** - New desktop application with MVC architecture, modular code, supporting single chat, discussion, debate, and batch processing modes
   - Developed with PyQt5 framework for GUI
   - Supports OpenAI, DeepSeek, and Ollama APIs
   - Modular design with clear code structure
   - Supports multi-turn conversations and history management

2. **AI_Talking_Web** - Web application with separated front-end and back-end, supporting online use
   - Front-end developed with TypeScript
   - Back-end using FastAPI framework
   - Supports real-time AI conversations and discussions
   - Provides complete API documentation

3. **Chat2Chat** - Old desktop application with single-file architecture, complete functionality, suitable for quick deployment and use
   - Lightweight design, easy to use
   - Supports basic AI conversation functions
   - Suitable for simple scenarios

## Features

### Core Features

- 💬 **Single Chat Mode**: One-on-one chat with AI, supporting multiple AI models and APIs
- 🔄 **Discussion Mode**: Two AIs conduct in-depth discussions on specified topics
- ⚖️ **Debate Mode**: Two AIs engage in structured debates on specified topics
- 📝 **History Management**: View, edit, copy, delete, and manage chat history, supporting batch operations
- 🔧 **API Configuration**: Unified management of multiple API keys and system prompts
- 📊 **Batch Processing**: Support batch processing of multiple discussion topics to improve efficiency
- 📋 **About Us**: View application version and development team information
- 🌐 **Internationalization Support**: Support multiple language interfaces, freely switchable

### Technical Features

- 🌟 **Modern Architecture**: Desktop application adopts MVC architecture, web application adopts front-end and back-end separation
- 🔌 **Multi-API Support**: Supports OpenAI, DeepSeek, and Ollama APIs
- 🎨 **Friendly Interface**: Intuitive and easy-to-use graphical user interface, supporting multiple themes
- 📱 **Cross-Platform**: Supports Windows, macOS, and Linux
- 🔒 **Secure and Reliable**: Perfect error handling and resource management
- 📈 **High Performance**: Optimized API calls and resource management
- 🧪 **Comprehensive Testing**: Includes unit tests, integration tests, and UI tests

## Installation and Usage

### 1. AI_Talking (New Desktop Application)

#### Install Dependencies

```bash
cd AI_Talking
pip install -r ../requirements.txt
```

#### Run Application

```bash
cd AI_Talking
python src/main.py
```

#### Quick Start

Windows users can directly run the `run_app.bat` script to start the application.

### 2. AI_Talking_Web (Web Application)

#### Start Complete Service

```bash
cd AI_Talking_Web
python start_server.py
```

#### Start Backend Service Separately

```bash
cd AI_Talking_Web
python backend/main.py
```

#### Frontend Development Mode

```bash
cd AI_Talking_Web
npm install
npm run dev
```

#### Frontend Build

```bash
cd AI_Talking_Web
npm run build
```

### 3. Chat2Chat (Old Desktop Application)

#### Run Application

```bash
cd Chat2Chat
python chat_gui.py
```

## Configure API Keys

### Desktop Application

1. After starting the application, click the "API Settings" tab
2. Configure the required API keys and system prompts
3. Click the "Save Settings" button

### Web Application

1. Access the web application
2. Click the "Settings" tab
3. Configure the required API keys and system prompts
4. Click the "Save Settings" button

## Environment Variable Configuration

You can also directly edit the `.env` file to configure API keys. The project root directory provides a `.env使用说明.md` file that details the usage of each configuration item.

```
# Ollama API Settings
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI API Settings
OPENAI_API_KEY=your_openai_api_key

# DeepSeek API Settings
DEEPSEEK_API_KEY=your_deepseek_api_key

# Chat System Prompt Settings
CHAT_SYSTEM_PROMPT=

# Discussion System Prompt Settings
DISCUSSION_SYSTEM_PROMPT=
DISCUSSION_AI1_SYSTEM_PROMPT=
DISCUSSION_AI2_SYSTEM_PROMPT=

# Debate System Prompt Settings
DEBATE_SYSTEM_PROMPT=
DEBATE_AI1_PROMPT=
DEBATE_AI2_PROMPT=

# Expert AI3 System Prompt
EXPERT_AI3_SYSTEM_PROMPT=

# Judge AI3 System Prompt
JUDGE_AI3_SYSTEM_PROMPT=
```

## Usage Guide

### Single Chat Mode

1. Select the "Chat" tab
2. Choose AI model and API type
3. Enter your question or message
4. Click the "Send" button
5. Wait for AI response

### Discussion Mode

1. Select the "Discussion" tab
2. Enter discussion topic
3. Choose two AI models and API types
4. Set discussion rounds and temperature parameters
5. Click the "Start Discussion" button
6. View discussion process and results

### Debate Mode

1. Select the "Debate" tab
2. Enter debate topic
3. Choose two AI models and API types (pro and con sides)
4. Set debate rounds and temperature parameters
5. Click the "Start Debate" button
6. View debate process and results

### Batch Processing

1. Select the "Batch Processing" tab
2. Enter multiple discussion topics, one per line
3. Choose AI model and API type
4. Set discussion parameters
5. Click the "Start Processing" button
6. View processing results

### History Management

1. Select the "History" tab
2. Browse history list
3. Click a record to view details
4. You can delete selected records or clear all records

### API Settings

1. Select the "API Settings" tab
2. Enter API keys and system prompts
3. Click the "Save Settings" button

### About Us

1. Select the "About Us" tab
2. View application version and development team information

## Technology Stack

### Desktop Application (AI_Talking)

| Technology | Purpose |
|------------|---------|
| Python | Main programming language |
| PyQt5 | GUI framework for building desktop interfaces |
| FastAPI | Backend API service |
| requests | HTTP request handling |
| python-dotenv | Environment variable management |
| markdown | Markdown rendering |
| pytest | Testing framework |
| Black | Code formatting |

### Web Application (AI_Talking_Web)

| Technology | Purpose |
|------------|---------|
| TypeScript | Frontend development language |
| FastAPI | Backend framework |
| Axios | HTTP request library |
| Marked | Markdown rendering |
| live-server | Development server |
| Swagger UI | API documentation generation |

## API Documentation

The web application provides complete API documentation, which can be accessed in the following ways:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Performance Optimization

### API Call Optimization

- 🔄 **Auto-retry**: Automatically retry failed API calls to improve reliability
- ⚡ **Rate limiting**: Dynamically adjust request frequency based on error rate
- 📥 **Batch requests**: Combine multiple API requests to reduce network overhead

### Resource Management

- 🧹 **Resource cleanup**: Timely cleanup of unused resources
- 🧵 **Thread pool**: Use thread pool to manage threads, avoiding too many threads
- 📦 **Context manager**: Safe resource management

## Security Design

### API Security

- 🔑 **Secure storage**: Encrypted storage of API keys
- ✅ **Input validation**: Strict validation of all inputs
- 🛡️ **CORS configuration**: Reasonable cross-domain access configuration
- 🚦 **Request throttling**: Prevent API abuse

### Data Security

- 🔒 **Data encryption**: Encrypted storage of sensitive data
- 📋 **Access control**: Strict access control
- 📝 **Secure logging**: No sensitive information in logs

## Monitoring and Maintenance

### Log System

- 📊 **Leveled logging**: Supports DEBUG, INFO, WARNING, ERROR, CRITICAL five levels
- 📝 **Detailed format**: Includes time, level, module name, message content
- 💾 **File storage**: Logs saved to files for easy analysis and debugging
- 📦 **Log rotation**: Automatically manages log file size to prevent excessive disk space usage

### Error Monitoring

- 📈 **Error statistics**: Statistics of error types and quantities
- ⚠️ **Error alerts**: Automatic alerts when error rate exceeds threshold
- 🔍 **Error analysis**: Detailed error information for easy problem locating

## Development Guide

### Code Style

- Python: Use Black for code formatting, follow PEP8 specifications
- TypeScript: Use TypeScript compiler for type checking, follow TypeScript best practices
- Use pre-commit hooks to automatically check code style

### Testing

- Unit tests: Test the functionality of individual modules, located in the `tests` directory
- Integration tests: Test interactions between modules to ensure overall system functionality
- UI tests: Test user interface interactions and responses

### Build

#### Desktop Application Packaging

```bash
cd AI_Talking
python -m PyInstaller --onefile --windowed --icon=../resources/icon.ico src/main.py
```

#### Web Application Build

```bash
cd AI_Talking_Web
npm run build
```

### Architecture Design

The project adopts a layered architecture design. For detailed architecture information, please refer to the `ARCHITECTURE.md` file.

## Version Description

| Version | Description |
|---------|-------------|
| v1.0 | Initial version, supporting basic AI discussion functionality |
| v2.0 | Refactored to MVC architecture, added debate and single chat modes |
| v3.0 | Added web application, supporting front-end and back-end separation |
| v4.0 | Optimized performance, added error monitoring and resource management |
| v5.0 | Improved test cases, added batch processing functionality, optimized user interface |

## Future Plans

1. 🌐 **Multi-language Support**: Support multiple language interfaces
2. ☁️ **Cloud Synchronization**: Cloud synchronization of chat history, supporting multi-device access
3. 🔌 **Plugin System**: Support plugin extensions to enhance functionality
4. 📱 **Mobile Optimization**: Better mobile experience
5. 🎙️ **Voice Conversation**: Support real-time voice conversation
6. 🎨 **Theme Customization**: Support custom themes and styles
7. 📊 **Data Analysis**: Dialogue data analysis and visualization
8. 🎯 **AI Fine-tuning**: Support model fine-tuning to improve dialogue quality

## Contribution

Welcome to submit Issues and Pull Requests! Contribution guidelines are as follows:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. For details, please see the `LICENSE` file.

## Contact

- Development Team: NONEAD Corporation
- Contact Email: support@nonead.com
- Project Address: [https://github.com/NONEAD/AI_Talking](https://github.com/NoneadChina/AI_Talking)

## Acknowledgments

Thanks to all developers and users who have contributed to this project!

## Related Documents

- [Architecture Design Document](ARCHITECTURE.md)
- [Change Log](CHANGELOG.md)
- [Environment Variable Usage Instructions](.env使用说明.md)
- [Code Review Report](code_review_report.md)