// 后端API服务类，用于处理与后端的通信

const API_BASE_URL = 'http://localhost:8000/api';

export interface ChatRequest {
    message: string;
    api: string;
    model: string;
    temperature: number;
}

export interface DiscussionRequest {
    topic: string;
    model1: string;
    api1: string;
    model2: string;
    api2: string;
    rounds: number;
    time_limit: number;
    temperature: number;
}

export interface DebateRequest {
    topic: string;
    model1: string;
    api1: string;
    model2: string;
    api2: string;
    rounds: number;
    time_limit: number;
    temperature: number;
}

export interface APIConfig {
    openai: {
        api_key: string;
        base_url: string;
    };
    deepseek: {
        api_key: string;
        base_url: string;
    };
    ollama: {
        base_url: string;
        api_key: string;
    };
}

export interface SystemPrompt {
    chat_system_prompt: string;
    discussion_system_prompt: string;
    discussion_ai1_system_prompt: string;
    discussion_ai2_system_prompt: string;
    debate_system_prompt: string;
    debate_ai1_system_prompt: string;
    debate_ai2_system_prompt: string;
}

export interface ChatResponse {
    success: boolean;
    response: string;
}

export interface HistoryRecord {
    id?: number;
    topic: string;
    model1: string;
    model2: string;
    api1: string;
    api2: string;
    rounds: number;
    chat_content: string;
    start_time: string;
    end_time: string;
}

class ApiService {
    // API调用重试配置
    private readonly MAX_RETRIES = 3;
    private readonly RETRY_DELAY = 1000; // 1秒
    
    // 限流配置
    private readonly RATE_LIMIT = 5; // 每秒最多5个请求
    private readonly TOKEN_BUCKET_SIZE = 10; // 令牌桶大小
    private tokens = this.TOKEN_BUCKET_SIZE;
    private lastTokenRefill = Date.now();
    
    /**
     * 通用API请求方法，包含重试和限流
     */
    private async request<T>(url: string, options: RequestInit): Promise<T> {
        // 限流：令牌桶算法
        const now = Date.now();
        const elapsed = now - this.lastTokenRefill;
        
        // 每秒钟补充令牌
        const tokensToAdd = Math.floor(elapsed / 1000) * this.RATE_LIMIT;
        if (tokensToAdd > 0) {
            this.tokens = Math.min(this.tokens + tokensToAdd, this.TOKEN_BUCKET_SIZE);
            this.lastTokenRefill = now;
        }
        
        // 等待获取令牌
        while (this.tokens <= 0) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // 消耗一个令牌
        this.tokens--;
        
        // 添加认证令牌
        const token = localStorage.getItem('token');
        const headers: Record<string, string> = { ...options.headers } as Record<string, string>;
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // 重试逻辑
        for (let attempt = 0; attempt < this.MAX_RETRIES; attempt++) {
            try {
                const response = await fetch(url, {
                    ...options,
                    headers
                });
                
                if (!response.ok) {
                    // 尝试解析错误响应
                    let errorMessage = `API请求失败: ${response.status}`;
                    try {
                        const errorData = await response.json();
                        if (errorData.detail) {
                            errorMessage = errorData.detail;
                        }
                    } catch (parseError) {
                        // 如果无法解析响应，则使用默认错误信息
                        errorMessage = `${errorMessage} - ${await response.text()}`;
                    }
                    
                    // 如果是服务器错误（5xx），则重试
                    if (response.status >= 500 && attempt < this.MAX_RETRIES - 1) {
                        console.warn(`API请求失败，将重试 (${attempt + 1}/${this.MAX_RETRIES}): ${errorMessage}`);
                        await new Promise(resolve => setTimeout(resolve, this.RETRY_DELAY * (attempt + 1)));
                        continue;
                    }
                    
                    // 如果是未授权错误，跳转到登录页面
                    if (response.status === 401) {
                        localStorage.removeItem('token');
                        window.location.reload();
                    }
                    
                    throw new Error(errorMessage);
                }
                
                return await response.json() as T;
            } catch (error) {
                // 网络错误或其他错误，进行重试
                if (attempt < this.MAX_RETRIES - 1) {
                    console.warn(`API请求失败，将重试 (${attempt + 1}/${this.MAX_RETRIES}): ${error}`);
                    await new Promise(resolve => setTimeout(resolve, this.RETRY_DELAY * (attempt + 1)));
                    continue;
                }
                
                throw error;
            }
        }
        
        // 理论上不会到达这里，因为前面已经抛出了错误
        throw new Error('API请求失败，已达到最大重试次数');
    }
    
    /**
     * 发送聊天消息
     */
    async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
        try {
            return await this.request<ChatResponse>(`${API_BASE_URL}/chat/send`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '发送聊天消息失败';
            console.error('发送聊天消息失败:', errorMessage);
            throw new Error(`发送聊天消息失败: ${errorMessage}`);
        }
    }

    /**
     * 发送聊天消息（流式输出）
     */
    async sendChatMessageStream(
        request: ChatRequest,
        onChunk: (chunk: string) => void,
        onComplete: () => void,
        onError: (error: Error) => void
    ): Promise<void> {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/chat/send/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // 检查响应类型是否为SSE
            if (!response.body) {
                throw new Error('Response body is null');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            async function read() {
                try {
                    const { done, value } = await reader.read();
                    if (done) {
                        onComplete();
                        return;
                    }

                    // 将新数据添加到缓冲区
                    buffer += decoder.decode(value, { stream: true });
                    
                    // 处理缓冲区中的所有完整事件
                    let eventEndIndex;
                    while ((eventEndIndex = buffer.indexOf('\n\n')) !== -1) {
                        const eventData = buffer.slice(0, eventEndIndex);
                        buffer = buffer.slice(eventEndIndex + 2);

                        // 处理SSE事件
                        if (eventData.startsWith('data: ')) {
                            const jsonData = eventData.slice(6);
                            try {
                                const parsed = JSON.parse(jsonData);
                                if (parsed.content) {
                                    onChunk(parsed.content);
                                }
                            } catch (parseError) {
                                console.error('Error parsing SSE data:', parseError);
                            }
                        }
                    }

                    // 继续读取
                    await read();
                } catch (error) {
                    onError(error instanceof Error ? error : new Error(String(error)));
                }
            }

            // 开始读取流
            await read();
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '发送聊天消息失败';
            console.error('发送聊天消息（流式）失败:', errorMessage);
            onError(error instanceof Error ? error : new Error(errorMessage));
        }
    }

    /**
     * 开始讨论
     */
    async startDiscussion(request: DiscussionRequest): Promise<any> {
        try {
            return await this.request<any>(`${API_BASE_URL}/discussion/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });
        } catch (error) {
            console.error('开始讨论失败:', error);
            throw error;
        }
    }

    /**
     * 开始辩论
     */
    async startDebate(request: DebateRequest): Promise<any> {
        try {
            return await this.request<any>(`${API_BASE_URL}/debate/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });
        } catch (error) {
            console.error('开始辩论失败:', error);
            throw error;
        }
    }

    /**
     * 获取历史记录列表
     */
    async getHistoryList(): Promise<HistoryRecord[]> {
        try {
            const result = await this.request<any>(`${API_BASE_URL}/history/list`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return result.history_list || [];
        } catch (error) {
            console.error('获取历史记录列表失败:', error);
            return [];
        }
    }

    /**
     * 获取历史记录详情
     */
    async getHistoryDetail(index: number): Promise<HistoryRecord | null> {
        try {
            const result = await this.request<any>(`${API_BASE_URL}/history/detail/${index}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return result.history_detail || null;
        } catch (error) {
            console.error('获取历史记录详情失败:', error);
            return null;
        }
    }

    /**
     * 删除历史记录
     */
    async deleteHistory(index: number): Promise<boolean> {
        try {
            const result = await this.request<any>(`${API_BASE_URL}/history/delete/${index}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return result.success || false;
        } catch (error) {
            console.error('删除历史记录失败:', error);
            return false;
        }
    }

    /**
     * 清空所有历史记录
     */
    async clearAllHistory(): Promise<boolean> {
        try {
            const result = await this.request<any>(`${API_BASE_URL}/history/clear`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return result.success || false;
        } catch (error) {
            console.error('清空历史记录失败:', error);
            return false;
        }
    }

    /**
     * 保存API设置
     */
    async saveSettings(apiConfig: APIConfig, systemPrompt: SystemPrompt): Promise<boolean> {
        try {
            const result = await this.request<any>(`${API_BASE_URL}/settings/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    api_config: apiConfig,
                    system_prompt: systemPrompt,
                }),
            });
            return result.success || false;
        } catch (error) {
            console.error('保存设置失败:', error);
            return false;
        }
    }

    /**
     * 加载API设置
     */
    async loadSettings(): Promise<{ apiConfig: APIConfig; systemPrompt: SystemPrompt } | null> {
        try {
            const result = await this.request<any>(`${API_BASE_URL}/settings/load`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return {
                apiConfig: result.api_config || {},
                systemPrompt: result.system_prompt || {},
            };
        } catch (error) {
            console.error('加载设置失败:', error);
            return null;
        }
    }

    /**
     * 获取关于信息
     */
    async getAboutInfo(): Promise<any> {
        try {
            const result = await this.request<any>(`${API_BASE_URL}/about`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return result.about || {};
        } catch (error) {
            console.error('获取关于信息失败:', error);
            return {};
        }
    }

    /**
     * 获取错误统计信息
     */
    async getErrorStatistics(): Promise<any> {
        try {
            return await this.request<any>(`${API_BASE_URL}/error-monitor/statistics`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
        } catch (error) {
            console.error('获取错误统计信息失败:', error);
            return {
                error_counts: {},
                error_rate: 0,
                api_error_counts: {}
            };
        }
    }

    /**
     * 获取最近的错误记录
     */
    async getRecentErrors(count: number = 10): Promise<any> {
        try {
            return await this.request<any>(`${API_BASE_URL}/error-monitor/recent-errors?count=${count}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
        } catch (error) {
            console.error('获取最近错误记录失败:', error);
            return {
                recent_errors: []
            };
        }
    }

    /**
     * 清空错误记录
     */
    async clearErrorRecords(): Promise<boolean> {
        try {
            const result = await this.request<any>(`${API_BASE_URL}/error-monitor/clear`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            return result.success || false;
        } catch (error) {
            console.error('清空错误记录失败:', error);
            return false;
        }
    }
}

export default ApiService;