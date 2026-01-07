1、机头上升下降速度是否能加快  匀速的寄存器位置
2、穿键杆中间速度是否能加快 匀速的寄存器位置
3、收带到收紧之前一直在转，要问清楚这个转在干吗!



# AI Talking 自动更新功能说明

## 功能概述

AI Talking 应用现已集成自动更新功能，支持在应用启动时自动检查更新，并在发现新版本时提示用户下载和安装。

## 核心功能

1. **自动检查更新**：应用启动后5秒自动检查更新
2. **新版本提示**：发现新版本时显示提示框
3. **后台下载**：更新包在后台下载，不影响应用使用
4. **关闭后安装**：应用关闭后自动安装更新
5. **版本历史记录**：详细记录版本信息，便于调试和数据分析
6. **自动化版本管理**：提供脚本用于自动更新版本号和构建发布

## 更新服务器配置

应用默认使用以下更新服务器配置：

```
更新服务器URL: https://gitcode.com/tonyke/AI_Talking/releases
Provider类型: generic
支持平台: Windows, macOS, Linux
```

## 版本管理流程

### 1. 手动检查更新

应用启动时会自动检查更新，您也可以在未来的版本中通过设置界面手动触发检查。

### 2. 自动更新流程

1. 应用启动，延迟5秒后开始检查更新
2. 发送请求到更新服务器获取最新版本信息
3. 比较版本号，如果发现新版本则显示提示
4. 用户确认后，后台下载更新包
5. 下载完成后，提示用户应用关闭后自动安装
6. 用户关闭应用，自动启动安装程序
7. 安装完成后，下次启动将使用新版本

### 3. 版本更新脚本

提供了 `scripts/update_version.py` 脚本用于自动化版本更新和发布流程：

#### 使用方法

```bash
# 更新补丁版本 (1.0.0 -> 1.0.1)
python scripts/update_version.py patch

# 更新次要版本 (1.0.0 -> 1.1.0)
python scripts/update_version.py minor

# 更新主要版本 (1.0.0 -> 2.0.0)
python scripts/update_version.py major

# 更新版本并构建应用
python scripts/update_version.py minor --build

# 更新版本并推送到远程仓库
python scripts/update_version.py minor --push

# 更新版本、构建应用并推送到远程仓库
python scripts/update_version.py minor --build --push
```

#### 脚本功能

- 自动更新 `src/__init__.py` 中的版本号
- 自动更新 `about_tab.py` 中的版本显示
- 自动更新安装程序配置文件中的版本号
- 生成发布说明和 `latest.json` 文件
- 支持构建应用程序
- 支持创建Git提交和标签
- 支持推送更改到远程仓库

## 版本历史记录

版本历史记录存储在 `logs/version.log` 文件中，包含以下信息：

- 启动时间
- 应用版本
- 平台信息
- 系统环境
- 打包状态

## 开发说明

### 更新服务模块结构

- `UpdateService`：核心更新服务类，负责检查更新、下载更新和安装更新
- `UpdateNotificationWidget`：更新通知组件，用于在窗口标题栏右侧显示更新提示
- `UpdateManager`：更新管理器，协调更新服务和UI组件

### 信号机制

使用PyQt5的信号机制实现跨线程通信，确保UI更新的线程安全：

- `update_available`：发现新版本信号
- `update_downloaded`：更新下载完成信号
- `update_progress`：下载进度信号
- `update_error`：更新错误信号

### 配置文件

- `latest.json`：存储最新版本信息，用于更新检查
- `scripts/update_version.py`：版本更新脚本

## 故障排除

### 自动更新失败

1. 检查网络连接是否正常
2. 检查更新服务器是否可访问
3. 查看应用日志文件获取详细错误信息
4. 手动下载更新包进行安装

### 版本更新脚本失败

1. 确保Git已正确配置
2. 确保有足够的权限修改文件
3. 确保PyInstaller已正确安装
4. 查看控制台输出获取详细错误信息

## 未来规划

1. 支持更多平台（macOS、Linux）
2. 实现增量更新
3. 支持更新日志查看
4. 实现手动检查更新功能
5. 支持更新预览功能

## 联系方式

如有任何问题或建议，请通过以下方式联系：

- GitCode仓库：https://gitcode.com/tonyke/AI_Talking
- 仓库Issues：https://gitcode.com/tonyke/AI_Talking/issues
