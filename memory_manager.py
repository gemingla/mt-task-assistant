"""
AI记忆管理模块
支持短期记忆和长期记忆，具备智能记忆更新和检索功能
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import re

# 导入智能记忆过滤器
from smart_memory_filter import SmartMemoryFilter


class Memory:
    """记忆项数据结构"""
    
    def __init__(self, content: str, memory_type: str = "short_term", 
                 importance: float = 0.5, tags: List[str] = None,
                 metadata: Dict[str, Any] = None):
        self.id = self._generate_id(content)
        self.content = content
        self.memory_type = memory_type  # short_term 或 long_term
        self.importance = importance  # 0.0 到 1.0
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.embedding = None  # 用于语义检索的向量（未来扩展）
    
    def _generate_id(self, content: str) -> str:
        """生成唯一ID"""
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return hash_obj.hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """从字典创建记忆对象"""
        memory = cls(
            content=data["content"],
            memory_type=data.get("memory_type", "short_term"),
            importance=data.get("importance", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
        memory.id = data["id"]
        memory.created_at = datetime.fromisoformat(data["created_at"])
        memory.last_accessed = datetime.fromisoformat(data["last_accessed"])
        memory.access_count = data.get("access_count", 0)
        return memory
    
    def access(self):
        """访问记忆，更新访问时间和计数"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, storage_path: str = None, max_short_term: int = 100, 
                 max_long_term: int = 1000):
        """
        初始化记忆管理器
        
        Args:
            storage_path: 记忆存储路径
            max_short_term: 短期记忆最大数量
            max_long_term: 长期记忆最大数量
        """
        if storage_path is None:
            from utils import get_data_path
            storage_path = get_data_path("memory_storage")
        
        self.storage_path = storage_path
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term
        
        # 记忆存储
        self.short_term_memories: List[Memory] = []
        self.long_term_memories: List[Memory] = []
        
        # 索引用于快速检索
        self.tag_index: Dict[str, List[str]] = defaultdict(list)  # tag -> memory_ids
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)  # keyword -> memory_ids
        
        # 智能记忆过滤器
        self.smart_filter = SmartMemoryFilter()
        
        # 隐私保护：敏感信息关键词
        self.sensitive_keywords = [
            "密码", "password", "账号", "account", "身份证", "id card",
            "银行卡", "bank card", "信用卡", "credit card", "手机号", "phone",
            "地址", "address", "邮箱", "email", "姓名", "name"
        ]
        
        # 加载已有记忆
        self._load_memories()
    
    def _get_memory_file(self) -> str:
        """获取记忆文件路径"""
        return os.path.join(self.storage_path, "memories.json")
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
    
    def _load_memories(self):
        """从文件加载记忆"""
        memory_file = self._get_memory_file()
        if not os.path.exists(memory_file):
            return
        
        try:
            with open(memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载短期记忆
            for mem_data in data.get("short_term", []):
                memory = Memory.from_dict(mem_data)
                self.short_term_memories.append(memory)
            
            # 加载长期记忆
            for mem_data in data.get("long_term", []):
                memory = Memory.from_dict(mem_data)
                self.long_term_memories.append(memory)
            
            # 重建索引
            self._rebuild_indexes()
            
        except Exception as e:
            print(f"加载记忆失败: {e}")
    
    def _save_memories(self):
        """保存记忆到文件"""
        self._ensure_storage_dir()
        memory_file = self._get_memory_file()
        
        try:
            data = {
                "short_term": [m.to_dict() for m in self.short_term_memories],
                "long_term": [m.to_dict() for m in self.long_term_memories],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存记忆失败: {e}")
    
    def _rebuild_indexes(self):
        """重建索引"""
        self.tag_index.clear()
        self.keyword_index.clear()
        
        all_memories = self.short_term_memories + self.long_term_memories
        for memory in all_memories:
            # 标签索引
            for tag in memory.tags:
                self.tag_index[tag].append(memory.id)
            
            # 关键词索引
            keywords = self._extract_keywords(memory.content)
            for keyword in keywords:
                self.keyword_index[keyword].append(memory.id)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（可以后续改进为使用NLP）
        # 移除标点符号和特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        
        # 分词（简单按空格分割，可以改进为使用jieba等）
        words = text.split()
        
        # 过滤停用词和短词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        keywords = [w.lower() for w in words if len(w) > 1 and w.lower() not in stopwords]
        
        return keywords
    
    def _calculate_importance(self, content: str, context: Dict[str, Any] = None) -> float:
        """
        计算记忆的重要性分数
        
        Args:
            content: 记忆内容
            context: 上下文信息
        
        Returns:
            重要性分数 (0.0 到 1.0)
        """
        importance = 0.5  # 基础分数
        
        # 1. 内容长度因素
        if len(content) > 100:
            importance += 0.1
        if len(content) > 200:
            importance += 0.1
        
        # 2. 关键词因素
        important_keywords = [
            "重要", "important", "记住", "remember", "关键", "key",
            "必须", "must", "不要忘记", "don't forget", "提醒", "remind"
        ]
        for keyword in important_keywords:
            if keyword in content.lower():
                importance += 0.15
                break
        
        # 3. 任务相关因素
        task_keywords = ["任务", "task", "计划", "plan", "目标", "goal", "截止", "deadline"]
        for keyword in task_keywords:
            if keyword in content.lower():
                importance += 0.1
                break
        
        # 4. 时间相关因素
        time_keywords = ["明天", "tomorrow", "下周", "next week", "今天", "today", "时间", "time"]
        for keyword in time_keywords:
            if keyword in content.lower():
                importance += 0.05
                break
        
        # 5. 上下文因素
        if context:
            # 如果用户明确要求记住
            if context.get("explicit_remember"):
                importance += 0.2
            
            # 如果是任务创建相关
            if context.get("task_creation"):
                importance += 0.15
        
        # 限制在 0.0 到 1.0 之间
        return min(max(importance, 0.0), 1.0)
    
    def _contains_sensitive_info(self, content: str) -> bool:
        """检查是否包含敏感信息"""
        content_lower = content.lower()
        for keyword in self.sensitive_keywords:
            if keyword in content_lower:
                # 进一步检查是否有数字模式（可能是敏感数据）
                if re.search(r'\d{4,}', content):
                    return True
        return False
    
    def _sanitize_content(self, content: str) -> str:
        """清理敏感信息"""
        # 移除可能的手机号
        content = re.sub(r'1[3-9]\d{9}', '[手机号]', content)
        
        # 移除可能的身份证号
        content = re.sub(r'\d{17}[\dXx]', '[身份证号]', content)
        
        # 移除可能的银行卡号
        content = re.sub(r'\d{16,19}', '[银行卡号]', content)
        
        return content
    
    def add_memory(self, content: str, memory_type: str = "auto",
                   tags: List[str] = None, metadata: Dict[str, Any] = None,
                   context: Dict[str, Any] = None,
                   force_remember: bool = False) -> Optional[Memory]:
        """
        添加新记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型 ("short_term", "long_term", "auto")
            tags: 标签列表
            metadata: 元数据
            context: 上下文信息
            force_remember: 是否强制记忆（跳过智能过滤）
        
        Returns:
            创建的记忆对象，如果不值得记忆则返回 None
        """
        # 🧠 智能过滤：判断是否值得记忆
        if not force_remember:
            should_remember, reason, importance = self.smart_filter.should_remember(content, context)
            
            if not should_remember:
                # 记录过滤日志
                print(f"[智能过滤] 跳过记忆: {reason} (重要性: {importance:.2f})")
                print(f"  内容: {content[:50]}...")
                return None
            else:
                print(f"[智能过滤] ✅ 记忆: {reason} (重要性: {importance:.2f})")
        
        # 检查敏感信息
        if self._contains_sensitive_info(content):
            content = self._sanitize_content(content)
            if metadata is None:
                metadata = {}
            metadata["sanitized"] = True
        
        # 计算重要性
        calculated_importance = self._calculate_importance(content, context)
        
        # 如果智能过滤器给出了重要性分数，使用它
        if not force_remember and importance > 0:
            calculated_importance = max(calculated_importance, importance)
        
        # 自动决定记忆类型
        if memory_type == "auto":
            if calculated_importance > 0.7:
                memory_type = "long_term"
            else:
                memory_type = "short_term"
        
        # 创建记忆对象
        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=calculated_importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # 添加到对应的记忆列表
        if memory_type == "short_term":
            self.short_term_memories.append(memory)
            # 检查是否需要升级为长期记忆
            self._check_upgrade(memory)
            # 清理超出限制的短期记忆
            self._cleanup_short_term()
        else:
            self.long_term_memories.append(memory)
            # 清理超出限制的长期记忆
            self._cleanup_long_term()
        
        # 更新索引
        for tag in memory.tags:
            self.tag_index[tag].append(memory.id)
        
        keywords = self._extract_keywords(memory.content)
        for keyword in keywords:
            self.keyword_index[keyword].append(memory.id)
        
        # 保存记忆
        self._save_memories()
        
        return memory
    
    def _check_upgrade(self, memory: Memory):
        """检查是否需要将短期记忆升级为长期记忆"""
        # 如果访问次数超过阈值，升级为长期记忆
        if memory.access_count >= 3 and memory.importance > 0.6:
            if memory in self.short_term_memories:
                self.short_term_memories.remove(memory)
                memory.memory_type = "long_term"
                self.long_term_memories.append(memory)
    
    def _cleanup_short_term(self):
        """清理短期记忆"""
        if len(self.short_term_memories) > self.max_short_term:
            # 按重要性和访问时间排序
            self.short_term_memories.sort(
                key=lambda m: (m.importance, m.last_accessed),
                reverse=True
            )
            
            # 保留最重要的记忆
            removed = self.short_term_memories[self.max_short_term:]
            self.short_term_memories = self.short_term_memories[:self.max_short_term]
            
            # 从索引中移除
            for memory in removed:
                self._remove_from_index(memory)
    
    def _cleanup_long_term(self):
        """清理长期记忆"""
        if len(self.long_term_memories) > self.max_long_term:
            # 按重要性和访问时间排序
            self.long_term_memories.sort(
                key=lambda m: (m.importance, m.last_accessed),
                reverse=True
            )
            
            # 保留最重要的记忆
            removed = self.long_term_memories[self.max_long_term:]
            self.long_term_memories = self.long_term_memories[:self.max_long_term]
            
            # 从索引中移除
            for memory in removed:
                self._remove_from_index(memory)
    
    def _remove_from_index(self, memory: Memory):
        """从索引中移除记忆"""
        for tag in memory.tags:
            if memory.id in self.tag_index[tag]:
                self.tag_index[tag].remove(memory.id)
        
        keywords = self._extract_keywords(memory.content)
        for keyword in keywords:
            if memory.id in self.keyword_index[keyword]:
                self.keyword_index[keyword].remove(memory.id)
    
    def search_memories(self, query: str, top_k: int = 5, 
                       memory_type: str = None) -> List[Tuple[Memory, float]]:
        """
        检索相关记忆
        
        Args:
            query: 查询文本
            top_k: 返回前k个结果
            memory_type: 记忆类型过滤 ("short_term", "long_term", None表示全部)
        
        Returns:
            记忆列表及其相关性分数
        """
        # 提取查询关键词
        query_keywords = self._extract_keywords(query)
        
        # 收集候选记忆
        candidate_ids = set()
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                candidate_ids.update(self.keyword_index[keyword])
        
        # 获取候选记忆对象
        candidates = []
        all_memories = self.short_term_memories + self.long_term_memories
        memory_dict = {m.id: m for m in all_memories}
        
        for mem_id in candidate_ids:
            if mem_id in memory_dict:
                memory = memory_dict[mem_id]
                
                # 类型过滤
                if memory_type and memory.memory_type != memory_type:
                    continue
                
                candidates.append(memory)
        
        # 计算相关性分数
        results = []
        for memory in candidates:
            score = self._calculate_relevance(memory, query_keywords)
            results.append((memory, score))
        
        # 按相关性排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前k个结果
        return results[:top_k]
    
    def _calculate_relevance(self, memory: Memory, query_keywords: List[str]) -> float:
        """计算记忆与查询的相关性"""
        score = 0.0
        
        # 1. 关键词匹配分数
        memory_keywords = self._extract_keywords(memory.content)
        matched_keywords = set(query_keywords) & set(memory_keywords)
        keyword_score = len(matched_keywords) / max(len(query_keywords), 1)
        score += keyword_score * 0.5
        
        # 2. 重要性分数
        score += memory.importance * 0.3
        
        # 3. 时间衰减分数（越近的记忆权重越高）
        days_old = (datetime.now() - memory.created_at).days
        time_score = max(0, 1 - days_old / 30)  # 30天衰减到0
        score += time_score * 0.1
        
        # 4. 访问频率分数
        access_score = min(memory.access_count / 10, 1.0)  # 最多10次访问达到满分
        score += access_score * 0.1
        
        return score
    
    def get_context_for_chat(self, current_message: str, max_memories: int = 5) -> str:
        """
        为聊天获取相关上下文
        
        Args:
            current_message: 当前用户消息
            max_memories: 最大记忆数量
        
        Returns:
            格式化的上下文字符串
        """
        # 检索相关记忆
        results = self.search_memories(current_message, top_k=max_memories)
        
        if not results:
            return ""
        
        # 格式化上下文
        context_parts = ["【历史记忆】"]
        for memory, score in results:
            # 标记记忆被访问
            memory.access()
            
            # 添加到上下文
            time_str = memory.created_at.strftime("%Y-%m-%d")
            context_parts.append(f"- [{time_str}] {memory.content}")
        
        # 保存访问更新
        self._save_memories()
        
        return "\n".join(context_parts)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "short_term_count": len(self.short_term_memories),
            "long_term_count": len(self.long_term_memories),
            "total_memories": len(self.short_term_memories) + len(self.long_term_memories),
            "tag_count": len(self.tag_index),
            "keyword_count": len(self.keyword_index),
            "oldest_memory": min(
                [m.created_at for m in self.short_term_memories + self.long_term_memories],
                default=datetime.now()
            ).isoformat(),
            "newest_memory": max(
                [m.created_at for m in self.short_term_memories + self.long_term_memories],
                default=datetime.now()
            ).isoformat()
        }
    
    def clear_memories(self, memory_type: str = None):
        """
        清除记忆
        
        Args:
            memory_type: 要清除的类型 ("short_term", "long_term", None表示全部)
        """
        if memory_type is None or memory_type == "short_term":
            self.short_term_memories.clear()
        
        if memory_type is None or memory_type == "long_term":
            self.long_term_memories.clear()
        
        # 重建索引
        self._rebuild_indexes()
        
        # 保存
        self._save_memories()
    
    def export_memories(self, filepath: str):
        """导出记忆到文件"""
        data = {
            "short_term": [m.to_dict() for m in self.short_term_memories],
            "long_term": [m.to_dict() for m in self.long_term_memories],
            "exported_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_memories(self, filepath: str, merge: bool = True):
        """
        从文件导入记忆
        
        Args:
            filepath: 文件路径
            merge: 是否合并现有记忆（True）或替换（False）
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not merge:
            self.clear_memories()
        
        # 导入短期记忆
        for mem_data in data.get("short_term", []):
            memory = Memory.from_dict(mem_data)
            self.short_term_memories.append(memory)
        
        # 导入长期记忆
        for mem_data in data.get("long_term", []):
            memory = Memory.from_dict(mem_data)
            self.long_term_memories.append(memory)
        
        # 重建索引
        self._rebuild_indexes()
        
        # 保存
        self._save_memories()
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """
        获取智能过滤器的统计数据
        
        Returns:
            统计数据字典
        """
        return self.smart_filter.get_stats()
    
    def reset_filter_stats(self):
        """重置智能过滤器的统计数据"""
        self.smart_filter.reset_stats()
    
    def get_memory_quality_report(self) -> Dict[str, Any]:
        """
        获取记忆质量报告
        
        Returns:
            质量报告字典
        """
        from smart_memory_filter import MemoryQualityAnalyzer
        
        analyzer = MemoryQualityAnalyzer()
        
        # 分析所有记忆的质量
        all_memories = self.short_term_memories + self.long_term_memories
        
        if not all_memories:
            return {
                "total_memories": 0,
                "average_quality": 0.0,
                "quality_distribution": {}
            }
        
        quality_scores = []
        
        for memory in all_memories[:50]:  # 只分析最近50条
            metrics = analyzer.analyze_memory_quality(memory.content)
            quality_scores.append(analyzer.get_overall_quality())
        
        # 计算平均质量
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # 质量分布
        quality_distribution = {
            "high": sum(1 for q in quality_scores if q >= 0.7),
            "medium": sum(1 for q in quality_scores if 0.4 <= q < 0.7),
            "low": sum(1 for q in quality_scores if q < 0.4)
        }
        
        return {
            "total_memories": len(all_memories),
            "analyzed_memories": len(quality_scores),
            "average_quality": avg_quality,
            "quality_distribution": quality_distribution,
            "short_term_count": len(self.short_term_memories),
            "long_term_count": len(self.long_term_memories)
        }
