@echo off
setlocal enabledelayedexpansion

REM AI Talking 安装脚本
color 0A
echo.  _______ _    _  ______ _______    _______ ______  _______ _______ _______
echo. |_____| |    | |_____/ |______      |_____| |     \ |______ |       |______
echo. |     | |____| |    \_ |______      |     | |_____/ ______| |_____  ______|
echo. 

set "INSTALL_DIR=%USERPROFILE%\AI_Talking"
set "SRC_DIR=%~dp0\dist"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\AI Talking"

:DISPLAY_MENU
echo.==========================================================================
echo.                  AI Talking 安装程序 v0.3.9
 echo.==========================================================================
echo.  [1] 安装 AI Talking
echo.  [2] 创建桌面快捷方式
echo.  [3] 创建开始菜单快捷方式
echo.  [4] 运行 AI Talking
echo.  [5] 退出
echo.==========================================================================
echo.
set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto CREATE_DESKTOP_SHORTCUT
if "%choice%"=="3" goto CREATE_START_MENU_SHORTCUT
if "%choice%"=="4" goto RUN_APP
if "%choice%"=="5" exit /b 0

echo 无效的选项！
pause
goto DISPLAY_MENU

:INSTALL
echo.正在安装 AI Talking...

REM 创建安装目录
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\resources" mkdir "%INSTALL_DIR%\resources"

REM 复制文件
echo.复制程序文件...
if exist "%SRC_DIR%\AI_Talking.exe" (
    copy /Y "%SRC_DIR%\AI_Talking.exe" "%INSTALL_DIR%"
) else (
    echo 错误：找不到 AI_Talking.exe 文件！
    pause
    goto DISPLAY_MENU
)

REM 复制资源文件
if exist "%SRC_DIR%\resources\*.*" (
    xcopy /Y "%SRC_DIR%\resources\*.*" "%INSTALL_DIR%\resources"
)

REM 复制环境配置文件
if exist "%SRC_DIR%\.env" (
    copy /Y "%SRC_DIR%\.env" "%INSTALL_DIR%"
)

echo.安装完成！
pause
goto DISPLAY_MENU

:CREATE_DESKTOP_SHORTCUT
echo.创建桌面快捷方式...
set "DESKTOP_SHORTCUT=%USERPROFILE%\Desktop\AI Talking.lnk"

REM 使用 PowerShell 创建快捷方式
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\AI_Talking.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\resources\icon.ico'; $Shortcut.Save()"

echo.桌面快捷方式已创建！
pause
goto DISPLAY_MENU

:CREATE_START_MENU_SHORTCUT
echo.创建开始菜单快捷方式...

REM 创建开始菜单目录
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%"

set "START_MENU_SHORTCUT=%START_MENU_DIR%\AI Talking.lnk"

REM 使用 PowerShell 创建快捷方式
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\AI_Talking.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\resources\icon.ico'; $Shortcut.Save()"

echo.开始菜单快捷方式已创建！
pause
goto DISPLAY_MENU

:RUN_APP
echo.启动 AI Talking...
if exist "%INSTALL_DIR%\AI_Talking.exe" (
    cd "%INSTALL_DIR%"
    start "" "%INSTALL_DIR%\AI_Talking.exe"
    exit /b 0
) else (
    echo 错误：找不到安装的程序！请先安装应用。
    pause
    goto DISPLAY_MENU
)
