# -*- coding: utf-8 -*-
"""
同时启动前端和后端服务的脚本
"""
import os
import subprocess
import sys
import time
import threading
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_backend():
    """启动后端服务"""
    logger.info("正在启动后端服务...")
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    os.chdir(backend_dir)
    subprocess.run([sys.executable, "main.py"])

def start_frontend():
    """启动前端服务"""
    logger.info("正在启动前端服务...")
    # 直接运行start_server.py脚本，该脚本已经包含了前端服务的启动逻辑
    os.chdir(os.path.dirname(__file__))
    subprocess.run([sys.executable, "start_server.py"])

def main():
    """主函数"""
    logger.info("=== AI Talking Web 启动脚本 ===")
    logger.info("正在启动前后端服务...")
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"当前工作目录: {current_dir}")
    
    # 创建后端线程
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    
    # 创建前端线程
    frontend_thread = threading.Thread(target=start_frontend)
    frontend_thread.daemon = True
    
    # 启动线程
    backend_thread.start()
    time.sleep(2)  # 等待后端服务启动
    frontend_thread.start()
    
    # 保持主进程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n正在停止服务...")
        sys.exit(0)

if __name__ == "__main__":
    main()