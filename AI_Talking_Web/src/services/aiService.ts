import axios, { AxiosInstance } from 'axios';
import { ApiType, Message, AIResponse, ApiSettings, OllamaModel } from '../types/types';

class AIService {
    private settings: ApiSettings;
    private ollamaClient: AxiosInstance | null = null;
    private openaiClient: AxiosInstance | null = null;
    private deepseekClient: AxiosInstance | null = null;

    constructor(settings: ApiSettings) {
        this.settings = settings;
        this.initClients();
    }

    private initClients(): void {
        // 初始化Ollama客户端
        const ollamaConfig: any = {
            baseURL: this.settings.ollama.url,
            timeout: 60000
        };
        
        // 如果有API密钥，添加到请求头
        if (this.settings.ollama.key && this.settings.ollama.key !== 'Ollama') {
            ollamaConfig.headers = {
                'Authorization': `Bearer ${this.settings.ollama.key}`
            };
        }
        
        this.ollamaClient = axios.create(ollamaConfig);

        // 初始化OpenAI客户端
        if (this.settings.openai.key) {
            this.openaiClient = axios.create({
                baseURL: this.settings.openai.baseUrl || 'https://api.openai.com/v1',
                timeout: 60000,
                headers: {
                    'Authorization': `Bearer ${this.settings.openai.key}`,
                    'Content-Type': 'application/json'
                }
            });
        }

        // 初始化DeepSeek客户端
        if (this.settings.deepseek.key) {
            this.deepseekClient = axios.create({
                baseURL: this.settings.deepseek.baseUrl || 'https://api.deepseek.com/v1',
                timeout: 60000,
                headers: {
                    'Authorization': `Bearer ${this.settings.deepseek.key}`,
                    'Content-Type': 'application/json'
                }
            });
        }
    }

    updateSettings(settings: ApiSettings): void {
        this.settings = settings;
        this.initClients(); // 更新设置后重新初始化客户端
    }

    async getOllamaModels(): Promise<OllamaModel[]> {
        try {
            // 调用后端API获取Ollama模型列表
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/api/models/ollama', {
                headers: {
                    ...(token && { 'Authorization': `Bearer ${token}` })
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data.models || [];
        } catch (error) {
            console.error('Failed to get Ollama models:', error);
            // 失败时返回默认模型列表
            return [
                { name: 'qwen3:14b', model: 'qwen3:14b', modified_at: '', size: 0, digest: '' },
                { name: 'llama3:8b', model: 'llama3:8b', modified_at: '', size: 0, digest: '' },
                { name: 'mistral:7b', model: 'mistral:7b', modified_at: '', size: 0, digest: '' },
                { name: 'gemma:7b', model: 'gemma:7b', modified_at: '', size: 0, digest: '' },
                { name: 'deepseek-v3.1:671b-cloud', model: 'deepseek-v3.1:671b-cloud', modified_at: '', size: 0, digest: '' },
                { name: 'deepseek-r1:8b', model: 'deepseek-r1:8b', modified_at: '', size: 0, digest: '' },
                { name: 'deepseek-r1:1.5b', model: 'deepseek-r1:1.5b', modified_at: '', size: 0, digest: '' },
                { name: 'deepseek-r1:14b', model: 'deepseek-r1:14b', modified_at: '', size: 0, digest: '' }
            ];
        }
    }

    async getOpenAIModels(): Promise<string[]> {
        try {
            if (!this.openaiClient) {
                // 客户端未初始化，直接返回默认模型列表，不抛出错误
                return ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo'];
            }
            const response = await this.openaiClient.get('/models');
            return response.data.data
                .filter((model: any) => model.id.includes('gpt'))
                .map((model: any) => model.id);
        } catch (error) {
            console.error('Failed to get OpenAI models:', error);
            // 失败时返回默认模型列表
            return ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo'];
        }
    }

    async getDeepSeekModels(): Promise<string[]> {
        try {
            if (!this.deepseekClient) {
                // 客户端未初始化，直接返回默认模型列表，不抛出错误
                return ['deepseek-chat', 'deepseek-coder'];
            }
            const response = await this.deepseekClient.get('/models');
            return response.data.data
                .map((model: any) => model.id);
        } catch (error) {
            console.error('Failed to get DeepSeek models:', error);
            // 失败时返回默认模型列表
            return ['deepseek-chat', 'deepseek-coder'];
        }
    }

    async getAIResponse(
        apiType: ApiType,
        model: string,
        messages: Message[],
        temperature: number = 0.8
    ): Promise<AIResponse> {
        try {
            switch (apiType) {
                case 'ollama':
                    return await this.getOllamaResponse(model, messages, temperature);
                case 'openai':
                    return await this.getOpenAIResponse(model, messages, temperature);
                case 'deepseek':
                    return await this.getDeepSeekResponse(model, messages, temperature);
                default:
                    return { success: false, error: 'Unsupported API type' };
            }
        } catch (error) {
            console.error('Error getting AI response:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    private async getOllamaResponse(
        model: string,
        messages: Message[],
        temperature: number
    ): Promise<AIResponse> {
        if (!this.ollamaClient) {
            return { success: false, error: 'Ollama client not initialized' };
        }

        const response = await this.ollamaClient.post('/api/chat', {
            model,
            messages,
            options: {
                temperature,
                num_predict: 1024,
                top_p: 0.9
            },
            stream: false
        });

        let content = response.data.message?.content || '';
        content = this.processOllamaResponse(content);
        return { success: true, content };
    }

    private async getOpenAIResponse(
        model: string,
        messages: Message[],
        temperature: number
    ): Promise<AIResponse> {
        if (!this.openaiClient) {
            return { success: false, error: 'OpenAI client not initialized' };
        }

        const response = await this.openaiClient.post('/chat/completions', {
            model,
            messages,
            temperature,
            max_tokens: 1024,
            n: 1,
            stop: null
        });

        const content = response.data.choices[0].message.content.trim();
        return { success: true, content };
    }

    private async getDeepSeekResponse(
        model: string,
        messages: Message[],
        temperature: number
    ): Promise<AIResponse> {
        if (!this.deepseekClient) {
            return { success: false, error: 'DeepSeek client not initialized' };
        }

        const response = await this.deepseekClient.post('/chat/completions', {
            model,
            messages,
            temperature,
            max_tokens: 1024,
            n: 1,
            stop: null
        });

        const content = response.data.choices[0].message.content.trim();
        return { success: true, content };
    }

    private processOllamaResponse(text: string): string {
        // 移除思考标签
        text = this.removeThinkingTags(text);
        
        // 移除JSON元数据
        text = this.removeJsonMetadata(text);
        
        // 压缩重复段落
        text = this.compressDuplicateParagraphs(text);
        
        // 压缩空行
        text = this.compressEmptyLines(text);
        
        return text.trim();
    }

    private removeThinkingTags(text: string): string {
        // 移除<|im_start|>think和<|im_end|>标签
        const thinkingTagRegex = /<\|im_start\|>think[\s\S]*?<\|im_end\|>/g;
        return text.replace(thinkingTagRegex, '');
    }

    private removeJsonMetadata(text: string): string {
        // 移除JSON元数据
        const jsonMetadataRegex = /\{"tool_call":[\s\S]*?\}|\{"name":[\s\S]*?\}|\{"tool_result":[\s\S]*?\}/g;
        return text.replace(jsonMetadataRegex, '');
    }

    private compressDuplicateParagraphs(text: string): string {
        const paragraphs = text.split('\n\n');
        const uniqueParagraphs: string[] = [];
        
        for (const paragraph of paragraphs) {
            if (paragraph.trim() && !uniqueParagraphs.includes(paragraph)) {
                uniqueParagraphs.push(paragraph);
            }
        }
        
        return uniqueParagraphs.join('\n\n');
    }

    private compressEmptyLines(text: string): string {
        return text.replace(/\n{3,}/g, '\n\n');
    }
}

export default AIService;