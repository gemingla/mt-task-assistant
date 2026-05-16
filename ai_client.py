import json
import os
import re
import requests
from utils import get_data_path

# 获取配置文件的正确路径
def get_config_path():
    return get_data_path("config.json")


def render_latex(text):
    """
    将 LaTeX 数学公式转换为 Qt HTML 格式

    支持的转换：
    - \sqrt{x} → √x
    - \frac{a}{b} → a/b
    - ^{x} → 上标
    - _{x} → 下标
    - \angle → ∠
    - \triangle → △
    - \alpha, \beta, \gamma 等 → α, β, γ
    - \pi → π
    - \pm → ±
    - \times → ×
    - \div → ÷
    - \leq → ≤
    - \geq → ≥
    - \neq → ≠
    - \infty → ∞
    - \cdot → ·
    - \vec{x} → x→
    - \(...\) → 内容
    - \[...\] → 内容
    """
    if not text:
        return text

    result = text

    def remove_latex_delimiters(match):
        return match.group(1)

    result = re.sub(r'\\\((.+?)\\\)', remove_latex_delimiters, result, flags=re.DOTALL)
    result = re.sub(r'\\\[(.+?)\\\]', remove_latex_delimiters, result, flags=re.DOTALL)
    result = re.sub(r'\$\$(.+?)\$\$', remove_latex_delimiters, result, flags=re.DOTALL)
    result = re.sub(r'\$(.+?)\$', remove_latex_delimiters, result, flags=re.DOTALL)

    greek_map = {
        r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
        r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
        r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
        r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
        r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
        r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
        r'\Alpha': 'Α', r'\Beta': 'Β', r'\Gamma': 'Γ', r'\Delta': 'Δ',
        r'\Theta': 'Θ', r'\Lambda': 'Λ', r'\Xi': 'Ξ', r'\Pi': 'Π',
        r'\Sigma': 'Σ', r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
    }

    for latex, greek in greek_map.items():
        result = result.replace(latex, greek)

    result = result.replace(r'\sqrt', '√')
    result = result.replace(r'\angle', '∠')
    result = result.replace(r'\triangle', '△')
    result = result.replace(r'\pm', '±')
    result = result.replace(r'\times', '×')
    result = result.replace(r'\div', '÷')
    result = result.replace(r'\cdot', '·')
    result = result.replace(r'\leq', '≤')
    result = result.replace(r'\geq', '≥')
    result = result.replace(r'\neq', '≠')
    result = result.replace(r'\infty', '∞')
    result = result.replace(r'\perp', '⊥')
    result = result.replace(r'\parallel', '∥')
    result = result.replace(r'\subset', '⊂')
    result = result.replace(r'\subseteq', '⊆')
    result = result.replace(r'\cup', '∪')
    result = result.replace(r'\cap', '∩')
    result = result.replace(r'\sum', 'Σ')
    result = result.replace(r'\product', 'Π')
    result = result.replace(r'\partial', '∂')
    result = result.replace(r'\nabla', '∇')
    result = result.replace(r'\forall', '∀')
    result = result.replace(r'\exists', '∃')
    result = result.replace(r'\approx', '≈')
    result = result.replace(r'\equiv', '≡')
    result = result.replace(r'\sim', '∼')
    result = result.replace(r'\propto', '∝')
    result = result.replace(r'\circ', '∘')
    result = result.replace(r'\bullet', '•')
    result = result.replace(r'\rightarrow', '→')
    result = result.replace(r'\leftarrow', '←')
    result = result.replace(r'\Rightarrow', '⇒')
    result = result.replace(r'\Leftarrow', '⇐')
    result = result.replace(r'\leftrightarrow', '↔')
    result = result.replace(r'\Leftrightarrow', '⇔')
    result = result.replace(r'\therefore', '∴')
    result = result.replace(r'\because', '∵')
    result = result.replace(r'\degree', '°')
    result = result.replace(r'\prime', '′')
    result = result.replace(r'\int', '∫')
    result = result.replace(r'\oint', '∮')
    result = result.replace(r'\lim', 'lim')
    result = result.replace(r'\log', 'log')
    result = result.replace(r'\ln', 'ln')
    result = result.replace(r'\sin', 'sin')
    result = result.replace(r'\cos', 'cos')
    result = result.replace(r'\tan', 'tan')
    result = result.replace(r'\cot', 'cot')
    result = result.replace(r'\sec', 'sec')
    result = result.replace(r'\csc', 'csc')
    result = result.replace(r'\arcsin', 'arcsin')
    result = result.replace(r'\arccos', 'arccos')
    result = result.replace(r'\arctan', 'arctan')
    result = result.replace(r'\sinh', 'sinh')
    result = result.replace(r'\cosh', 'cosh')
    result = result.replace(r'\tanh', 'tanh')
    result = result.replace(r'\exp', 'exp')
    result = result.replace(r'\min', 'min')
    result = result.replace(r'\max', 'max')
    result = result.replace(r'\gcd', 'gcd')
    result = result.replace(r'\lcm', 'lcm')
    result = result.replace(r'\det', 'det')
    result = result.replace(r'\dim', 'dim')
    result = result.replace(r'\ker', 'ker')
    result = result.replace(r'\hom', 'hom')
    result = result.replace(r'\arg', 'arg')
    result = result.replace(r'\deg', 'deg')
    result = result.replace(r'\inf', 'inf')
    result = result.replace(r'\sup', 'sup')

    result = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', result)

    result = re.sub(r'\\sqrt\{([^{}]+)\}', r'√(\1)', result)

    result = re.sub(r'\^\{([^{}]+)\}', r'<sup>\1</sup>', result)
    result = re.sub(r'\^(\d+)', r'<sup>\1</sup>', result)
    result = re.sub(r'\^([a-zA-Z])', r'<sup>\1</sup>', result)

    result = re.sub(r'_\{([^{}]+)\}', r'<sub>\1</sub>', result)
    result = re.sub(r'_(\d+)', r'<sub>\1</sub>', result)
    result = re.sub(r'_([a-zA-Z])', r'<sub>\1</sub>', result)

    result = re.sub(r'\\left\s*|\\right\s*', '', result)

    result = re.sub(r'\\vec\{([^{}]+)\}', r'\1→', result)
    result = re.sub(r'\\bar\{([^{}]+)\}', r'\1̄', result)
    result = re.sub(r'\\hat\{([^{}]+)\}', r'\1̂', result)
    result = re.sub(r'\\tilde\{([^{}]+)\}', r'\1̃', result)
    result = re.sub(r'\\dot\{([^{}]+)\}', r'\1̇', result)
    result = re.sub(r'\\ddot\{([^{}]+)\}', r'\1̈', result)

    result = re.sub(r'\\begin\{[^}]+\}', '', result)
    result = re.sub(r'\\end\{[^}]+\}', '', result)
    result = re.sub(r'\\item\s*', '• ', result)
    result = re.sub(r'\\text\{([^{}]+)\}', r'\1', result)
    result = re.sub(r'\\textbf\{([^{}]+)\}', r'<b>\1</b>', result)
    result = re.sub(r'\\textit\{([^{}]+)\}', r'<i>\1</i>', result)
    result = re.sub(r'\\underline\{([^{}]+)\}', r'<u>\1</u>', result)

    result = re.sub(r'\{([^{}]*)\}', r'\1', result)

    result = result.replace(r'\,', ' ')
    result = result.replace(r'\;', ' ')
    result = result.replace(r'\!', '')
    result = result.replace(r'\:', ' ')
    result = result.replace(r'~', ' ')
    result = result.replace(r'\\ ', ' ')

    result = result.replace(r'\\n', '<br>')
    result = result.replace('\n', '<br>')

    return result


def get_models(api_url: str, api_key: str, callback=None) -> list:
    """
    获取可用模型列表

    Args:
        api_url: API 地址
        api_key: API Key
        callback: 可选的错误回调函数

    Returns:
        list: 模型名称列表，失败时返回 None
    """
    if not api_url or not api_key:
        if callback:
            callback("请先输入 API 地址和 API Key")
        return None

    api_url = api_url.rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(
            f"{api_url}/models",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        models = []
        if "data" in data:
            for model in data["data"]:
                if "id" in model:
                    models.append(model["id"])
        elif isinstance(data, list):
            for model in data:
                if isinstance(model, dict) and "id" in model:
                    models.append(model["id"])
                elif isinstance(model, str):
                    models.append(model)

        models.sort()
        return models
    except requests.exceptions.Timeout:
        if callback:
            callback("请求超时，请检查网络连接")
        return None
    except requests.exceptions.ConnectionError:
        if callback:
            callback("无法连接到 API，请检查 API 地址是否正确")
        return None
    except json.JSONDecodeError:
        if callback:
            callback("API 响应格式错误")
        return None
    except Exception as e:
        if callback:
            callback(f"获取模型列表失败: {str(e)}")
        return None


def call_ai(messages: list, callback=None) -> str:
    """
    从 config.json 读取配置并调用 AI API

    Args:
        messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
        callback: 可选的错误回调函数，接收错误消息字符串

    Returns:
        str: AI 响应的 content 字符串，失败时返回 None
    """
    try:
        with open(get_config_path(), "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        if callback:
            callback("配置文件不存在，请先在设置中配置 API")
        return None
    except json.JSONDecodeError:
        if callback:
            callback("配置文件格式错误")
        return None

    api_url = config.get("api_url", "").rstrip("/")
    api_key = config.get("api_key", "")
    model = config.get("model", "")
    system_prompt = config.get("system_prompt", "你是一个专业的效率助手，请用简洁清晰的语言帮助用户管理时间。")

    if not api_url or not api_key:
        if callback:
            callback("请先在设置中配置 API 地址和 API Key")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload_messages = [{"role": "system", "content": system_prompt}]
    payload_messages.extend(messages)

    payload = {
        "model": model,
        "messages": payload_messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            f"{api_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=(10, 120)
        )
        response.raise_for_status()
        data = response.json()

        if "choices" not in data or len(data["choices"]) == 0:
            if callback:
                callback("API 响应为空 choices")
            return None

        choice = data["choices"][0]
        if "message" not in choice:
            if callback:
                callback("API 响应缺少 message 字段")
            return None

        content = choice["message"].get("content", "")
        if not content:
            if callback:
                callback("API 返回内容为空")
            return None

        return content
    except requests.exceptions.Timeout:
        if callback:
            callback("请求超时（网络慢或服务器响应慢），请重试")
        return None
    except requests.exceptions.ConnectionError:
        if callback:
            callback("无法连接到 API，请检查 API 地址是否正确")
        return None
    except json.JSONDecodeError:
        if callback:
            callback(f"API 响应格式错误: {response.text[:200]}")
        return None
    except KeyError as e:
        if callback:
            callback(f"API 响应缺少必要字段: {str(e)}")
        return None
    except Exception as e:
        if callback:
            callback(f"请求失败: {str(e)}")
        return None


class StreamAIResponse:
    def __init__(self):
        self.content = ""

    def on_chunk(self, chunk_text):
        # 确保 chunk_text 不为 None
        if chunk_text is not None:
            self.content += chunk_text

    def get_content(self):
        return self.content


def call_ai_stream(messages: list, on_chunk=None, on_error=None, on_complete=None) -> StreamAIResponse:
    """
    流式调用 AI API，使用 SSE

    Args:
        messages: 消息列表
        on_chunk: 每个chunk返回时的回调，接收 (chunk_text, accumulated_text)
        on_error: 错误回调
        on_complete: 完成时的回调，接收最终内容

    Returns:
        StreamAIResponse: 流式响应对象
    """
    try:
        with open(get_config_path(), "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        if on_error:
            on_error("配置文件不存在，请先在设置中配置 API")
        return None
    except json.JSONDecodeError:
        if on_error:
            on_error("配置文件格式错误")
        return None

    api_url = config.get("api_url", "").rstrip("/")
    api_key = config.get("api_key", "")
    model = config.get("model", "")
    system_prompt = config.get("system_prompt", "你是一个专业的效率助手，请用简洁清晰的语言帮助用户管理时间。")

    if not api_url or not api_key:
        if on_error:
            on_error("请先在设置中配置 API 地址和 API Key")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload_messages = [{"role": "system", "content": system_prompt}]
    payload_messages.extend(messages)

    payload = {
        "model": model,
        "messages": payload_messages,
        "temperature": 0.7,
        "stream": True
    }

    response_obj = StreamAIResponse()

    try:
        response = requests.post(
            f"{api_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=(10, 120),
            stream=True
        )
        response.raise_for_status()

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
                            chunk = delta["content"]
                            # 确保 chunk 不为 None
                            if chunk is not None:
                                response_obj.on_chunk(chunk)
                                if on_chunk:
                                    on_chunk(chunk, response_obj.get_content())
                except json.JSONDecodeError:
                    continue

        if on_complete:
            on_complete(response_obj.get_content())

        return response_obj

    except requests.exceptions.Timeout:
        if on_error:
            on_error("请求超时（网络慢或服务器响应慢），请重试")
        return None
    except requests.exceptions.ConnectionError:
        if on_error:
            on_error("无法连接到 API，请检查 API 地址是否正确")
        return None
    except Exception as e:
        if on_error:
            # 提供更详细的错误信息
            error_type = type(e).__name__
            error_msg = str(e)
            
            # 检查是否是字符串拼接错误
            if "can only concatenate str" in error_msg:
                on_error(f"代码错误：字符串拼接失败。详细信息：{error_msg}")
            # 检查是否是JSON解析错误
            elif "Expecting value" in error_msg or "JSON" in error_type:
                on_error(f"API返回格式错误。详细信息：{error_msg}")
            # 检查是否是属性错误
            elif "has no attribute" in error_msg or "NoneType" in error_msg:
                on_error(f"代码错误：空值访问。详细信息：{error_msg}")
            # 其他错误
            else:
                on_error(f"请求失败 [{error_type}]: {error_msg}")
            
            # 打印完整堆栈到控制台
            import traceback
            print(f"\n[ERROR] AI请求失败详情:")
            print(f"  错误类型: {error_type}")
            print(f"  错误信息: {error_msg}")
            print(f"  API URL: {api_url}")
            print(f"  Model: {model}")
            print(f"  完整堆栈:")
            traceback.print_exc()
        return None


class AIClient:
    def __init__(self, config):
        self.api_url = config.get("api_url", "").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "")
        self.system_prompt = config.get("system_prompt", "")

    def chat(self, messages, system_prompt=None):
        if not self.api_url or not self.api_key:
            return None, "请先在设置中配置 API 地址和 API Key"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        elif self.system_prompt:
            payload_messages.append({"role": "system", "content": self.system_prompt})
        payload_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": 0.7
        }

        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=(10, 120)
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content, None
        except requests.exceptions.Timeout:
            return None, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return None, "无法连接到 API，请检查 API 地址是否正确"
        except Exception as e:
            return None, f"请求失败: {str(e)}"
