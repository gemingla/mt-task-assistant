"""
API 连接诊断工具
用于检测和诊断 API 配置问题
"""

import json
import os
import sys
import requests
from datetime import datetime
from utils import get_data_path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def get_config_path():
    """获取配置文件路径"""
    return get_data_path("config.json")


def load_config():
    """加载配置文件"""
    try:
        with open(get_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ 配置文件不存在")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        return None


def test_api_connection():
    """测试 API 连接"""
    print("\n" + "="*60)
    print("API 连接诊断工具")
    print("="*60)
    
    # 1. 检查配置文件
    print("\n[步骤 1] 检查配置文件...")
    config = load_config()
    if not config:
        print("   请先在程序中配置 API")
        return False
    
    # 2. 检查配置项
    print("\n[步骤 2] 检查配置项...")
    api_url = config.get("api_url", "").strip()
    api_key = config.get("api_key", "").strip()
    model = config.get("model", "").strip()
    
    issues = []
    
    if not api_url:
        issues.append("[X] API 地址为空")
    else:
        print(f"   [OK] API 地址: {api_url}")
    
    if not api_key:
        issues.append("[X] API Key 为空")
    else:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "****"
        print(f"   [OK] API Key: {masked_key}")
    
    if not model:
        issues.append("[X] 模型名称为空")
    else:
        print(f"   [OK] 模型: {model}")
    
    if issues:
        print("\n配置问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    
    # 3. 测试网络连接
    print("\n[步骤 3] 测试网络连接...")
    try:
        # 测试基本连接
        test_url = api_url.rstrip("/")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 尝试获取模型列表
        print(f"   正在连接: {test_url}/models")
        response = requests.get(
            f"{test_url}/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   [OK] 网络连接成功")
            
            # 解析模型列表
            data = response.json()
            models = []
            if "data" in data:
                models = [m.get("id") for m in data["data"] if "id" in m]
            elif isinstance(data, list):
                models = [m.get("id") if isinstance(m, dict) else m for m in data]
            
            print(f"   [OK] 可用模型数量: {len(models)}")
            
            # 检查配置的模型是否在列表中
            if model in models:
                print(f"   [OK] 当前模型 '{model}' 可用")
            else:
                print(f"   [!] 当前模型 '{model}' 不在可用列表中")
                if models:
                    print(f"   可用模型示例: {', '.join(models[:5])}")
        else:
            print(f"   [X] 连接失败，状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("   [X] 连接超时，请检查网络或 API 地址")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   [X] 连接错误: {e}")
        return False
    except Exception as e:
        print(f"   [X] 未知错误: {e}")
        return False
    
    # 4. 测试聊天接口
    print("\n[步骤 4] 测试聊天接口...")
    try:
        test_messages = [
            {"role": "system", "content": "你是一个测试助手"},
            {"role": "user", "content": "请回复'测试成功'"}
        ]
        
        payload = {
            "model": model,
            "messages": test_messages,
            "temperature": 0.7
        }
        
        print(f"   正在发送测试请求...")
        response = requests.post(
            f"{test_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=(10, 30)
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                print(f"   [OK] 聊天接口正常")
                print(f"   AI 回复: {content[:100]}")
            else:
                print(f"   [!] 响应格式异常: {data}")
        else:
            print(f"   [X] 请求失败，状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   [X] 测试失败: {e}")
        return False
    
    # 5. 测试流式接口
    print("\n[步骤 5] 测试流式接口...")
    try:
        payload["stream"] = True
        
        print(f"   正在测试流式响应...")
        response = requests.post(
            f"{test_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=(10, 30),
            stream=True
        )
        
        if response.status_code == 200:
            chunk_count = 0
            content = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                chunk_content = delta["content"]
                                # 确保 chunk_content 不为 None
                                if chunk_content is not None:
                                    content += chunk_content
                                    chunk_count += 1
                    except json.JSONDecodeError:
                        continue
            
            print(f"   [OK] 流式接口正常")
            print(f"   接收到 {chunk_count} 个数据块")
            print(f"   AI 回复: {content[:100]}")
        else:
            print(f"   [!] 流式接口可能不支持，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"   [!] 流式接口测试失败: {e}")
    
    print("\n" + "="*60)
    print("[OK] 所有测试通过！API 配置正常")
    print("="*60)
    return True


def test_emergency_detection():
    """测试紧急情况检测"""
    print("\n" + "="*60)
    print("紧急情况检测测试")
    print("="*60)
    
    config = load_config()
    if not config:
        return False
    
    api_url = config.get("api_url", "").rstrip("/")
    api_key = config.get("api_key", "")
    model = config.get("model", "")
    
    if not api_url or not api_key or not model:
        print("❌ 请先配置 API")
        return False
    
    # 测试提示词
    test_prompt = """
请判断用户的意图，并严格按照以下JSON格式回复（不要添加任何解释）：

{
  "intent": "意图类型",
  "emergency_type": "紧急类型（如果有）",
  "urgency": "紧急程度",
  "affected_tasks": [受影响的任务编号],
  "emergency_task_name": "紧急任务名称（如果需要创建）",
  "emergency_task_duration": 预计时长分钟数（数字）,
  "emergency_task_due": "截止日期（YYYY-MM-DD格式，如果有）",
  "suggestions": "建议"
}

用户消息：我有编程大赛，时间与本来的任务相冲突
"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个专业的效率助手"},
            {"role": "user", "content": test_prompt}
        ],
        "temperature": 0.3
    }
    
    try:
        print("\n正在测试紧急情况检测...")
        response = requests.post(
            f"{api_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=(10, 30)
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                print("\nAI 原始回复:")
                print(content)
                
                # 尝试解析JSON
                try:
                    import re
                    json_str = content.strip()
                    if json_str.startswith("```"):
                        json_str = json_str.split("\n", 1)[1] if "\n" in json_str else json_str
                    if json_str.endswith("```"):
                        json_str = json_str.rsplit("\n", 1)[0] if "\n" in json_str else json_str
                    json_str = json_str.strip()
                    
                    result = json.loads(json_str)
                    print("\n解析结果:")
                    print(f"  意图: {result.get('intent')}")
                    print(f"  紧急类型: {result.get('emergency_type')}")
                    print(f"  紧急程度: {result.get('urgency')}")
                    print(f"  紧急任务名称: {result.get('emergency_task_name')}")
                    print(f"  预计时长: {result.get('emergency_task_duration')} 分钟")
                    
                    print("\n[OK] 紧急情况检测正常")
                    return True
                except json.JSONDecodeError as e:
                    print(f"\n[X] JSON 解析失败: {e}")
                    print(f"清理后的字符串: {json_str}")
                    return False
            else:
                print("[X] 响应格式异常")
                return False
        else:
            print(f"[X] 请求失败，状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行诊断
    print("\n开始诊断...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试API连接
    api_ok = test_api_connection()
    
    # 如果API正常，测试紧急情况检测
    if api_ok:
        test_emergency_detection()
    
    print("\n诊断完成！")
