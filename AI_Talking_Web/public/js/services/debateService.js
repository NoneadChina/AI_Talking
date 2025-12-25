class DebateService {
    constructor(aiService) {
        this.isRunning = false;
        this.debateHistory = [];
        this.startTime = null;
        this.timeLimit = 0;
        this.aiService = aiService;
    }
    async startDebate(config, onMessage, onStatusUpdate, onError, onComplete) {
        if (this.isRunning) {
            onError('辩论已经在进行中');
            return;
        }
        this.isRunning = true;
        this.debateHistory = [];
        this.startTime = Date.now();
        this.timeLimit = config.timeLimit;
        try {
            // 验证输入
            if (!config.topic.trim()) {
                throw new Error('请输入辩论主题');
            }
            onStatusUpdate('准备开始辩论...');
            // 创建系统提示词
            const debateSystemPrompt = localStorage.getItem('debateSystemPrompt') || '';
            const ai1SystemPrompt = localStorage.getItem('debateAI1SystemPrompt') || '你是正方，支持这个观点';
            const ai2SystemPrompt = localStorage.getItem('debateAI2SystemPrompt') || '你是反方，反对这个观点';
            // 初始化辩论历史
            const commonPrompt = `${debateSystemPrompt}\n辩论主题: ${config.topic}`;
            let ai1Messages = [
                { role: 'system', content: `${commonPrompt}\n${ai1SystemPrompt}` },
                { role: 'user', content: `请开始你的辩论，支持这个观点：${config.topic}` }
            ];
            let ai2Messages = [
                { role: 'system', content: `${commonPrompt}\n${ai2SystemPrompt}` },
                { role: 'user', content: `请开始你的辩论，反对这个观点：${config.topic}` }
            ];
            // 第一轮：AI1先发言（正方）
            onStatusUpdate('正方AI正在思考...');
            const ai1FirstResponse = await this.aiService.getAIResponse(config.api1, config.model1, ai1Messages, config.temperature);
            if (!ai1FirstResponse.success) {
                throw new Error(`正方AI生成失败: ${ai1FirstResponse.error}`);
            }
            const ai1FirstMessage = {
                sender: 'ai1',
                content: ai1FirstResponse.content || '',
                timestamp: new Date()
            };
            this.debateHistory.push(ai1FirstMessage);
            onMessage(ai1FirstMessage);
            onStatusUpdate('正方AI发言完成');
            // 更新AI2的消息历史
            ai2Messages.push({
                role: 'assistant',
                content: ai1FirstResponse.content || ''
            });
            ai2Messages.push({
                role: 'user',
                content: '请针对正方的观点进行反驳'
            });
            // 进行剩余轮次的辩论
            for (let round = 1; round < config.rounds; round++) {
                // 检查时间限制
                if (!this.checkTimeLimit(onStatusUpdate)) {
                    return;
                }
                // 检查是否停止
                if (!this.isRunning) {
                    return;
                }
                // AI2发言（反方）
                onStatusUpdate('反方AI正在思考...');
                const ai2Response = await this.aiService.getAIResponse(config.api2, config.model2, ai2Messages, config.temperature);
                if (!ai2Response.success) {
                    throw new Error(`反方AI生成失败: ${ai2Response.error}`);
                }
                const ai2Message = {
                    sender: 'ai2',
                    content: ai2Response.content || '',
                    timestamp: new Date()
                };
                this.debateHistory.push(ai2Message);
                onMessage(ai2Message);
                onStatusUpdate('反方AI发言完成');
                // 更新AI1的消息历史
                ai1Messages.push({
                    role: 'assistant',
                    content: ai2Response.content || ''
                });
                ai1Messages.push({
                    role: 'user',
                    content: '请针对反方的观点进行反驳'
                });
                // 检查时间限制
                if (!this.checkTimeLimit(onStatusUpdate)) {
                    return;
                }
                // 检查是否停止
                if (!this.isRunning) {
                    return;
                }
                // AI1发言（正方）
                onStatusUpdate('正方AI正在思考...');
                const ai1Response = await this.aiService.getAIResponse(config.api1, config.model1, ai1Messages, config.temperature);
                if (!ai1Response.success) {
                    throw new Error(`正方AI生成失败: ${ai1Response.error}`);
                }
                const ai1Message = {
                    sender: 'ai1',
                    content: ai1Response.content || '',
                    timestamp: new Date()
                };
                this.debateHistory.push(ai1Message);
                onMessage(ai1Message);
                onStatusUpdate('正方AI发言完成');
                // 更新AI2的消息历史
                ai2Messages.push({
                    role: 'assistant',
                    content: ai1Response.content || ''
                });
                ai2Messages.push({
                    role: 'user',
                    content: '请针对正方的观点进行反驳'
                });
            }
            onStatusUpdate('辩论完成');
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
    stopDebate() {
        this.isRunning = false;
    }
    checkTimeLimit(onStatusUpdate) {
        if (this.timeLimit && this.startTime) {
            const elapsedTime = (Date.now() - this.startTime) / 1000;
            if (elapsedTime >= this.timeLimit) {
                onStatusUpdate('辩论时间已达限制');
                this.isRunning = false;
                return false;
            }
        }
        return true;
    }
    getDebateHistory() {
        return [...this.debateHistory];
    }
    isDebateRunning() {
        return this.isRunning;
    }
}
export default DebateService;
