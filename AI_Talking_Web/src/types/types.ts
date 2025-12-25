// API类型定义
export type ApiType = 'ollama' | 'openai' | 'deepseek';

// 消息类型定义
export interface Message {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

// AI响应类型定义
export interface AIResponse {
    success: boolean;
    content?: string;
    error?: string;
}

// API设置类型定义
export interface ApiSettings {
    openai: {
        key: string;
        baseUrl: string;
    };
    deepseek: {
        key: string;
        baseUrl: string;
    };
    ollama: {
        url: string;
        key: string;
    };
    systemPrompts: {
        common: string;
        ai1: string;
        ai2: string;
    };
}

// 对话配置类型定义
export interface ChatConfig {
    topic: string;
    model1: string;
    api1: ApiType;
    model2: string;
    api2: ApiType;
    rounds: number;
    timeLimit: number;
    temperature: number;
}

// Ollama模型类型定义
export interface OllamaModel {
    name: string;
    model: string;
    modified_at: string;
    size: number;
    digest: string;
}

// 聊天消息显示类型
export interface ChatMessageDisplay {
    sender: string;
    content: string;
    timestamp: Date;
}