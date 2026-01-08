import requests
import json

def test_ollama_chat():
    """
    测试Ollama聊天API是否正常工作
    """
    # 设置请求参数
    url = "http://localhost:11434/api/chat"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3.2",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": False
    }
    
    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text}")
        
        # 尝试解析JSON响应
        try:
            json_response = response.json()
            print(f"JSON解析结果: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)}")
            
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        return None

if __name__ == "__main__":
    test_ollama_chat()
