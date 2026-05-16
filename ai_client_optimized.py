"""
优化版 AI 客户端
- 连接池复用
- 配置缓存
- 智能重试
- 并发控制
- 性能监控
"""

import json
import os
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
import time
from typing import Optional, Dict, List, Callable, Tuple
from functools import lru_cache


class ConfigCache:
    """配置缓存管理器"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None
        self._last_modified = 0
        self._lock = threading.Lock()
    
    def get_config(self) -> Dict:
        """获取配置（带缓存）"""
        with self._lock:
            try:
                # 检查文件修改时间
                current_mtime = os.path.getmtime(self.config_path)
                
                # 如果文件未修改，返回缓存
                if self._config and current_mtime == self._last_modified:
                    return self._config
                
                # 重新读取配置
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                    self._last_modified = current_mtime
                
                return self._config
            except Exception as e:
                print(f"[ConfigCache] 读取配置失败: {e}")
                return self._config or {}
    
    def invalidate(self):
        """使缓存失效"""
        with self._lock:
            self._config = None
            self._last_modified = 0


class ConnectionPool:
    """HTTP 连接池管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._sessions = {}
        self._session_lock = threading.Lock()
        
        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time": 0,
            "avg_time": 0
        }
        self._stats_lock = threading.Lock()
    
    def get_session(self, api_url: str) -> requests.Session:
        """获取或创建 Session"""
        with self._session_lock:
            # 使用 API URL 的域名作为 key
            from urllib.parse import urlparse
            domain = urlparse(api_url).netloc
            
            if domain not in self._sessions:
                session = requests.Session()
                
                # 配置重试策略
                retry_strategy = Retry(
                    total=3,  # 最多重试 3 次
                    backoff_factor=0.5,  # 指数退避
                    status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
                    allowed_methods=["POST", "GET"]  # 允许重试的方法
                )
                
                adapter = HTTPAdapter(
                    max_retries=retry_strategy,
                    pool_connections=10,  # 连接池大小
                    pool_maxsize=20,  # 最大连接数
                    pool_block=False
                )
                
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                
                self._sessions[domain] = session
            
            return self._sessions[domain]
    
    def update_stats(self, elapsed_time: float, success: bool):
        """更新性能统计"""
        with self._stats_lock:
            self.stats["total_requests"] += 1
            self.stats["total_time"] += elapsed_time
            self.stats["avg_time"] = self.stats["total_time"] / self.stats["total_requests"]
            
            if success:
                self.stats["successful_requests"] += 1
            else:
                self.stats["failed_requests"] += 1
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        with self._stats_lock:
            return self.stats.copy()


class RequestQueue:
    """请求队列管理器（防止并发过载）"""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._semaphore = threading.Semaphore(max_concurrent)
        self._active_count = 0
        self._lock = threading.Lock()
    
    def acquire(self):
        """获取请求槽位"""
        self._semaphore.acquire()
        with self._lock:
            self._active_count += 1
    
    def release(self):
        """释放请求槽位"""
        with self._lock:
            self._active_count -= 1
        self._semaphore.release()
    
    def get_status(self) -> Dict:
        """获取队列状态"""
        with self._lock:
            return {
                "active_requests": self._active_count,
                "max_concurrent": self.max_concurrent,
                "available_slots": self.max_concurrent - self._active_count
            }


class OptimizedAIClient:
    """优化版 AI 客户端"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            from utils import get_data_path
            config_path = get_data_path("config.json")
        
        self.config_cache = ConfigCache(config_path)
        self.connection_pool = ConnectionPool()
        self.request_queue = RequestQueue(max_concurrent=5)
        
        # 超时配置（优化版）
        self.timeout_config = {
            "connect": 5,  # 连接超时 5 秒
            "read": 60,  # 读取超时 60 秒（从 120 秒降低）
            "stream_read": 90  # 流式读取超时 90 秒
        }
    
    def call_ai(self, messages: List[Dict], callback: Callable = None) -> Optional[str]:
        """
        调用 AI API（优化版）
        
        Args:
            messages: 消息列表
            callback: 错误回调函数
            
        Returns:
            AI 响应内容，失败返回 None
        """
        start_time = time.time()
        
        # 获取配置（带缓存）
        config = self.config_cache.get_config()
        
        api_url = config.get("api_url", "").rstrip("/")
        api_key = config.get("api_key", "")
        model = config.get("model", "")
        system_prompt = config.get("system_prompt", "你是一个专业的效率助手，请用简洁清晰的语言帮助用户管理时间。")
        
        if not api_url or not api_key:
            if callback:
                callback("请先在设置中配置 API 地址和 API Key")
            return None
        
        # 获取连接池 Session
        session = self.connection_pool.get_session(api_url)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 构建请求体
        payload_messages = [{"role": "system", "content": system_prompt}]
        payload_messages.extend(messages)
        
        payload = {
            "model": model,
            "messages": payload_messages,
            "temperature": 0.7,
            "max_tokens": 2000  # 限制输出长度，加快响应
        }
        
        # 获取请求槽位
        self.request_queue.acquire()
        
        try:
            # 发送请求（使用连接池）
            response = session.post(
                f"{api_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=(self.timeout_config["connect"], self.timeout_config["read"])
            )
            response.raise_for_status()
            data = response.json()
            
            # 解析响应
            if "choices" not in data or len(data["choices"]) == 0:
                if callback:
                    callback("API 响应为空")
                return None
            
            content = data["choices"][0]["message"].get("content", "")
            
            # 更新统计
            elapsed = time.time() - start_time
            self.connection_pool.update_stats(elapsed, success=True)
            
            return content
            
        except requests.exceptions.Timeout:
            if callback:
                callback("请求超时，请检查网络连接")
            self.connection_pool.update_stats(time.time() - start_time, success=False)
            return None
            
        except requests.exceptions.ConnectionError:
            if callback:
                callback("无法连接到 API，请检查 API 地址")
            self.connection_pool.update_stats(time.time() - start_time, success=False)
            return None
            
        except Exception as e:
            if callback:
                callback(f"请求失败: {str(e)}")
            self.connection_pool.update_stats(time.time() - start_time, success=False)
            return None
            
        finally:
            # 释放请求槽位
            self.request_queue.release()
    
    def call_ai_stream(
        self, 
        messages: List[Dict], 
        on_chunk: Callable = None, 
        on_error: Callable = None, 
        on_complete: Callable = None
    ) -> Optional[str]:
        """
        流式调用 AI API（优化版）
        
        Args:
            messages: 消息列表
            on_chunk: chunk 回调 (chunk_text, accumulated_text)
            on_error: 错误回调
            on_complete: 完成回调
            
        Returns:
            完整响应内容
        """
        start_time = time.time()
        
        # 获取配置
        config = self.config_cache.get_config()
        
        api_url = config.get("api_url", "").rstrip("/")
        api_key = config.get("api_key", "")
        model = config.get("model", "")
        system_prompt = config.get("system_prompt", "你是一个专业的效率助手，请用简洁清晰的语言帮助用户管理时间。")
        
        if not api_url or not api_key:
            if on_error:
                on_error("请先在设置中配置 API 地址和 API Key")
            return None
        
        # 获取连接池 Session
        session = self.connection_pool.get_session(api_url)
        
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
            "max_tokens": 2000,
            "stream": True
        }
        
        accumulated_content = ""
        
        # 获取请求槽位
        self.request_queue.acquire()
        
        try:
            response = session.post(
                f"{api_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=(self.timeout_config["connect"], self.timeout_config["stream_read"]),
                stream=True
            )
            response.raise_for_status()
            
            # 解析流式响应
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
                            chunk = delta.get("content")
                            
                            if chunk:
                                accumulated_content += chunk
                                if on_chunk:
                                    on_chunk(chunk, accumulated_content)
                    except json.JSONDecodeError:
                        continue
            
            # 更新统计
            elapsed = time.time() - start_time
            self.connection_pool.update_stats(elapsed, success=True)
            
            if on_complete:
                on_complete(accumulated_content)
            
            return accumulated_content
            
        except requests.exceptions.Timeout:
            if on_error:
                on_error("请求超时")
            self.connection_pool.update_stats(time.time() - start_time, success=False)
            return None
            
        except requests.exceptions.ConnectionError:
            if on_error:
                on_error("无法连接到 API")
            self.connection_pool.update_stats(time.time() - start_time, success=False)
            return None
            
        except Exception as e:
            if on_error:
                on_error(f"请求失败: {str(e)}")
            self.connection_pool.update_stats(time.time() - start_time, success=False)
            return None
            
        finally:
            # 释放请求槽位
            self.request_queue.release()
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        return {
            "connection_pool": self.connection_pool.get_stats(),
            "request_queue": self.request_queue.get_status()
        }


# 全局单例
_global_client = None
_client_lock = threading.Lock()


def get_optimized_client() -> OptimizedAIClient:
    """获取全局优化客户端实例"""
    global _global_client
    
    if _global_client is None:
        with _client_lock:
            if _global_client is None:
                _global_client = OptimizedAIClient()
    
    return _global_client


# 兼容旧接口的函数
def call_ai_optimized(messages: List[Dict], callback: Callable = None) -> Optional[str]:
    """
    优化版 AI 调用（兼容旧接口）
    
    Args:
        messages: 消息列表
        callback: 错误回调
        
    Returns:
        AI 响应内容
    """
    client = get_optimized_client()
    return client.call_ai(messages, callback)


def call_ai_stream_optimized(
    messages: List[Dict], 
    on_chunk: Callable = None, 
    on_error: Callable = None, 
    on_complete: Callable = None
) -> Optional[str]:
    """
    优化版流式 AI 调用（兼容旧接口）
    
    Args:
        messages: 消息列表
        on_chunk: chunk 回调
        on_error: 错误回调
        on_complete: 完成回调
        
    Returns:
        完整响应内容
    """
    client = get_optimized_client()
    return client.call_ai_stream(messages, on_chunk, on_error, on_complete)
