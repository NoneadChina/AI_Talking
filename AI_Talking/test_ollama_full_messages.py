import requests
import json

def test_ollama_chat_with_full_messages():
    """
    测试包含完整消息历史的 Ollama 聊天 API 请求
    """
    url = "http://localhost:11434/api/chat"
    headers = {
        "Content-Type": "application/json"
    }
    
    # 测试用例: 模拟完整的对话历史
    print("=== 测试用例: 完整对话历史 ===")
    
    # 模拟 AI_Talking 中可能构建的消息历史
    messages = [
        {"role": "system", "content": "你是一个乐于助人的AI助手。"},
        {"role": "user", "content": "你好，我叫小明。"},
        {"role": "assistant", "content": "你好，小明！很高兴认识你。"},
        {"role": "user", "content": "今天天气怎么样？"}
    ]
    
    data = {
        "model": "llama3.2",
        "messages": messages,
        "stream": False,
        "temperature": 0.8
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 解析响应
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"\n响应消息: {json_response.get('message', {}).get('content', '')}")
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
    
    # 测试用例: 空消息内容
    print("\n=== 测试用例: 空消息内容 ===")
    empty_messages = [
        {"role": "user", "content": ""}
    ]
    
    data_empty = {
        "model": "llama3.2",
        "messages": empty_messages,
        "stream": False,
        "temperature": 0.8
    }
    
    try:
        response = requests.post(url, headers=headers, json=data_empty, timeout=60)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    test_ollama_chat_with_full_messages()
