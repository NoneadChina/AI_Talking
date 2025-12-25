import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time

# 设置端口
PORT = 8001

# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 切换到public目录，确保能访问到正确的静态文件
public_dir = os.path.join(script_dir, 'public')
os.chdir(public_dir)

# 启动服务器的函数
def start_server():
    # 创建HTTP服务器
    with http.server.HTTPServer(('', PORT), http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"服务器已启动在 http://localhost:{PORT}")
        print("按 Ctrl+C 停止服务器")
        try:
            # 运行服务器直到被中断
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n正在关闭服务器...")
            httpd.server_close()
            print("服务器已关闭")

# 打开浏览器的函数
def open_browser():
    # 等待服务器启动
    time.sleep(1)
    print(f"正在打开浏览器...")
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    # 检查是否需要构建应用
    if not os.path.exists('js/main.js'):
        print("注意: 应用可能尚未构建。请确保已运行 'npm install' 和 'npm run build'")
    
    # 在新线程中启动服务器
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # 在主线程中打开浏览器
    open_browser()
    
    # 保持主线程运行，直到用户按Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在退出...")
        sys.exit(0)