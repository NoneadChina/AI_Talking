const LanguageDetector = i18nextBrowserLanguageDetector;
import AIService from './services/aiService';
import ChatService from './services/chatService';
import DebateService from './services/debateService';
import ApiService from './services/apiService';
// 初始化i18next国际化
i18next
    .use(LanguageDetector)
    .init({
    resources: {
        en: {
            translation: {
                chat: 'Chat',
                discussion: 'Discussion',
                debate: 'Debate',
                settings: 'Settings',
                history: 'History',
                about: 'About',
                send: 'Send',
                save: 'Save',
                load: 'Load',
                export: 'Export',
                clear: 'Clear',
                start: 'Start',
                stop: 'Stop',
                topic: 'Topic',
                model: 'Model',
                api: 'API',
                rounds: 'Rounds',
                temperature: 'Temperature',
                timeLimit: 'Time Limit',
                apiKey: 'API Key',
                baseUrl: 'Base URL',
                systemPrompt: 'System Prompt',
                status: 'Status',
                ready: 'Ready',
                loading: 'Loading...',
                success: 'Success',
                error: 'Error',
                pleaseEnterTopic: 'Please enter a topic',
                pleaseSelectModel: 'Please select a model',
                sendingMessage: 'Sending message...',
                gettingResponse: 'Getting response...',
                messageSent: 'Message sent',
                responseReceived: 'Response received',
                chatStarted: 'Chat started',
                chatStopped: 'Chat stopped',
                debateStarted: 'Debate started',
                debateStopped: 'Debate stopped',
                settingsSaved: 'Settings saved',
                settingsLoaded: 'Settings loaded',
                historySaved: 'History saved',
                historyLoaded: 'History loaded',
                historyCleared: 'History cleared',
                modelListUpdated: 'Model list updated',
                gettingModelList: 'Getting model list...',
                noModelsFound: 'No models found',
                failedToGetModels: 'Failed to get models',
                failedToSendMessage: 'Failed to send message',
                failedToGetResponse: 'Failed to get response',
                failedToStartChat: 'Failed to start chat',
                failedToStopChat: 'Failed to stop chat',
                failedToStartDebate: 'Failed to start debate',
                failedToStopDebate: 'Failed to stop debate',
                failedToSaveSettings: 'Failed to save settings',
                failedToLoadSettings: 'Failed to load settings',
                failedToSaveHistory: 'Failed to save history',
                failedToLoadHistory: 'Failed to load history',
                failedToClearHistory: 'Failed to clear history',
                failedToExportHistory: 'Failed to export history',
                failedToDeleteHistory: 'Failed to delete history',
                failedToGetHistoryList: 'Failed to get history list',
                failedToGetHistoryDetail: 'Failed to get history detail',
                failedToUpdateModelList: 'Failed to update model list',
                failedToGetOllamaModels: 'Failed to get Ollama models',
                failedToGetOpenAIModels: 'Failed to get OpenAI models',
                failedToGetDeepSeekModels: 'Failed to get DeepSeek models',
                pleaseWait: 'Please wait...',
                yes: 'Yes',
                no: 'No',
                cancel: 'Cancel',
                ok: 'OK',
                confirm: 'Confirm',
                delete: 'Delete',
                selectAll: 'Select All',
                deselectAll: 'Deselect All',
                deleteSelected: 'Delete Selected',
                clearAll: 'Clear All',
                exportSelected: 'Export Selected',
                exportCurrent: 'Export Current',
                deleteCurrent: 'Delete Current',
                refresh: 'Refresh',
                search: 'Search',
                filter: 'Filter',
                sort: 'Sort',
                ascending: 'Ascending',
                descending: 'Descending',
                page: 'Page',
                of: 'of',
                perPage: 'per page',
                first: 'First',
                previous: 'Previous',
                next: 'Next',
                last: 'Last',
                showing: 'Showing',
                to: 'to',
                results: 'results',
                total: 'Total',
                actions: 'Actions',
                details: 'Details',
                edit: 'Edit',
                view: 'View',
                download: 'Download',
                upload: 'Upload',
                import: 'Import',
                share: 'Share',
                copy: 'Copy',
                paste: 'Paste',
                cut: 'Cut',
                undo: 'Undo',
                redo: 'Redo',
                find: 'Find',
                replace: 'Replace',
                findNext: 'Find Next',
                findPrevious: 'Find Previous',
                replaceAll: 'Replace All',
                goTo: 'Go To',
                line: 'Line',
                column: 'Column',
                saveAs: 'Save As',
                open: 'Open',
                new: 'New',
                close: 'Close',
                exit: 'Exit',
                help: 'Help',
                preferences: 'Preferences',
                language: 'Language',
                theme: 'Theme',
                dark: 'Dark',
                light: 'Light',
                system: 'System',
                font: 'Font',
                fontSize: 'Font Size',
                reset: 'Reset',
                apply: 'Apply',
                areYouSure: 'Are you sure?',
                thisActionCannotBeUndone: 'This action cannot be undone.',
                pleaseConfirm: 'Please confirm.',
                deleteSelectedItems: 'Delete selected items?',
                clearAllItems: 'Clear all items?',
                yesDelete: 'Yes, delete',
                yesClear: 'Yes, clear',
                warning: 'Warning',
                info: 'Info',
                notice: 'Notice',
                message: 'Message',
                detail: 'Detail',
                moreInfo: 'More Info',
                lessInfo: 'Less Info',
                hide: 'Hide',
                show: 'Show',
                expand: 'Expand',
                collapse: 'Collapse',
                expandAll: 'Expand All',
                collapseAll: 'Collapse All',
                processing: 'Processing...',
                saving: 'Saving...',
                loadingData: 'Loading data...',
                savingData: 'Saving data...',
                noData: 'No data available.',
                noResults: 'No results found.',
                searchResults: 'Search results',
                filterResults: 'Filter results',
                sortResults: 'Sort results',
                pageResults: 'Page results',
                totalResults: 'Total results',
                showingResults: 'Showing results',
                fromToResults: 'from {{from}} to {{to}} of {{total}} results',
                previousPage: 'Previous page',
                nextPage: 'Next page',
                firstPage: 'First page',
                lastPage: 'Last page',
                pageNumber: 'Page number',
                pageSize: 'Page size',
                itemsPerPage: 'Items per page',
                jumpToPage: 'Jump to page',
                go: 'Go',
                selectPageSize: 'Select page size',
                refreshData: 'Refresh data',
                reloadData: 'Reload data',
                reload: 'Reload',
                add: 'Add',
                remove: 'Remove',
                confirmAction: 'Confirm action',
                pleaseConfirmAction: 'Please confirm this action.',
                thisActionIsIrreversible: 'This action is irreversible.',
                areYouSureYouWantToProceed: 'Are you sure you want to proceed?',
                yesProceed: 'Yes, proceed',
                noCancel: 'No, cancel',
                successMessage: 'Operation completed successfully.',
                errorMessage: 'Operation failed. Please try again.',
                warningMessage: 'Please review your input carefully.',
                infoMessage: 'Please note the following information.',
                noticeMessage: 'This is an important notice.',
                messageTitle: '{{type}} Message',
                closeMessage: 'Close message',
                moreDetails: 'More details',
                lessDetails: 'Less details',
                hideDetails: 'Hide details',
                showDetails: 'Show details',
                expandDetails: 'Expand details',
                collapseDetails: 'Collapse details',
                copyDetails: 'Copy details',
                copyToClipboard: 'Copy to clipboard',
                copiedToClipboard: 'Copied to clipboard!',
                failedToCopy: 'Failed to copy',
                tryAgain: 'Try again',
                dismiss: 'Dismiss',
                acknowledge: 'Acknowledge',
                accept: 'Accept',
                reject: 'Reject',
                agree: 'Agree',
                disagree: 'Disagree',
                maybe: 'Maybe',
                sure: 'Sure',
                notSure: 'Not sure',
                proceed: 'Proceed',
                abort: 'Abort',
                retry: 'Retry',
                ignore: 'Ignore',
                skip: 'Skip',
                continue: 'Continue',
                pause: 'Pause',
                resume: 'Resume',
                restart: 'Restart',
                shutdown: 'Shutdown',
                logOff: 'Log Off',
                signIn: 'Sign In',
                signOut: 'Sign Out',
                register: 'Register',
                login: 'Login',
                logout: 'Logout',
                username: 'Username',
                password: 'Password',
                email: 'Email',
                firstName: 'First Name',
                lastName: 'Last Name',
                fullName: 'Full Name',
                displayName: 'Display Name',
                phone: 'Phone',
                address: 'Address',
                city: 'City',
                state: 'State',
                zipCode: 'Zip Code',
                country: 'Country',
                website: 'Website',
                bio: 'Bio',
                profile: 'Profile',
                account: 'Account',
                security: 'Security',
                privacy: 'Privacy',
                notifications: 'Notifications'
            }
        },
        zh: {
            translation: {
                chat: '聊天',
                discussion: '讨论',
                debate: '辩论',
                settings: '设置',
                history: '历史',
                about: '关于',
                send: '发送',
                save: '保存',
                load: '加载',
                export: '导出',
                clear: '清空',
                start: '开始',
                stop: '停止',
                topic: '主题',
                model: '模型',
                api: 'API',
                rounds: '轮数',
                temperature: '温度',
                timeLimit: '时间限制',
                apiKey: 'API密钥',
                baseUrl: '基础URL',
                systemPrompt: '系统提示词',
                status: '状态',
                ready: '就绪',
                loading: '加载中...',
                success: '成功',
                error: '错误',
                pleaseEnterTopic: '请输入主题',
                pleaseSelectModel: '请选择模型',
                sendingMessage: '发送消息中...',
                gettingResponse: '获取响应中...',
                messageSent: '消息已发送',
                responseReceived: '已收到响应',
                chatStarted: '聊天已开始',
                chatStopped: '聊天已停止',
                debateStarted: '辩论已开始',
                debateStopped: '辩论已停止',
                settingsSaved: '设置已保存',
                settingsLoaded: '设置已加载',
                historySaved: '历史已保存',
                historyLoaded: '历史已加载',
                historyCleared: '历史已清空',
                modelListUpdated: '模型列表已更新',
                gettingModelList: '获取模型列表中...',
                noModelsFound: '未找到模型',
                failedToGetModels: '获取模型失败',
                failedToSendMessage: '发送消息失败',
                failedToGetResponse: '获取响应失败',
                failedToStartChat: '开始聊天失败',
                failedToStopChat: '停止聊天失败',
                failedToStartDebate: '开始辩论失败',
                failedToStopDebate: '停止辩论失败',
                failedToSaveSettings: '保存设置失败',
                failedToLoadSettings: '加载设置失败',
                failedToSaveHistory: '保存历史失败',
                failedToLoadHistory: '加载历史失败',
                failedToClearHistory: '清空历史失败',
                failedToExportHistory: '导出历史失败',
                failedToDeleteHistory: '删除历史失败',
                failedToGetHistoryList: '获取历史列表失败',
                failedToGetHistoryDetail: '获取历史详情失败',
                failedToUpdateModelList: '更新模型列表失败',
                failedToGetOllamaModels: '获取Ollama模型失败',
                failedToGetOpenAIModels: '获取OpenAI模型失败',
                failedToGetDeepSeekModels: '获取DeepSeek模型失败',
                pleaseWait: '请稍候...',
                yes: '是',
                no: '否',
                cancel: '取消',
                ok: '确定',
                confirm: '确认',
                delete: '删除',
                selectAll: '全选',
                deselectAll: '取消全选',
                deleteSelected: '删除选中',
                clearAll: '清空所有',
                exportSelected: '导出选中',
                exportCurrent: '导出当前',
                deleteCurrent: '删除当前',
                refresh: '刷新',
                search: '搜索',
                filter: '过滤',
                sort: '排序',
                ascending: '升序',
                descending: '降序',
                page: '页',
                of: '共',
                perPage: '每页',
                first: '首页',
                previous: '上一页',
                next: '下一页',
                last: '末页',
                showing: '显示',
                to: '到',
                results: '条结果',
                total: '总计',
                actions: '操作',
                details: '详情',
                edit: '编辑',
                view: '查看',
                download: '下载',
                upload: '上传',
                import: '导入',
                share: '分享',
                copy: '复制',
                paste: '粘贴',
                cut: '剪切',
                undo: '撤销',
                redo: '重做',
                find: '查找',
                replace: '替换',
                findNext: '查找下一个',
                findPrevious: '查找上一个',
                replaceAll: '全部替换',
                goTo: '转到',
                line: '行',
                column: '列',
                saveAs: '另存为',
                open: '打开',
                new: '新建',
                close: '关闭',
                exit: '退出',
                help: '帮助',
                preferences: '首选项',
                language: '语言',
                theme: '主题',
                dark: '深色',
                light: '浅色',
                system: '系统',
                font: '字体',
                fontSize: '字号',
                reset: '重置',
                apply: '应用',
                areYouSure: '确定吗？',
                thisActionCannotBeUndone: '此操作不可撤销。',
                pleaseConfirm: '请确认。',
                deleteSelectedItems: '删除选中项？',
                clearAllItems: '清空所有项？',
                yesDelete: '是，删除',
                yesClear: '是，清空',
                warning: '警告',
                info: '信息',
                notice: '通知',
                message: '消息',
                detail: '详情',
                moreInfo: '更多信息',
                lessInfo: '更少信息',
                hide: '隐藏',
                show: '显示',
                expand: '展开',
                collapse: '折叠',
                expandAll: '全部展开',
                collapseAll: '全部折叠',
                processing: '处理中...',
                saving: '保存中...',
                loadingData: '加载数据中...',
                savingData: '保存数据中...',
                noData: '无可用数据。',
                noResults: '未找到结果。',
                searchResults: '搜索结果',
                filterResults: '过滤结果',
                sortResults: '排序结果',
                pageResults: '分页结果',
                totalResults: '总结果数',
                showingResults: '显示结果',
                fromToResults: '从 {{from}} 到 {{to}}，共 {{total}} 条结果',
                previousPage: '上一页',
                nextPage: '下一页',
                firstPage: '首页',
                lastPage: '末页',
                pageNumber: '页码',
                pageSize: '每页条数',
                itemsPerPage: '每页条数',
                jumpToPage: '跳转到页',
                go: '前往',
                selectPageSize: '选择每页条数',
                refreshData: '刷新数据',
                reloadData: '重新加载数据',
                reload: '重新加载',
                add: '添加',
                remove: '移除',
                confirmAction: '确认操作',
                pleaseConfirmAction: '请确认此操作。',
                thisActionIsIrreversible: '此操作不可逆。',
                areYouSureYouWantToProceed: '确定要继续吗？',
                yesProceed: '是，继续',
                noCancel: '否，取消',
                successMessage: '操作已成功完成。',
                errorMessage: '操作失败。请重试。',
                warningMessage: '请仔细检查您的输入。',
                infoMessage: '请注意以下信息。',
                noticeMessage: '这是一条重要通知。',
                messageTitle: '{{type}} 消息',
                closeMessage: '关闭消息',
                moreDetails: '更多详情',
                lessDetails: '更少详情',
                hideDetails: '隐藏详情',
                showDetails: '显示详情',
                expandDetails: '展开详情',
                collapseDetails: '折叠详情',
                copyDetails: '复制详情',
                copyToClipboard: '复制到剪贴板',
                copiedToClipboard: '已复制到剪贴板！',
                failedToCopy: '复制失败',
                tryAgain: '重试',
                dismiss: '忽略',
                acknowledge: '确认',
                accept: '接受',
                reject: '拒绝',
                agree: '同意',
                disagree: '不同意',
                maybe: '也许',
                sure: '确定',
                notSure: '不确定',
                proceed: '继续',
                abort: '中止',
                retry: '重试',
                ignore: '忽略',
                skip: '跳过',
                continue: '继续',
                pause: '暂停',
                resume: '恢复',
                restart: '重新开始',
                shutdown: '关闭',
                logOff: '注销',
                signIn: '登录',
                signOut: '退出',
                register: '注册',
                login: '登录',
                logout: '退出',
                username: '用户名',
                password: '密码',
                email: '邮箱',
                firstName: '名',
                lastName: '姓',
                fullName: '全名',
                displayName: '显示名称',
                phone: '电话',
                address: '地址',
                city: '城市',
                state: '州/省',
                zipCode: '邮政编码',
                country: '国家/地区',
                website: '网站',
                bio: '个人简介',
                profile: '个人资料',
                account: '账户',
                security: '安全',
                privacy: '隐私',
                notifications: '通知'
            }
        }
    },
    fallbackLng: 'zh',
    debug: true,
    interpolation: {
        escapeValue: false
    }
});
class App {
    constructor() {
        this.isChatRunning = false;
        this.isDebateRunning = false;
        this.chatHistory = [];
        // 检查是否已登录
        const token = localStorage.getItem('token');
        if (token) {
            // 已登录，隐藏登录模态框
            this.hideLoginModal();
        }
        // 初始化默认设置
        const defaultSettings = {
            openai: {
                key: localStorage.getItem('openaiKey') || '',
                baseUrl: localStorage.getItem('openaiBaseUrl') || 'https://api.openai.com/v1'
            },
            deepseek: {
                key: localStorage.getItem('deepseekKey') || '',
                baseUrl: localStorage.getItem('deepseekBaseUrl') || 'https://api.deepseek.com/v1'
            },
            ollama: { url: localStorage.getItem('ollamaUrl') || 'http://ai.corp.nonead.com:11434', key: localStorage.getItem('ollamaKey') || '' },
            systemPrompts: {
                common: localStorage.getItem('commonSystemPrompt') || '你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。',
                ai1: localStorage.getItem('ai1SystemPrompt') || '',
                ai2: localStorage.getItem('ai2SystemPrompt') || ''
            }
        };
        this.aiService = new AIService(defaultSettings);
        this.chatService = new ChatService(this.aiService);
        this.debateService = new DebateService(this.aiService);
        this.apiService = new ApiService();
        this.initializeEventListeners();
        this.loadSettings();
    }
    initializeEventListeners() {
        // 登录相关事件监听器
        document.getElementById('loginForm')?.addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerBtn')?.addEventListener('click', () => this.showRegisterModal());
        // 开始对话按钮
        document.getElementById('startChat')?.addEventListener('click', () => this.startChat());
        // 停止对话按钮
        document.getElementById('stopChat')?.addEventListener('click', () => this.stopChat());
        // 保存设置按钮
        document.getElementById('saveSettings')?.addEventListener('click', () => this.saveSettings());
        // 获取Ollama模型清单按钮
        document.getElementById('fetchOllamaModels')?.addEventListener('click', () => this.fetchAndDisplayOllamaModels());
        // 导出PDF按钮
        document.getElementById('exportPdf')?.addEventListener('click', () => this.exportPdf());
        // API类型选择变化，更新模型列表
        document.getElementById('api1')?.addEventListener('change', () => this.updateModelList('model1'));
        document.getElementById('api2')?.addEventListener('change', () => this.updateModelList('model2'));
        // 辩论模式事件监听器
        document.getElementById('startDebate')?.addEventListener('click', () => this.startDebate());
        document.getElementById('stopDebate')?.addEventListener('click', () => this.stopDebate());
        document.getElementById('debate-api1')?.addEventListener('change', () => this.updateModelList('debate-model1'));
        document.getElementById('debate-api2')?.addEventListener('change', () => this.updateModelList('debate-model2'));
        // 人类聊天模式事件监听器
        document.getElementById('human-provider')?.addEventListener('change', () => this.updateModelList('human-model'));
        document.getElementById('sendHumanMessage')?.addEventListener('click', () => this.sendHumanMessage());
        document.getElementById('clearHumanChat')?.addEventListener('click', () => this.clearHumanChat());
        // 历史管理事件监听器
        document.getElementById('refreshHistory')?.addEventListener('click', () => this.loadHistory());
        document.getElementById('deleteSelectedHistory')?.addEventListener('click', () => this.deleteSelectedHistory());
        document.getElementById('clearAllHistory')?.addEventListener('click', () => this.clearAllHistory());
        document.getElementById('exportHistory')?.addEventListener('click', () => this.exportHistory());
        document.getElementById('selectAllHistory')?.addEventListener('change', (e) => this.selectAllHistory(e));
    }
    async loadSettings() {
        try {
            // 从后端API加载设置
            const settings = await this.apiService.loadSettings();
            if (settings) {
                // 加载API设置
                const openaiKeyInput = document.getElementById('openaiKey');
                const openaiBaseUrlInput = document.getElementById('openaiBaseUrl');
                const deepseekKeyInput = document.getElementById('deepseekKey');
                const deepseekBaseUrlInput = document.getElementById('deepseekBaseUrl');
                const ollamaUrlInput = document.getElementById('ollamaUrl');
                const ollamaKeyInput = document.getElementById('ollamaKey');
                openaiKeyInput.value = settings.apiConfig.openai.api_key || localStorage.getItem('openaiKey') || '';
                openaiBaseUrlInput.value = settings.apiConfig.openai.base_url || localStorage.getItem('openaiBaseUrl') || 'https://api.openai.com/v1';
                deepseekKeyInput.value = settings.apiConfig.deepseek.api_key || localStorage.getItem('deepseekKey') || '';
                deepseekBaseUrlInput.value = settings.apiConfig.deepseek.base_url || localStorage.getItem('deepseekBaseUrl') || 'https://api.deepseek.com/v1';
                ollamaUrlInput.value = settings.apiConfig.ollama.base_url || localStorage.getItem('ollamaUrl') || 'http://ai.corp.nonead.com:11434';
                ollamaKeyInput.value = settings.apiConfig.ollama.api_key || localStorage.getItem('ollamaKey') || '';
                // 加载系统提示词
                const chatSystemPromptInput = document.getElementById('chatSystemPrompt');
                const discussionSystemPromptInput = document.getElementById('discussionSystemPrompt');
                const discussionAI1SystemPromptInput = document.getElementById('discussionAI1SystemPrompt');
                const discussionAI2SystemPromptInput = document.getElementById('discussionAI2SystemPrompt');
                const debateSystemPromptInput = document.getElementById('debateSystemPrompt');
                const debateAI1SystemPromptInput = document.getElementById('debateAI1SystemPrompt');
                const debateAI2SystemPromptInput = document.getElementById('debateAI2SystemPrompt');
                if (chatSystemPromptInput) {
                    chatSystemPromptInput.value = settings.systemPrompt.chat_system_prompt || '';
                }
                if (discussionSystemPromptInput) {
                    discussionSystemPromptInput.value = settings.systemPrompt.discussion_system_prompt || '';
                }
                if (discussionAI1SystemPromptInput) {
                    discussionAI1SystemPromptInput.value = settings.systemPrompt.discussion_ai1_system_prompt || '';
                }
                if (discussionAI2SystemPromptInput) {
                    discussionAI2SystemPromptInput.value = settings.systemPrompt.discussion_ai2_system_prompt || '';
                }
                if (debateSystemPromptInput) {
                    debateSystemPromptInput.value = settings.systemPrompt.debate_system_prompt || '';
                }
                if (debateAI1SystemPromptInput) {
                    debateAI1SystemPromptInput.value = settings.systemPrompt.debate_ai1_system_prompt || '';
                }
                if (debateAI2SystemPromptInput) {
                    debateAI2SystemPromptInput.value = settings.systemPrompt.debate_ai2_system_prompt || '';
                }
            }
        }
        catch (error) {
            console.error('加载设置失败:', error);
        }
        // 加载讨论模式设置
        const topicInput = document.getElementById('topic');
        const api1Select = document.getElementById('api1');
        const model1Select = document.getElementById('model1');
        const api2Select = document.getElementById('api2');
        const model2Select = document.getElementById('model2');
        const roundsInput = document.getElementById('rounds');
        const timeLimitInput = document.getElementById('timeLimit');
        const temperatureInput = document.getElementById('temperature');
        topicInput.value = localStorage.getItem('topic') || '';
        api1Select.value = localStorage.getItem('api1') || 'ollama';
        model1Select.value = localStorage.getItem('model1') || 'qwen3:14b';
        api2Select.value = localStorage.getItem('api2') || 'ollama';
        model2Select.value = localStorage.getItem('model2') || 'deepseek-r1:14b';
        roundsInput.value = localStorage.getItem('rounds') || '5';
        timeLimitInput.value = localStorage.getItem('timeLimit') || '0';
        temperatureInput.value = localStorage.getItem('temperature') || '1.0';
        // 更新显示值
        document.getElementById('rounds-value').textContent = roundsInput.value;
        document.getElementById('timeLimit-value').textContent = timeLimitInput.value === '0' ? '无限制' : timeLimitInput.value;
        // 加载辩论模式设置
        const debateTopicInput = document.getElementById('debate-topic');
        const debateApi1Select = document.getElementById('debate-api1');
        const debateModel1Select = document.getElementById('debate-model1');
        const debateApi2Select = document.getElementById('debate-api2');
        const debateModel2Select = document.getElementById('debate-model2');
        debateTopicInput.value = localStorage.getItem('debate-topic') || '';
        debateApi1Select.value = localStorage.getItem('debate-api1') || 'ollama';
        debateModel1Select.value = localStorage.getItem('debate-model1') || 'qwen3:14b';
        debateApi2Select.value = localStorage.getItem('debate-api2') || 'ollama';
        debateModel2Select.value = localStorage.getItem('debate-model2') || 'deepseek-r1:14b';
        // 加载系统提示词
        const commonSystemPromptInput = document.getElementById('commonSystemPrompt');
        const ai1SystemPromptInput = document.getElementById('ai1SystemPrompt');
        const ai2SystemPromptInput = document.getElementById('ai2SystemPrompt');
        commonSystemPromptInput.value = localStorage.getItem('commonSystemPrompt') || '你是一个参与讨论的AI助手。请根据收到的内容进行回应，言简意赅，只回答相关的问题，不要扩展，回答越简洁越好。';
        ai1SystemPromptInput.value = localStorage.getItem('ai1SystemPrompt') || '';
        ai2SystemPromptInput.value = localStorage.getItem('ai2SystemPrompt') || '';
        // 加载聊天历史
        const savedChatHistory = localStorage.getItem('chatHistory');
        if (savedChatHistory) {
            try {
                this.chatHistory = JSON.parse(savedChatHistory);
                // 重新渲染聊天历史
                for (const message of this.chatHistory) {
                    await this.appendToChatHistory(message);
                }
            }
            catch (error) {
                console.error('Failed to parse saved chat history:', error);
                this.chatHistory = [];
            }
        }
        // 初始化所有模式的模型列表
        this.updateModelList('model1');
        this.updateModelList('model2');
        this.updateModelList('debate-model1');
        this.updateModelList('debate-model2');
        this.updateModelList('human-model');
    }
    async saveSettings() {
        try {
            // API设置
            const openaiKeyInput = document.getElementById('openaiKey');
            const openaiBaseUrlInput = document.getElementById('openaiBaseUrl');
            const deepseekKeyInput = document.getElementById('deepseekKey');
            const deepseekBaseUrlInput = document.getElementById('deepseekBaseUrl');
            const ollamaUrlInput = document.getElementById('ollamaUrl');
            const ollamaKeyInput = document.getElementById('ollamaKey');
            // 讨论模式设置
            const topicInput = document.getElementById('topic');
            const api1Select = document.getElementById('api1');
            const model1Select = document.getElementById('model1');
            const api2Select = document.getElementById('api2');
            const model2Select = document.getElementById('model2');
            const roundsInput = document.getElementById('rounds');
            const timeLimitInput = document.getElementById('timeLimit');
            const temperatureInput = document.getElementById('temperature');
            // 辩论模式设置
            const debateTopicInput = document.getElementById('debate-topic');
            const debateApi1Select = document.getElementById('debate-api1');
            const debateModel1Select = document.getElementById('debate-model1');
            const debateApi2Select = document.getElementById('debate-api2');
            const debateModel2Select = document.getElementById('debate-model2');
            // 系统提示词
            const chatSystemPromptInput = document.getElementById('chatSystemPrompt');
            const discussionSystemPromptInput = document.getElementById('discussionSystemPrompt');
            const discussionAI1SystemPromptInput = document.getElementById('discussionAI1SystemPrompt');
            const discussionAI2SystemPromptInput = document.getElementById('discussionAI2SystemPrompt');
            const debateSystemPromptInput = document.getElementById('debateSystemPrompt');
            const debateAI1SystemPromptInput = document.getElementById('debateAI1SystemPrompt');
            const debateAI2SystemPromptInput = document.getElementById('debateAI2SystemPrompt');
            // 保存到localStorage
            // API设置
            localStorage.setItem('openaiKey', openaiKeyInput.value);
            localStorage.setItem('openaiBaseUrl', openaiBaseUrlInput.value);
            localStorage.setItem('deepseekKey', deepseekKeyInput.value);
            localStorage.setItem('deepseekBaseUrl', deepseekBaseUrlInput.value);
            localStorage.setItem('ollamaUrl', ollamaUrlInput.value);
            localStorage.setItem('ollamaKey', ollamaKeyInput.value);
            // 讨论模式设置
            localStorage.setItem('topic', topicInput.value);
            localStorage.setItem('api1', api1Select.value);
            localStorage.setItem('model1', model1Select.value);
            localStorage.setItem('api2', api2Select.value);
            localStorage.setItem('model2', model2Select.value);
            localStorage.setItem('rounds', roundsInput.value);
            localStorage.setItem('timeLimit', timeLimitInput.value);
            localStorage.setItem('temperature', temperatureInput.value);
            // 辩论模式设置
            localStorage.setItem('debate-topic', debateTopicInput.value);
            localStorage.setItem('debate-api1', debateApi1Select.value);
            localStorage.setItem('debate-model1', debateModel1Select.value);
            localStorage.setItem('debate-api2', debateApi2Select.value);
            localStorage.setItem('debate-model2', debateModel2Select.value);
            // 构建API配置对象
            const apiConfig = {
                openai: {
                    api_key: openaiKeyInput.value,
                    base_url: openaiBaseUrlInput.value
                },
                deepseek: {
                    api_key: deepseekKeyInput.value,
                    base_url: deepseekBaseUrlInput.value
                },
                ollama: {
                    base_url: ollamaUrlInput.value,
                    api_key: ollamaKeyInput.value
                }
            };
            // 构建系统提示词对象
            const systemPrompt = {
                chat_system_prompt: chatSystemPromptInput?.value || '',
                discussion_system_prompt: discussionSystemPromptInput?.value || '',
                discussion_ai1_system_prompt: discussionAI1SystemPromptInput?.value || '',
                discussion_ai2_system_prompt: discussionAI2SystemPromptInput?.value || '',
                debate_system_prompt: debateSystemPromptInput?.value || '',
                debate_ai1_system_prompt: debateAI1SystemPromptInput?.value || '',
                debate_ai2_system_prompt: debateAI2SystemPromptInput?.value || ''
            };
            // 调用后端API保存设置
            const success = await this.apiService.saveSettings(apiConfig, systemPrompt);
            if (success) {
                // 更新AI服务设置
                const newSettings = {
                    openai: {
                        key: openaiKeyInput.value,
                        baseUrl: openaiBaseUrlInput.value
                    },
                    deepseek: {
                        key: deepseekKeyInput.value,
                        baseUrl: deepseekBaseUrlInput.value
                    },
                    ollama: { url: ollamaUrlInput.value, key: ollamaKeyInput.value },
                    systemPrompts: {
                        common: chatSystemPromptInput?.value || '',
                        ai1: discussionAI1SystemPromptInput?.value || '',
                        ai2: discussionAI2SystemPromptInput?.value || ''
                    }
                };
                this.aiService.updateSettings(newSettings);
                // 更新显示值
                document.getElementById('rounds-value').textContent = roundsInput.value;
                document.getElementById('timeLimit-value').textContent = timeLimitInput.value === '0' ? '无限制' : timeLimitInput.value;
                // 保存聊天历史到localStorage
                localStorage.setItem('chatHistory', JSON.stringify(this.chatHistory));
                // 显示保存成功提示
                this.updateStatus('设置已保存');
            }
            else {
                this.showErrorMessage('保存设置失败');
            }
        }
        catch (error) {
            console.error('保存设置失败:', error);
            this.showErrorMessage('保存设置失败');
        }
    }
    /**
     * 获取并显示Ollama模型清单
     */
    async fetchAndDisplayOllamaModels() {
        try {
            this.updateStatus('获取Ollama模型清单中...');
            const modelsListDiv = document.getElementById('ollamaModelsList');
            if (!modelsListDiv) {
                console.error('Ollama models list div not found');
                return;
            }
            // 显示加载状态
            modelsListDiv.innerHTML = '<div class="loading">加载中...</div>';
            // 获取Ollama模型列表
            const models = await this.aiService.getOllamaModels();
            // 清空并显示模型列表
            modelsListDiv.innerHTML = '';
            if (models.length === 0) {
                modelsListDiv.innerHTML = '<div class="no-models">未找到Ollama模型</div>';
                return;
            }
            // 创建模型列表
            const ul = document.createElement('ul');
            models.forEach(model => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <strong>${model.name}</strong><br>
                    <small>大小: ${(model.size / 1024 / 1024 / 1024).toFixed(2)} GB | 修改时间: ${new Date(model.modified_at).toLocaleString()}</small>
                `;
                ul.appendChild(li);
            });
            modelsListDiv.appendChild(ul);
            this.updateStatus('Ollama模型清单获取成功');
        }
        catch (error) {
            console.error('Failed to fetch Ollama models:', error);
            const modelsListDiv = document.getElementById('ollamaModelsList');
            if (modelsListDiv) {
                modelsListDiv.innerHTML = '<div class="error">获取模型清单失败</div>';
            }
            this.updateStatus('获取Ollama模型清单失败');
        }
    }
    async startChat() {
        // 获取配置
        const config = this.getChatConfig();
        if (!config)
            return;
        // 清空聊天历史
        this.clearChatHistory();
        // 启用/禁用按钮
        this.enableUI(false);
        this.isChatRunning = true;
        try {
            // 调用后端API开始讨论
            this.updateStatus('开始讨论...');
            const response = await this.apiService.startDiscussion({
                topic: config.topic,
                model1: config.model1,
                api1: config.api1,
                model2: config.model2,
                api2: config.api2,
                rounds: config.rounds,
                time_limit: config.timeLimit,
                temperature: config.temperature
            });
            if (response.success) {
                // 显示讨论结果
                const chatHistoryElement = document.getElementById('chatHistory');
                if (chatHistoryElement) {
                    // 将讨论历史按轮次分割并显示
                    const lines = response.discussion_history.split('\n');
                    let currentSender = 'ai1';
                    let currentMessage = '';
                    for (const line of lines) {
                        const trimmedLine = line.trim();
                        if (trimmedLine.startsWith('=== 第')) {
                            // 新的一轮开始，显示之前的消息
                            if (currentMessage.trim()) {
                                await this.appendToChatHistory({
                                    sender: currentSender,
                                    content: currentMessage.trim(),
                                    timestamp: new Date()
                                });
                                currentMessage = '';
                            }
                        }
                        else if (trimmedLine.includes(':')) {
                            // 模型发言开始
                            if (currentMessage.trim()) {
                                await this.appendToChatHistory({
                                    sender: currentSender,
                                    content: currentMessage.trim(),
                                    timestamp: new Date()
                                });
                                currentMessage = '';
                            }
                            // 切换发送者
                            currentSender = currentSender === 'ai1' ? 'ai2' : 'ai1';
                            currentMessage = trimmedLine + '\n';
                        }
                        else {
                            currentMessage += line + '\n';
                        }
                    }
                    // 显示最后一条消息
                    if (currentMessage.trim()) {
                        await this.appendToChatHistory({
                            sender: currentSender,
                            content: currentMessage.trim(),
                            timestamp: new Date()
                        });
                    }
                }
                this.updateStatus('讨论已完成');
            }
            else {
                throw new Error('讨论失败');
            }
        }
        catch (error) {
            console.error('Failed to start chat:', error);
            this.showErrorMessage('讨论失败');
            this.updateStatus('讨论失败');
        }
        finally {
            this.enableUI(true);
            this.isChatRunning = false;
        }
    }
    async stopChat() {
        this.isChatRunning = false;
        this.enableUI(true);
        this.updateStatus('讨论已停止');
    }
    async startDebate() {
        // 获取辩论配置
        const config = this.getDebateConfig();
        if (!config)
            return;
        // 清空聊天历史
        this.clearChatHistory();
        // 启用/禁用按钮
        this.enableUI(false);
        this.isDebateRunning = true;
        try {
            // 调用后端API开始辩论
            this.updateStatus('开始辩论...');
            const response = await this.apiService.startDebate({
                topic: config.topic,
                model1: config.model1,
                api1: config.api1,
                model2: config.model2,
                api2: config.api2,
                rounds: config.rounds,
                time_limit: config.timeLimit,
                temperature: config.temperature
            });
            if (response.success) {
                // 显示辩论结果
                const chatHistoryElement = document.getElementById('chatHistory');
                if (chatHistoryElement) {
                    // 将辩论历史按轮次分割并显示
                    const lines = response.debate_history.split('\n');
                    let currentSender = 'ai1';
                    let currentMessage = '';
                    for (const line of lines) {
                        const trimmedLine = line.trim();
                        if (trimmedLine.startsWith('=== 第')) {
                            // 新的一轮开始，显示之前的消息
                            if (currentMessage.trim()) {
                                await this.appendToChatHistory({
                                    sender: currentSender,
                                    content: currentMessage.trim(),
                                    timestamp: new Date()
                                });
                                currentMessage = '';
                            }
                        }
                        else if (trimmedLine.includes(':')) {
                            // 模型发言开始
                            if (currentMessage.trim()) {
                                await this.appendToChatHistory({
                                    sender: currentSender,
                                    content: currentMessage.trim(),
                                    timestamp: new Date()
                                });
                                currentMessage = '';
                            }
                            // 切换发送者
                            currentSender = currentSender === 'ai1' ? 'ai2' : 'ai1';
                            currentMessage = trimmedLine + '\n';
                        }
                        else {
                            currentMessage += line + '\n';
                        }
                    }
                    // 显示最后一条消息
                    if (currentMessage.trim()) {
                        await this.appendToChatHistory({
                            sender: currentSender,
                            content: currentMessage.trim(),
                            timestamp: new Date()
                        });
                    }
                }
                this.updateStatus('辩论已完成');
            }
            else {
                throw new Error('辩论失败');
            }
        }
        catch (error) {
            console.error('Failed to start debate:', error);
            this.showErrorMessage('辩论失败');
            this.updateStatus('辩论失败');
        }
        finally {
            this.enableUI(true);
            this.isDebateRunning = false;
        }
    }
    async stopDebate() {
        this.isDebateRunning = false;
        this.enableUI(true);
        this.updateStatus('辩论已停止');
    }
    async sendHumanMessage() {
        const messageInput = document.getElementById('human-message');
        const message = messageInput.value.trim();
        if (!message)
            return;
        // 清空输入框
        messageInput.value = '';
        // 添加用户消息到聊天历史
        await this.appendToChatHistory({
            sender: 'user',
            content: message,
            timestamp: new Date()
        });
        // 获取聊天配置
        const providerSelect = document.getElementById('human-provider');
        const modelSelect = document.getElementById('human-model');
        const temperatureInput = document.getElementById('human-temperature');
        const config = {
            message: message,
            api: providerSelect.value,
            model: modelSelect.value,
            temperature: parseFloat(temperatureInput.value)
        };
        try {
            // 调用后端API获取AI响应（流式输出）
            this.updateStatus('AI回复中...');
            // 添加一个临时的AI消息容器，用于实时更新
            const aiMessageId = `ai-message-${Date.now()}`;
            await this.appendToChatHistory({
                sender: 'ai',
                content: '<span id="' + aiMessageId + '"></span>',
                timestamp: new Date()
            });
            const aiMessageElement = document.getElementById(aiMessageId);
            if (!aiMessageElement) {
                throw new Error('Failed to create AI message element');
            }
            // 使用流式请求
            await this.apiService.sendChatMessageStream(config, 
            // 收到新数据时的回调
            (chunk) => {
                aiMessageElement.textContent += chunk;
            }, 
            // 完成时的回调
            () => {
                // 将临时容器替换为最终内容
                const finalContent = aiMessageElement.textContent || '';
                aiMessageElement.outerHTML = finalContent;
                this.updateStatus('AI回复完成');
            }, 
            // 出错时的回调
            (error) => {
                aiMessageElement.textContent = `Error: ${error.message}`;
                this.showErrorMessage('AI回复失败');
                this.updateStatus('AI回复失败');
                console.error('Failed to send human message (streaming):', error);
            });
        }
        catch (error) {
            console.error('Failed to send human message:', error);
            this.showErrorMessage('AI回复失败');
            this.updateStatus('AI回复失败');
        }
    }
    getChatConfig() {
        const topicInput = document.getElementById('topic');
        const api1Select = document.getElementById('api1');
        const model1Select = document.getElementById('model1');
        const api2Select = document.getElementById('api2');
        const model2Select = document.getElementById('model2');
        const roundsInput = document.getElementById('rounds');
        const timeLimitInput = document.getElementById('timeLimit');
        const temperatureInput = document.getElementById('temperature');
        const topic = topicInput.value.trim();
        if (!topic) {
            this.showErrorMessage('请输入讨论主题');
            return null;
        }
        return {
            topic,
            model1: model1Select.value,
            api1: api1Select.value,
            model2: model2Select.value,
            api2: api2Select.value,
            rounds: parseInt(roundsInput.value),
            timeLimit: parseInt(timeLimitInput.value),
            temperature: parseFloat(temperatureInput.value)
        };
    }
    getDebateConfig() {
        const topicInput = document.getElementById('debate-topic');
        const api1Select = document.getElementById('debate-api1');
        const model1Select = document.getElementById('debate-model1');
        const api2Select = document.getElementById('debate-api2');
        const model2Select = document.getElementById('debate-model2');
        const roundsInput = document.getElementById('debate-rounds');
        const timeLimitInput = document.getElementById('debate-timeLimit');
        const temperatureInput = document.getElementById('debate-temperature');
        const topic = topicInput.value.trim();
        if (!topic) {
            this.showErrorMessage('请输入辩论主题');
            return null;
        }
        return {
            topic,
            model1: model1Select.value,
            api1: api1Select.value,
            model2: model2Select.value,
            api2: api2Select.value,
            rounds: parseInt(roundsInput.value),
            timeLimit: parseInt(timeLimitInput.value),
            temperature: parseFloat(temperatureInput.value)
        };
    }
    async appendToChatHistory(message) {
        // 添加到聊天历史数组
        this.chatHistory.push(message);
        // 创建消息元素
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender}`;
        // 创建头像元素
        const avatarElement = document.createElement('div');
        avatarElement.className = 'avatar';
        avatarElement.innerHTML = `<img src="https://via.placeholder.com/40" alt="${message.sender}">`;
        // 创建消息内容元素
        const contentElement = document.createElement('div');
        contentElement.className = 'content';
        // 创建消息头部
        const headerElement = document.createElement('div');
        headerElement.className = 'header';
        headerElement.innerHTML = `<span class="sender">${message.sender}</span><span class="time">${message.timestamp.toLocaleTimeString()}</span>`;
        // 创建消息正文
        const bodyElement = document.createElement('div');
        bodyElement.className = 'body';
        bodyElement.innerHTML = await marked.parse(message.content);
        // 组合元素
        contentElement.appendChild(headerElement);
        contentElement.appendChild(bodyElement);
        messageElement.appendChild(avatarElement);
        messageElement.appendChild(contentElement);
        // 添加到聊天历史容器
        const chatHistoryElement = document.getElementById('chatHistory');
        if (chatHistoryElement) {
            chatHistoryElement.appendChild(messageElement);
            // 滚动到底部
            chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight;
        }
    }
    clearChatHistory() {
        // 清空聊天历史数组
        this.chatHistory = [];
        // 清空聊天历史容器
        const chatHistoryElement = document.getElementById('chatHistory');
        if (chatHistoryElement) {
            chatHistoryElement.innerHTML = '';
        }
    }
    clearHumanChat() {
        this.clearChatHistory();
    }
    enableUI(enabled) {
        // 启用/禁用讨论相关按钮
        const startButton = document.getElementById('startChat');
        const stopButton = document.getElementById('stopChat');
        const saveButton = document.getElementById('saveSettings');
        if (startButton)
            startButton.disabled = !enabled;
        if (stopButton)
            stopButton.disabled = enabled;
        if (saveButton)
            saveButton.disabled = !enabled;
        // 启用/禁用辩论相关按钮
        const startDebateButton = document.getElementById('startDebate');
        const stopDebateButton = document.getElementById('stopDebate');
        if (startDebateButton)
            startDebateButton.disabled = !enabled;
        if (stopDebateButton)
            stopDebateButton.disabled = enabled;
    }
    updateStatus(message) {
        const statusElement = document.getElementById('status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
    showErrorMessage(message) {
        alert(`错误: ${message}`);
    }
    updateModelList(modelSelectId) {
        // 根据API类型更新模型列表
        const modelSelect = document.getElementById(modelSelectId);
        const apiSelect = document.getElementById(modelSelectId.replace('model', 'api'));
        const apiType = apiSelect.value;
        // 清空模型列表
        modelSelect.innerHTML = '';
        // 添加模型选项
        let models = [];
        switch (apiType) {
            case 'ollama':
                models = ['qwen3:14b', 'deepseek-r1:14b', 'llama3:8b', 'gemma:7b', 'mistral:7b'];
                break;
            case 'openai':
                models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'];
                break;
            case 'deepseek':
                models = ['deepseek-chat', 'deepseek-coder'];
                break;
            default:
                models = [];
        }
        // 添加模型选项到下拉列表
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });
    }
    async loadHistory() {
        try {
            const historyList = await this.apiService.getHistoryList();
            // 更新历史列表显示
            const historyListElement = document.getElementById('history-list');
            if (historyListElement) {
                historyListElement.innerHTML = '';
                historyList.forEach((item, index) => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <input type="checkbox" id="history-item-${index}" data-index="${index}">
                        <label for="history-item-${index}">${item.topic} (${item.start_time})</label>
                        <div class="history-actions">
                            <button onclick="app.viewHistory(${index})">查看</button>
                            <button onclick="app.deleteHistory(${index})">删除</button>
                        </div>
                    `;
                    historyListElement.appendChild(li);
                });
            }
        }
        catch (error) {
            console.error('加载历史记录失败:', error);
            this.showErrorMessage('加载历史记录失败');
        }
    }
    async viewHistory(index) {
        try {
            const history = await this.apiService.getHistoryDetail(index);
            if (history) {
                // 显示历史详情
                const historyDetailElement = document.getElementById('history-detail');
                if (historyDetailElement) {
                    historyDetailElement.innerHTML = `
                        <h3>${history.topic}</h3>
                        <p>开始时间: ${history.start_time}</p>
                        <p>结束时间: ${history.end_time}</p>
                        <p>模型1: ${history.model1} (${history.api1})</p>
                        <p>模型2: ${history.model2} (${history.api2})</p>
                        <p>轮数: ${history.rounds}</p>
                        <h4>聊天内容:</h4>
                        <div class="history-content">${await marked.parse(history.chat_content)}</div>
                    `;
                }
            }
        }
        catch (error) {
            console.error('查看历史记录失败:', error);
            this.showErrorMessage('查看历史记录失败');
        }
    }
    async deleteHistory(index) {
        if (!confirm('确定要删除这条历史记录吗？'))
            return;
        try {
            const success = await this.apiService.deleteHistory(index);
            if (success) {
                // 重新加载历史列表
                this.loadHistory();
                this.showErrorMessage('删除历史记录成功');
            }
        }
        catch (error) {
            console.error('删除历史记录失败:', error);
            this.showErrorMessage('删除历史记录失败');
        }
    }
    async deleteSelectedHistory() {
        // 获取所有选中的历史记录
        const checkboxes = document.querySelectorAll('input[type="checkbox"][data-index]:checked');
        const indices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
        if (indices.length === 0)
            return;
        if (!confirm(`确定要删除选中的 ${indices.length} 条历史记录吗？`))
            return;
        try {
            for (const index of indices) {
                await this.apiService.deleteHistory(index);
            }
            // 重新加载历史列表
            this.loadHistory();
            this.showErrorMessage('删除选中的历史记录成功');
        }
        catch (error) {
            console.error('删除选中的历史记录失败:', error);
            this.showErrorMessage('删除选中的历史记录失败');
        }
    }
    async clearAllHistory() {
        if (!confirm('确定要清空所有历史记录吗？'))
            return;
        try {
            const success = await this.apiService.clearAllHistory();
            if (success) {
                // 重新加载历史列表
                this.loadHistory();
                this.showErrorMessage('清空所有历史记录成功');
            }
        }
        catch (error) {
            console.error('清空所有历史记录失败:', error);
            this.showErrorMessage('清空所有历史记录失败');
        }
    }
    async exportHistory() {
        try {
            const historyList = await this.apiService.getHistoryList();
            // 导出为JSON文件
            const dataStr = JSON.stringify(historyList, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'chat_history.json';
            link.click();
            URL.revokeObjectURL(url);
        }
        catch (error) {
            console.error('导出历史记录失败:', error);
            this.showErrorMessage('导出历史记录失败');
        }
    }
    selectAllHistory(e) {
        const isChecked = e.target.checked;
        const checkboxes = document.querySelectorAll('input[type="checkbox"][data-index]');
        checkboxes.forEach(cb => {
            cb.checked = isChecked;
        });
    }
    exportPdf() {
        // 使用浏览器的打印功能导出PDF
        window.print();
    }
    /**
     * 处理登录表单提交
     */
    async handleLogin(e) {
        e.preventDefault();
        const usernameInput = document.getElementById('loginUsername');
        const passwordInput = document.getElementById('loginPassword');
        const errorElement = document.getElementById('loginError');
        const username = usernameInput.value;
        const password = passwordInput.value;
        if (!username || !password) {
            errorElement.textContent = '请输入用户名和密码';
            return;
        }
        try {
            // 调用登录API
            const response = await fetch('http://localhost:8000/api/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: username,
                    password: password
                })
            });
            if (response.ok) {
                const data = await response.json();
                // 保存token到localStorage
                localStorage.setItem('token', data.access_token);
                // 隐藏登录模态框
                this.hideLoginModal();
            }
            else {
                const errorData = await response.json();
                errorElement.textContent = errorData.detail || '登录失败，请检查用户名和密码';
            }
        }
        catch (error) {
            console.error('登录失败:', error);
            errorElement.textContent = '登录失败，服务器连接错误';
        }
    }
    /**
     * 隐藏登录模态框
     */
    hideLoginModal() {
        const loginModal = document.getElementById('loginModal');
        if (loginModal) {
            loginModal.style.display = 'none';
        }
    }
    /**
     * 显示注册模态框
     */
    showRegisterModal() {
        // 这里可以实现注册模态框的显示逻辑
        alert('注册功能正在开发中');
    }
}
// 初始化应用
const app = new App();
window.app = app;
