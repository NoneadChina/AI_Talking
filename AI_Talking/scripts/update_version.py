#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本更新脚本
用于自动更新版本号、构建和发布
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

def get_current_version() -> str:
    """
    从src/__init__.py获取当前版本号
    """
    try:
        with open('src/__init__.py', 'r', encoding='utf-8') as f:
            content = f.read()
            version_line = [line for line in content.split('\n') if '__version__' in line][0]
            version = version_line.split('=')[1].strip().strip('"')
            return version
    except Exception as e:
        print(f"获取当前版本号失败: {e}")
        sys.exit(1)

def update_version_file(new_version: str) -> None:
    """
    更新src/__init__.py中的版本号
    """
    try:
        with open('src/__init__.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = []
        for line in content.split('\n'):
            if '__version__' in line:
                new_content.append(f'__version__ = "{new_version}"')
            else:
                new_content.append(line)
        
        with open('src/__init__.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_content))
        
        print(f"已更新版本号到: {new_version}")
    except Exception as e:
        print(f"更新版本号失败: {e}")
        sys.exit(1)

def update_about_tab(new_version: str) -> None:
    """
    更新about_tab.py中的版本显示
    """
    try:
        with open('src/ui/about_tab.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式替换版本号，支持任何当前版本
        import re
        new_content = re.sub(r'version_label = QLabel\("版本\s+[\d.]+"\)', f'version_label = QLabel("版本 {new_version}")', content)
        
        with open('src/ui/about_tab.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"已更新about_tab.py中的版本显示到: {new_version}")
    except Exception as e:
        print(f"更新about_tab.py失败: {e}")
        sys.exit(1)

def update_installer_config(new_version: str) -> None:
    """
    更新安装程序配置文件中的版本号
    """
    try:
        # 更新Inno Setup配置
        if os.path.exists('AI_Talking_Setup.iss'):
            with open('AI_Talking_Setup.iss', 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace(
                'AppVersion=1.0.1',
                f'AppVersion={new_version}'
            )
            
            with open('AI_Talking_Setup.iss', 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"已更新AI_Talking_Setup.iss中的版本号到: {new_version}")
    except Exception as e:
        print(f"更新安装程序配置失败: {e}")
        sys.exit(1)

def generate_release_notes(new_version: str) -> str:
    """
    生成发布说明
    """
    release_notes = f"""
AI Talking {new_version} 发布说明

发布日期: {datetime.now().strftime('%Y-%m-%d')}

更新内容:
- 修复了已知问题
- 优化了性能
- 增强了稳定性

详细更新日志请访问官方网站。
"""
    return release_notes.strip()

def create_release_package(new_version: str) -> None:
    """
    创建发布包
    """
    try:
        # 创建发布目录
        release_dir = Path(f'releases/v{new_version}')
        release_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成发布说明
        release_notes = generate_release_notes(new_version)
        with open(release_dir / 'RELEASE_NOTES.md', 'w', encoding='utf-8') as f:
            f.write(release_notes)
        
        # 生成latest.json
        latest_json = {
            "version": new_version,
            "releaseDate": datetime.now().strftime('%Y-%m-%d'),
            "releaseNotes": release_notes,
            "win32": {
                "url": f"https://gitcode.com/tonyke/AI_Talking/releases/download/v{new_version}/AI_Talking_Setup.exe",
            "sha256": "",
            "size": 0
        },
        "darwin": {
            "url": f"https://gitcode.com/tonyke/AI_Talking/releases/download/v{new_version}/AI_Talking.dmg",
            "sha256": "",
            "size": 0
        },
        "linux": {
            "url": f"https://gitcode.com/tonyke/AI_Talking/releases/download/v{new_version}/AI_Talking.AppImage",
                "sha256": "",
                "size": 0
            }
        }
        
        with open(release_dir / 'latest.json', 'w', encoding='utf-8') as f:
            json.dump(latest_json, f, indent=2, ensure_ascii=False)
        
        # 复制到根目录latest.json
        with open('latest.json', 'w', encoding='utf-8') as f:
            json.dump(latest_json, f, indent=2, ensure_ascii=False)
        
        print(f"已生成发布包配置文件到: {release_dir}")
    except Exception as e:
        print(f"创建发布包失败: {e}")
        sys.exit(1)

def build_application() -> None:
    """
    构建应用程序
    """
    try:
        print("开始构建应用程序...")
        # 运行PyInstaller构建
        result = subprocess.run(['pyinstaller', 'AI Talking.spec'], check=True, capture_output=True, text=True)
        print(result.stdout)
        print("应用程序构建成功！")
    except subprocess.CalledProcessError as e:
        print(f"构建应用程序失败: {e}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

def commit_and_tag(new_version: str) -> None:
    """
    创建Git提交和标签
    """
    try:
        print("开始Git提交和标签...")
        
        # 添加更改
        subprocess.run(['git', 'add', '.'], check=True)
        
        # 创建提交
        commit_msg = f"Bump version to {new_version}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # 创建标签
        tag_name = f"v{new_version}"
        subprocess.run(['git', 'tag', tag_name], check=True)
        
        print(f"已创建Git提交和标签: {tag_name}")
    except subprocess.CalledProcessError as e:
        print(f"Git操作失败: {e}")
        sys.exit(1)

def push_to_remote() -> None:
    """
    推送更改到远程仓库
    """
    try:
        print("开始推送更改到远程仓库...")
        
        # 推送提交
        subprocess.run(['git', 'push'], check=True)
        
        # 推送标签
        subprocess.run(['git', 'push', '--tags'], check=True)
        
        print("已推送更改到远程仓库")
    except subprocess.CalledProcessError as e:
        print(f"推送远程仓库失败: {e}")
        sys.exit(1)

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='AI Talking版本更新脚本')
    parser.add_argument('version_type', choices=['patch', 'minor', 'major'], help='版本更新类型')
    parser.add_argument('--push', action='store_true', help='推送到远程仓库')
    parser.add_argument('--build', action='store_true', help='构建应用程序')
    args = parser.parse_args()
    
    # 获取当前版本
    current_version = get_current_version()
    print(f"当前版本: {current_version}")
    
    # 解析当前版本
    major, minor, patch = map(int, current_version.split('.'))
    
    # 根据更新类型计算新版本
    if args.version_type == 'patch':
        patch += 1
    elif args.version_type == 'minor':
        minor += 1
        patch = 0
    elif args.version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    
    new_version = f"{major}.{minor}.{patch}"
    print(f"新版本: {new_version}")
    
    # 更新版本号
    update_version_file(new_version)
    update_about_tab(new_version)
    update_installer_config(new_version)
    
    # 生成发布包配置
    create_release_package(new_version)
    
    # 构建应用程序
    if args.build:
        build_application()
    
    # 创建Git提交和标签
    commit_and_tag(new_version)
    
    # 推送到远程仓库
    if args.push:
        push_to_remote()
    
    print("版本更新完成！")

if __name__ == "__main__":
    main()
