"""
智能记忆过滤系统
自动判断内容是否值得记忆，提高记忆质量
"""

import re
from typing import Dict, Any, Tuple
from datetime import datetime


class SmartMemoryFilter:
    """智能记忆过滤器"""
    
    def __init__(self):
        # 不值得记忆的模式
        self.skip_patterns = [
            # 简单的问候和寒暄
            r'^(你好|hi|hello|嗨|早上好|晚上好|下午好)[！!。.]*$',
            r'^(谢谢|感谢|thanks|thank you)[！!。.]*$',
            r'^(好的|ok|嗯|哦|明白|了解)[！!。.]*$',
            
            # 简单的确认
            r'^(是的|对|没错|正确|right)[！!。.]*$',
            r'^(不是|不对|错了|wrong)[！!。.]*$',
            
            # 简单的表情符号
            r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0]+$',
        ]
        
        # 值得记忆的关键词
        self.important_keywords = {
            # 任务相关
            'task': ['任务', '作业', '考试', '截止', 'deadline', '计划', '目标', '安排'],
            'schedule': ['明天', '下周', '周末', '时间', '日期', '提醒', '闹钟'],
            'preference': ['喜欢', '偏好', '习惯', '通常', '总是', '一般'],
            'important': ['重要', '关键', '必须', '一定', '记住', '记得'],
            'learning': ['学习', '复习', '预习', '练习', '作业', '考试'],
        }
        
        # 敏感信息关键词（不应该记忆）
        self.sensitive_keywords = [
            '密码', 'password', '账号', 'account', '身份证', 'id card',
            '银行卡', 'bank card', '手机号', 'phone', '地址', 'address'
        ]
        
        # 统计数据
        self.stats = {
            'total_checked': 0,
            'should_remember': 0,
            'should_skip': 0,
            'sensitive_blocked': 0
        }
    
    def should_remember(self, content: str, context: Dict[str, Any] = None) -> Tuple[bool, str, float]:
        """
        判断内容是否值得记忆
        
        Args:
            content: 要判断的内容
            context: 上下文信息
        
        Returns:
            (是否记忆, 原因, 重要性分数)
        """
        self.stats['total_checked'] += 1
        
        # 1. 检查是否为空或过短
        if not content or len(content.strip()) < 3:
            self.stats['should_skip'] += 1
            return False, "内容过短", 0.0
        
        content = content.strip()
        
        # 2. 检查是否包含敏感信息
        if self._contains_sensitive_info(content):
            self.stats['sensitive_blocked'] += 1
            return False, "包含敏感信息", 0.0
        
        # 3. 检查是否匹配跳过模式
        for pattern in self.skip_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                self.stats['should_skip'] += 1
                return False, "简单问候或确认", 0.0
        
        # 4. 检查是否包含重要关键词
        importance_score, matched_category = self._check_importance(content)
        
        # 5. 检查是否有实质内容
        has_substance = self._has_substance(content)
        
        # 6. 检查上下文
        context_bonus = 0.0
        if context:
            # 如果用户明确要求记住
            if context.get('explicit_remember'):
                importance_score += 0.3
                context_bonus = 0.3
            
            # 如果是任务创建相关
            if context.get('task_creation'):
                importance_score += 0.2
                context_bonus = 0.2
            
            # 如果是 AI 建议相关
            if context.get('ai_suggestion'):
                importance_score += 0.1
                context_bonus = 0.1
        
        # 7. 综合判断
        final_score = min(importance_score, 1.0)
        
        # 决策逻辑
        if final_score >= 0.3 or has_substance:
            self.stats['should_remember'] += 1
            
            # 生成原因
            reasons = []
            if matched_category:
                reasons.append(f"包含{matched_category}相关信息")
            if has_substance:
                reasons.append("包含实质内容")
            if context_bonus > 0:
                reasons.append("上下文重要")
            
            reason = "、".join(reasons) if reasons else "有价值的信息"
            
            return True, reason, final_score
        else:
            self.stats['should_skip'] += 1
            return False, "信息价值较低", final_score
    
    def _contains_sensitive_info(self, content: str) -> bool:
        """检查是否包含敏感信息"""
        content_lower = content.lower()
        
        # 检查敏感关键词
        for keyword in self.sensitive_keywords:
            if keyword in content_lower:
                # 进一步检查是否有数字模式
                if re.search(r'\d{4,}', content):
                    return True
        
        return False
    
    def _check_importance(self, content: str) -> Tuple[float, str]:
        """检查内容重要性"""
        content_lower = content.lower()
        max_score = 0.0
        matched_category = ""
        
        for category, keywords in self.important_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    score = 0.3 if category in ['task', 'important'] else 0.2
                    if score > max_score:
                        max_score = score
                        matched_category = category
        
        return max_score, matched_category
    
    def _has_substance(self, content: str) -> bool:
        """检查是否有实质内容"""
        # 1. 长度检查
        if len(content) < 10:
            return False
        
        # 2. 检查是否包含具体信息
        # 包含数字（可能是时间、日期、数量等）
        has_numbers = bool(re.search(r'\d+', content))
        
        # 包含时间词
        has_time = bool(re.search(r'(明天|后天|下周|周[一二三四五六日]|今天|\d+月|\d+号|\d+点)', content))
        
        # 包含任务词
        has_task = bool(re.search(r'(任务|作业|考试|复习|预习|练习|计划)', content))
        
        # 包含学习词
        has_learning = bool(re.search(r'(学习|科目|数学|语文|英语|物理|化学)', content))
        
        # 包含问句（可能是重要问题）
        has_question = '?' in content or '？' in content
        
        # 包含感叹（可能是重要提醒）
        has_exclamation = '!' in content or '！' in content
        
        # 综合判断
        substance_indicators = [has_numbers, has_time, has_task, has_learning, has_question, has_exclamation]
        
        # 至少包含2个实质指标
        return sum(substance_indicators) >= 2
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        return {
            **self.stats,
            'remember_rate': (
                self.stats['should_remember'] / self.stats['total_checked'] * 100
                if self.stats['total_checked'] > 0 else 0
            )
        }
    
    def reset_stats(self):
        """重置统计数据"""
        self.stats = {
            'total_checked': 0,
            'should_remember': 0,
            'should_skip': 0,
            'sensitive_blocked': 0
        }


class MemoryQualityAnalyzer:
    """记忆质量分析器"""
    
    def __init__(self):
        self.quality_metrics = {
            'relevance': 0.0,      # 相关性
            'uniqueness': 0.0,     # 独特性
            'timeliness': 0.0,     # 时效性
            'completeness': 0.0,   # 完整性
        }
    
    def analyze_memory_quality(self, content: str, context: Dict[str, Any] = None) -> Dict[str, float]:
        """
        分析记忆质量
        
        Returns:
            质量指标字典
        """
        # 1. 相关性（与任务管理相关）
        self.quality_metrics['relevance'] = self._calculate_relevance(content)
        
        # 2. 独特性（是否重复）
        self.quality_metrics['uniqueness'] = self._calculate_uniqueness(content, context)
        
        # 3. 时效性（是否包含时间信息）
        self.quality_metrics['timeliness'] = self._calculate_timeliness(content)
        
        # 4. 完整性（信息是否完整）
        self.quality_metrics['completeness'] = self._calculate_completeness(content)
        
        return self.quality_metrics
    
    def _calculate_relevance(self, content: str) -> float:
        """计算相关性"""
        relevant_keywords = [
            '任务', '作业', '考试', '学习', '计划', '时间', '截止',
            'task', 'homework', 'exam', 'study', 'plan', 'time', 'deadline'
        ]
        
        content_lower = content.lower()
        matches = sum(1 for kw in relevant_keywords if kw in content_lower)
        
        return min(matches * 0.2, 1.0)
    
    def _calculate_uniqueness(self, content: str, context: Dict[str, Any] = None) -> float:
        """计算独特性"""
        # 简单实现：基于内容长度和特殊字符
        base_score = 0.5
        
        # 长度加成
        if len(content) > 50:
            base_score += 0.2
        if len(content) > 100:
            base_score += 0.1
        
        # 特殊字符加成（包含具体信息）
        if re.search(r'\d+', content):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _calculate_timeliness(self, content: str) -> float:
        """计算时效性"""
        time_keywords = [
            '明天', '后天', '下周', '今天', '现在', '马上', '立即',
            'tomorrow', 'today', 'now', 'immediately'
        ]
        
        content_lower = content.lower()
        for keyword in time_keywords:
            if keyword in content_lower:
                return 0.8
        
        return 0.3
    
    def _calculate_completeness(self, content: str) -> float:
        """计算完整性"""
        # 检查是否包含完整句子
        has_subject = bool(re.search(r'[我你他她它]', content))
        has_verb = bool(re.search(r'[是要有做学看说]', content))
        has_object = bool(re.search(r'[任务作业考试计划]', content))
        
        # 检查是否包含具体信息
        has_details = bool(re.search(r'\d+|时间|地点|科目', content))
        
        score = 0.3
        if has_subject:
            score += 0.2
        if has_verb:
            score += 0.2
        if has_object:
            score += 0.2
        if has_details:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_overall_quality(self) -> float:
        """获取整体质量分数"""
        return sum(self.quality_metrics.values()) / len(self.quality_metrics)


# 使用示例
if __name__ == "__main__":
    # 创建智能过滤器
    filter = SmartMemoryFilter()
    
    # 测试用例
    test_cases = [
        "你好",
        "明天有数学考试",
        "谢谢",
        "我需要记住这个任务：周五交作业",
        "我的密码是123456",
        "下周计划：复习英语、做数学作业",
    ]
    
    print("=" * 60)
    print("智能记忆过滤测试")
    print("=" * 60)
    
    for content in test_cases:
        should_remember, reason, score = filter.should_remember(content)
        print(f"\n内容: {content}")
        print(f"是否记忆: {'✅ 是' if should_remember else '❌ 否'}")
        print(f"原因: {reason}")
        print(f"重要性: {score:.2f}")
    
    print("\n" + "=" * 60)
    print("统计数据:")
    print(filter.get_stats())
