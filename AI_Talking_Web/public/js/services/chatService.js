class ChatService {
    constructor(aiService) {
        this.isRunning = false;
        this.chatHistory = [];
        this.startTime = null;
        this.timeLimit = 0;
        this.aiService = aiService;
    }
    async startChat(config, onMessage, onStatusUpdate, onError, onComplete) {
        if (this.isRunning) {
            onError('对话已经在运行中');
            return;
        }
        this.isRunning = true;
        this.chatHistory = [];
        this.startTime = Date.now();
        this.timeLimit = config.timeLimit;
        try {
            // 验证输入
            if (!config.topic.trim()) {
                throw new Error('请输入讨论主题');
            }
            onStatusUpdate('准备开始对话...');
            // 创建系统提示词
            const commonSystemPrompt = localStorage.getItem('commonSystemPrompt') || '你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。';
            const ai1SystemPrompt = localStorage.getItem('ai1SystemPrompt') || '';
            const ai2SystemPrompt = localStorage.getItem('ai2SystemPrompt') || '';
            // 完整系统提示词
            const fullAi1SystemPrompt = `${commonSystemPrompt}${ai1SystemPrompt ? '\n' + ai1SystemPrompt : ''}`;
            const fullAi2SystemPrompt = `${commonSystemPrompt}${ai2SystemPrompt ? '\n' + ai2SystemPrompt : ''}`;
            // 初始化对话历史（与GUI版本保持一致）
            let ai1Messages = [
                { role: 'system', content: fullAi1SystemPrompt }
            ];
            // 用于存储AI 2的完整对话历史（不包含主题）
            const ai2History = [];
            // 显示初始状态信息
            onStatusUpdate(`两个AI开始围绕主题 '${config.topic}' 进行讨论`);
            onStatusUpdate(`AI 1: ${config.model1} (API: ${config.api1})`);
            onStatusUpdate(`AI 2: ${config.model2} (API: ${config.api2})`);
            // 添加时间限制信息到状态
            if (this.timeLimit) {
                onStatusUpdate(`时间限制: ${this.timeLimit} 秒`);
            }
            onStatusUpdate(`对话轮数: ${config.rounds} 轮`);
            // 进行对话轮次（与GUI版本保持一致的轮次处理）
            for (let round = 1; round <= config.rounds; round++) {
                // 检查是否已停止
                if (!this.isRunning) {
                    onStatusUpdate('对话已停止');
                    break;
                }
                // 检查时间限制 - 每轮开始时
                if (!this.checkTimeLimit(onStatusUpdate, true)) {
                    return;
                }
                onStatusUpdate(`----- 第 ${round}/${config.rounds} 轮对话开始 -----`);
                // AI1发言
                onStatusUpdate(`AI 1 的第 ${round} 轮发言中...`);
                let ai1CurrentMessages = [...ai1Messages];
                if (round === 1) {
                    // 第一轮：AI1使用包含主题的初始消息
                    ai1CurrentMessages.push({
                        role: 'user',
                        content: `请开始讨论主题：${config.topic}。请提供你的见解和观点。`
                    });
                }
                const ai1Response = await this.aiService.getAIResponse(config.api1, config.model1, ai1CurrentMessages, config.temperature);
                // 检查是否已停止
                if (!this.isRunning) {
                    onStatusUpdate('对话已停止');
                    break;
                }
                // 检查时间限制 - AI1发言后
                if (!this.checkTimeLimit(onStatusUpdate, false)) {
                    return;
                }
                // 处理空回复（与GUI版本保持一致）
                let ai1Content = ai1Response.success && ai1Response.content ? ai1Response.content.trim() : '';
                if (!ai1Content) {
                    onStatusUpdate(`警告: AI 1 的回复为空`);
                    ai1Content = '我对此主题没有特别的见解。';
                }
                // 显示AI1的回复
                const ai1Message = {
                    sender: `ai1 (${config.model1})`,
                    content: ai1Content,
                    timestamp: new Date()
                };
                this.chatHistory.push(ai1Message);
                onMessage(ai1Message);
                // AI1更新自己的对话历史（包含完整对话历史）
                ai1Messages.push({ role: 'assistant', content: ai1Content });
                // 检查是否已停止
                if (!this.isRunning) {
                    onStatusUpdate('对话已停止');
                    break;
                }
                // 检查时间限制 - AI2发言前
                if (!this.checkTimeLimit(onStatusUpdate, false)) {
                    return;
                }
                // 准备AI2的对话历史（与GUI版本保持一致）
                let ai2CurrentMessages = [{ role: 'system', content: fullAi2SystemPrompt }];
                if (round === 1) {
                    // 第一次对话时，将主题和AI1的回答一起传给AI2
                    ai2CurrentMessages.push({
                        role: 'user',
                        content: `讨论主题：${config.topic}。\nAI 1的观点：${ai1Content}`
                    });
                }
                else {
                    // 后续对话，提供完整的对话历史
                    ai2CurrentMessages = ai2CurrentMessages.concat(ai2History);
                }
                // AI2发言
                onStatusUpdate(`AI 2 的第 ${round} 轮回应中...`);
                const ai2Response = await this.aiService.getAIResponse(config.api2, config.model2, ai2CurrentMessages, config.temperature);
                // 检查是否已停止
                if (!this.isRunning) {
                    onStatusUpdate('对话已停止');
                    break;
                }
                // 检查时间限制 - AI2发言后
                if (!this.checkTimeLimit(onStatusUpdate, false)) {
                    return;
                }
                // 处理空回复（与GUI版本保持一致）
                let ai2Content = ai2Response.success && ai2Response.content ? ai2Response.content.trim() : '';
                if (!ai2Content) {
                    onStatusUpdate(`警告: AI 2 的回复为空`);
                    ai2Content = '我对此主题没有特别的见解。';
                }
                // 显示AI2的回复
                const ai2Message = {
                    sender: `ai2 (${config.model2})`,
                    content: ai2Content,
                    timestamp: new Date()
                };
                this.chatHistory.push(ai2Message);
                onMessage(ai2Message);
                // 更新AI2的历史记录（保存完整对话历史，不包含主题）
                ai2History.push({ role: 'user', content: ai1Content });
                ai2History.push({ role: 'assistant', content: ai2Content });
                // 将AI2的回应添加到AI1的对话历史（确保完整对话历史）
                ai1Messages.push({ role: 'user', content: ai2Content });
            }
            // 计算总耗时
            if (this.startTime) {
                const totalTime = (Date.now() - this.startTime) / 1000;
                onStatusUpdate(`对话结束，总耗时: ${totalTime.toFixed(2)} 秒`);
            }
            onComplete();
        }
        catch (error) {
            onError(error instanceof Error ? error.message : '未知错误');
        }
        finally {
            this.isRunning = false;
            this.startTime = null;
        }
    }
    stopChat() {
        this.isRunning = false;
    }
    /**
     * 检查时间限制（与GUI版本保持一致的实现）
     * @param onStatusUpdate 状态更新回调
     * @param showCurrentTime 是否显示当前耗时
     * @returns 是否继续对话
     */
    checkTimeLimit(onStatusUpdate, showCurrentTime) {
        if (this.timeLimit && this.startTime) {
            const elapsedTime = (Date.now() - this.startTime) / 1000;
            if (showCurrentTime) {
                onStatusUpdate(`当前耗时: ${elapsedTime.toFixed(1)}/${this.timeLimit}秒`);
            }
            if (elapsedTime >= this.timeLimit) {
                onStatusUpdate(`时间限制已达到 (${elapsedTime.toFixed(1)}/${this.timeLimit}秒)，对话结束`);
                this.isRunning = false;
                return false;
            }
        }
        return true;
    }
    getChatHistory() {
        return [...this.chatHistory];
    }
    isChatRunning() {
        return this.isRunning;
    }
}
export default ChatService;
