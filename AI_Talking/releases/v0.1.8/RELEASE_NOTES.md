# AI Talking 0.1.8 发布说明

发布日期: 2025-12-20

## 更新内容

- 修复了聊天功能加载历史后程序闪退的问题
- 修复了批量处理进度卡在0%的问题
- 优化了设置功能，保存设置后自动刷新模型列表
- 增强了系统稳定性

## 详细更新日志

### 聊天功能修复
- 修复了 `load_standard_chat_history` 方法中 `json` 模块导入位置不正确导致的程序闪退问题
- 确保聊天历史加载时能够正确渲染所有消息
- 优化了聊天历史加载的性能

### 批量处理功能修复
- 修复了批量处理进度计算中的整数除法问题，确保进度能够从0%正确递增到100%
- 优化了批量处理的性能
- 增强了批量处理的稳定性

### 设置功能优化
- 修复了API密钥保存逻辑，确保删除密钥时会从.env文件中移除对应配置
- 确保保存设置后所有模块的模型列表都会自动刷新
- 优化了配置更新机制，确保所有修改都能正确反映到.env文件中

### 系统稳定性增强
- 修复了多个潜在的崩溃点
- 优化了错误处理机制
- 增强了程序的鲁棒性

## 下载地址

- Windows: [AI_Talking_Setup.exe](https://gitcode.com/tonyke/AI_Talking/releases/download/v0.1.8/AI_Talking_Setup.exe)
- macOS: [AI_Talking.dmg](https://gitcode.com/tonyke/AI_Talking/releases/download/v0.1.8/AI_Talking.dmg)
- Linux: [AI_Talking.AppImage](https://gitcode.com/tonyke/AI_Talking/releases/download/v0.1.8/AI_Talking.AppImage)

## 联系方式

- 官方网站: [https://www.nonead.com](https://www.nonead.com)
- 邮箱: [service@nonead.com](mailto:service@nonead.com)
- 开源地址: [https://gitcode.com/tonyke/AI_Talking](https://gitcode.com/tonyke/AI_Talking)