import requests
import json

def test_ollama_chat_with_options():
    """
    测试包含 options 字段的 Ollama 聊天 API 请求
    """
    url = "http://localhost:11434/api/chat"
    headers = {
        "Content-Type": "application/json"
    }
    
    # 测试用例1: 直接传递 temperature（不使用 options）
    print("=== 测试用例1: 直接传递 temperature ===")
    data1 = {
        "model": "llama3.2",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": False,
        "temperature": 0.8
    }
    
    try:
        response = requests.post(url, headers=headers, json=data1, timeout=60)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
    
    # 测试用例2: 使用 options 传递 temperature
    print("\n=== 测试用例2: 使用 options 传递 temperature ===")
    data2 = {
        "model": "llama3.2",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": False,
        "options": {"temperature": 0.8}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data2, timeout=60)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
    
    # 测试用例3: 同时传递直接参数和 options
    print("\n=== 测试用例3: 同时传递直接参数和 options ===")
    data3 = {
        "model": "llama3.2",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": False,
        "temperature": 0.8,
        "options": {"temperature": 0.8}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data3, timeout=60)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    test_ollama_chat_with_options()
