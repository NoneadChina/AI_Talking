# AI Talking 0.3.9 发布说明

发布日期: 2025-12-28

## 功能改进

### 新增功能
- 添加配置文件支持，允许用户通过YAML配置文件自定义应用行为
- 实现日志分级和旋转功能，避免日志文件过大
- 在Web后端添加健康检查端点(/health)，便于监控应用状态

### 版本更新
- 🔧 更新版本号从0.3.8到0.3.9
- 🔧 更新requirements.txt，添加PyYAML依赖
- 🔧 修改日志配置，支持配置文件驱动的日志设置

## 问题修复
- 🐛 改进了Ollama Cloud API的错误处理，将"QMetaObject.invokeMethod() call failed"错误替换为更友好的"Ollama Cloud API 认证失败：无效的 API 密钥"提示
- 🐛 增强了Ollama Cloud API的调试日志，便于排查认证问题
