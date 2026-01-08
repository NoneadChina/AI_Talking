import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.ai_service import AIServiceFactory

def test_ollama_ai_service():
    """
    测试 AI_Talking 中的 OllamaAIService 类
    """
    print("=== 测试 AI_Talking OllamaAIService ===")
    
    # 使用 AI 服务工厂创建 Ollama 服务实例
    print("\n1. 创建 Ollama 服务实例")
    try:
        ai_service = AIServiceFactory.create_ai_service(
            "ollama", 
            base_url="http://localhost:11434"
        )
        print("✅ 成功创建 Ollama 服务实例")
    except Exception as e:
        print(f"❌ 创建服务实例失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试聊天完成
    print("\n2. 测试聊天完成功能")
    messages = [
        {"role": "user", "content": "你好，AI_Talking 测试"}
    ]
    
    try:
        # 使用已知的本地模型进行测试
        test_model = "llama3.2"
        
        print(f"使用模型: {test_model}")
        response = ai_service.chat_completion(
            messages=messages,
            model=test_model,
            temperature=0.8,
            stream=False
        )
        
        print(f"✅ 聊天响应成功")
        print(f"响应内容: {response}")
        return True
    except Exception as e:
        print(f"❌ 聊天完成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ollama_ai_service()
    if success:
        print("\n=== 测试成功！OllamaAIService 修复有效 ===")
    else:
        print("\n=== 测试失败！OllamaAIService 仍有问题 ===")
