# AI Talking 安装说明

## 安装方法

1. **使用批处理安装脚本**
   - 运行 `install_ai_talking.bat` 文件
   - 按照菜单提示选择操作
   - 推荐选择「1」安装应用，然后选择「2」创建桌面快捷方式

2. **手动安装（高级用户）**
   - 将 `dist` 目录中的所有文件复制到您想要的安装目录
   - 可以手动创建快捷方式指向 `AI_Talking.exe`

## 系统要求

- Windows 10 或 Windows 11
- 需要安装 .NET Framework 4.7.2 或更高版本
- 至少 2GB RAM 内存
- 至少 100MB 可用磁盘空间

## 注意事项

- 首次运行会自动生成 `config.yaml` 配置文件，您可以通过应用界面的设置标签页或直接编辑该文件来配置 API 密钥和其他参数
- 如果在安装过程中遇到权限问题，请以管理员身份运行安装脚本
- 应用程序默认安装在用户目录的 `AI_Talking` 文件夹中

## 卸载方法

1. 删除安装目录：`%USERPROFILE%\AI_Talking`
2. 删除开始菜单快捷方式：`%APPDATA%\Microsoft\Windows\Start Menu\Programs\AI Talking`
3. 删除桌面快捷方式：右键删除 "AI Talking" 快捷方式

## 支持

如有任何问题，请访问项目 GitHub 页面：
https://github.com/tonyke/AI_Talking/issues
