import { marked } from 'marked';
import AIService from './services/aiService';
import ChatService from './services/chatService';
class App {
    constructor() {
        this.isChatRunning = false;
        // 初始化默认设置
        const defaultSettings = {
            openai: {
                key: localStorage.getItem('openaiKey') || ''
            },
            deepseek: {
                key: localStorage.getItem('deepseekKey') || ''
            },
            ollama: {
                url: localStorage.getItem('ollamaUrl') || 'http://ai.corp.nonead.com:11434'
            },
            systemPrompts: {
                common: localStorage.getItem('commonSystemPrompt') || '你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。',
                ai1: localStorage.getItem('ai1SystemPrompt') || '',
                ai2: localStorage.getItem('ai2SystemPrompt') || ''
            }
        };
        this.aiService = new AIService(defaultSettings);
        this.chatService = new ChatService(this.aiService);
        this.initializeEventListeners();
        this.loadSettings();
    }
    initializeEventListeners() {
        // 开始对话按钮
        document.getElementById('startChat')?.addEventListener('click', () => this.startChat());
        // 停止对话按钮
        document.getElementById('stopChat')?.addEventListener('click', () => this.stopChat());
        // 保存设置按钮
        document.getElementById('saveSettings')?.addEventListener('click', () => this.saveSettings());
        // 导出PDF按钮
        document.getElementById('exportPdf')?.addEventListener('click', () => this.exportPdf());
        // API类型选择变化，更新模型列表
        document.getElementById('api1')?.addEventListener('change', () => this.updateModelList('model1'));
        document.getElementById('api2')?.addEventListener('change', () => this.updateModelList('model2'));
    }
    loadSettings() {
        // 加载API设置
        const openaiKeyInput = document.getElementById('openaiKey');
        const deepseekKeyInput = document.getElementById('deepseekKey');
        const ollamaUrlInput = document.getElementById('ollamaUrl');
        openaiKeyInput.value = localStorage.getItem('openaiKey') || '';
        deepseekKeyInput.value = localStorage.getItem('deepseekKey') || '';
        ollamaUrlInput.value = localStorage.getItem('ollamaUrl') || 'http://ai.corp.nonead.com:11434';
        // 加载系统提示词
        const commonSystemPromptInput = document.getElementById('commonSystemPrompt');
        const ai1SystemPromptInput = document.getElementById('ai1SystemPrompt');
        const ai2SystemPromptInput = document.getElementById('ai2SystemPrompt');
        commonSystemPromptInput.value = localStorage.getItem('commonSystemPrompt') || '你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。';
        ai1SystemPromptInput.value = localStorage.getItem('ai1SystemPrompt') || '';
        ai2SystemPromptInput.value = localStorage.getItem('ai2SystemPrompt') || '';
    }
    saveSettings() {
        const openaiKeyInput = document.getElementById('openaiKey');
        const deepseekKeyInput = document.getElementById('deepseekKey');
        const ollamaUrlInput = document.getElementById('ollamaUrl');
        const commonSystemPromptInput = document.getElementById('commonSystemPrompt');
        const ai1SystemPromptInput = document.getElementById('ai1SystemPrompt');
        const ai2SystemPromptInput = document.getElementById('ai2SystemPrompt');
        // 保存到localStorage
        localStorage.setItem('openaiKey', openaiKeyInput.value);
        localStorage.setItem('deepseekKey', deepseekKeyInput.value);
        localStorage.setItem('ollamaUrl', ollamaUrlInput.value);
        localStorage.setItem('commonSystemPrompt', commonSystemPromptInput.value);
        localStorage.setItem('ai1SystemPrompt', ai1SystemPromptInput.value);
        localStorage.setItem('ai2SystemPrompt', ai2SystemPromptInput.value);
        // 更新AI服务设置
        const newSettings = {
            openai: { key: openaiKeyInput.value },
            deepseek: { key: deepseekKeyInput.value },
            ollama: { url: ollamaUrlInput.value },
            systemPrompts: {
                common: commonSystemPromptInput.value,
                ai1: ai1SystemPromptInput.value,
                ai2: ai2SystemPromptInput.value
            }
        };
        this.aiService.updateSettings(newSettings);
        // 显示保存成功提示
        this.updateStatus('设置已保存');
    }
    startChat() {
        // 获取配置
        const config = this.getChatConfig();
        if (!config)
            return;
        // 清空聊天历史
        this.clearChatHistory();
        // 启用/禁用按钮
        this.enableUI(false);
        this.isChatRunning = true;
        // 开始对话
        this.chatService.startChat(config, (message) => this.appendToChatHistory(message), (status) => this.updateStatus(status), (error) => {
            this.showErrorMessage(error);
            this.enableUI(true);
            this.isChatRunning = false;
        }, () => {
            this.enableUI(true);
            this.isChatRunning = false;
        });
    }
    stopChat() {
        this.chatService.stopChat();
        this.updateStatus('对话已停止');
        this.enableUI(true);
        this.isChatRunning = false;
    }
    getChatConfig() {
        const topicInput = document.getElementById('topic');
        const model1Select = document.getElementById('model1');
        const api1Select = document.getElementById('api1');
        const model2Select = document.getElementById('model2');
        const api2Select = document.getElementById('api2');
        const roundsInput = document.getElementById('rounds');
        const timeLimitInput = document.getElementById('timeLimit');
        const temperatureInput = document.getElementById('temperature');
        // 验证输入
        if (!topicInput.value.trim()) {
            this.showErrorMessage('请输入讨论主题');
            return null;
        }
        return {
            topic: topicInput.value.trim(),
            model1: model1Select.value,
            api1: api1Select.value,
            model2: model2Select.value,
            api2: api2Select.value,
            rounds: parseInt(roundsInput.value),
            timeLimit: parseInt(timeLimitInput.value),
            temperature: parseFloat(temperatureInput.value)
        };
    }
    appendToChatHistory(message) {
        const chatHistoryElement = document.getElementById('chatHistory');
        if (!chatHistoryElement)
            return;
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${message.sender}`;
        const headerElement = document.createElement('div');
        headerElement.className = 'message-header';
        headerElement.textContent = message.sender === 'ai1' ? 'AI 1' : 'AI 2';
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        // 使用类型断言确保TypeScript编译通过
        contentElement.innerHTML = marked.parse(message.content);
        messageElement.appendChild(headerElement);
        messageElement.appendChild(contentElement);
        chatHistoryElement.appendChild(messageElement);
        // 滚动到底部
        chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight;
    }
    clearChatHistory() {
        const chatHistoryElement = document.getElementById('chatHistory');
        if (chatHistoryElement) {
            chatHistoryElement.innerHTML = '';
        }
    }
    updateStatus(status) {
        const statusElement = document.getElementById('status');
        if (statusElement) {
            statusElement.textContent = status;
        }
    }
    showErrorMessage(message) {
        alert(`错误: ${message}`);
    }
    enableUI(enabled) {
        document.getElementById('startChat').disabled = !enabled || this.isChatRunning;
        document.getElementById('stopChat').disabled = !this.isChatRunning;
        document.getElementById('exportPdf').disabled = !enabled;
        // 禁用/启用输入控件
        const controls = document.querySelectorAll('input, select, textarea');
        controls.forEach(control => {
            control.disabled = !enabled && !control.id.includes('stopChat');
        });
    }
    exportPdf() {
        const chatHistoryElement = document.getElementById('chatHistory');
        if (!chatHistoryElement)
            return;
        // 打印聊天历史
        window.print();
    }
    async updateModelList(modelSelectId) {
        const apiSelectId = modelSelectId === 'model1' ? 'api1' : 'api2';
        const apiSelect = document.getElementById(apiSelectId);
        const modelSelect = document.getElementById(modelSelectId);
        // 如果是Ollama API，尝试获取模型列表
        if (apiSelect.value === 'ollama') {
            try {
                this.updateStatus('获取Ollama模型列表...');
                const models = await this.aiService.getOllamaModels();
                // 清空当前选项并添加新模型
                modelSelect.innerHTML = '';
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = model.name;
                    modelSelect.appendChild(option);
                });
                this.updateStatus('就绪');
            }
            catch (error) {
                this.updateStatus('获取Ollama模型列表失败');
                console.error('Failed to update model list:', error);
            }
        }
    }
}
// 页面加载完成后初始化应用
window.addEventListener('DOMContentLoaded', () => {
    new App();
});
