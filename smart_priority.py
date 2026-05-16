"""
智能优先级排序模块
综合多种因素计算任务优先级，提供智能排序建议
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional


class SmartPriorityEngine:
    """智能优先级引擎"""

    # 标签重要性权重
    TAG_WEIGHTS = {
        "紧急": 2.0, "重要": 1.8, "工作": 1.3, "学习": 1.3, "项目": 1.4,
        "考试": 1.8, "会议": 1.5, "截止": 1.7,
        "生活": 1.0, "健康": 1.2, "运动": 1.1, "阅读": 1.0,
        "娱乐": 0.7, "休闲": 0.6, "游戏": 0.5,
    }

    def __init__(self, task_manager=None, stats_manager=None):
        self.task_manager = task_manager
        self.stats_manager = stats_manager
        self.now = datetime.now()

    def calculate_smart_priority(self, task) -> float:
        """计算任务的智能优先级分数 (0-100)"""
        self.now = datetime.now()

        # 用户设置优先级 (0-30分)
        user_priority = getattr(task, 'priority', 2)
        score = (user_priority / 5.0) * 30

        # 时间紧迫度 (0-40分)
        score += self._calculate_urgency_score(task)

        # 标签重要性 (0-15分)
        score += self._calculate_tag_score(task)

        # 任务年龄/饥饿度 (0-10分)
        score += self._calculate_age_score(task)

        # 历史完成率调整 (-5 到 +5分)
        score += self._calculate_completion_adjustment(task)

        return min(max(score, 0), 100)

    def _calculate_urgency_score(self, task) -> float:
        """计算时间紧迫度分数"""
        due_date = getattr(task, 'due_date', None)
        if not due_date:
            return 5

        try:
            due = datetime.strptime(due_date[:16], "%Y-%m-%d %H:%M") if isinstance(due_date, str) else due_date
            time_diff = (due - self.now).total_seconds()

            if time_diff < 0:
                return 120  # 已过期
            elif time_diff < 86400:
                return 100  # 24小时内
            elif time_diff < 172800:
                return 80   # 48小时内
            elif time_diff < 604800:
                return 60 * (1 - time_diff / 604800)  # 7天内递减
            elif time_diff < 1209600:
                return 48   # 14天内
            else:
                return max(5, 20 - time_diff / 86400 * 0.5)
        except (ValueError, TypeError):
            return 5

    def _calculate_tag_score(self, task) -> float:
        """计算标签重要性分数"""
        tags = getattr(task, 'tags', [])
        if not tags:
            return 7.5

        avg_weight = sum(self.TAG_WEIGHTS.get(t.lower(), 1.0) for t in tags) / len(tags)
        return min(avg_weight * 7.5, 15)

    def _calculate_age_score(self, task) -> float:
        """计算任务年龄分数（防止饥饿）"""
        created_date = getattr(task, 'created_date', None)
        if not created_date:
            return 5

        try:
            created = datetime.strptime(created_date[:10], "%Y-%m-%d") if isinstance(created_date, str) else created_date
            age_days = (self.now - created).days

            if age_days <= 1:
                return 8
            elif age_days <= 3:
                return 7
            elif age_days <= 7:
                return 6
            elif age_days <= 14:
                return 7 + min(age_days * 0.2, 3)
            else:
                return min(10, 5 + age_days * 0.3)
        except (ValueError, TypeError):
            return 5

    def _calculate_completion_adjustment(self, task) -> float:
        """根据历史完成率调整分数"""
        if not self.stats_manager or not self.task_manager:
            return 0

        tags = getattr(task, 'tags', [])
        if not tags:
            return 0

        rates = []
        for tag in tags:
            tag_tasks = [t for t in self.task_manager.tasks if tag in getattr(t, 'tags', [])]
            if tag_tasks:
                completed = sum(1 for t in tag_tasks if t.completed)
                rates.append(completed / len(tag_tasks))

        if not rates:
            return 0

        return min(max((sum(rates) / len(rates) - 0.5) * 10, -5), 5)

    def sort_tasks_by_priority(self, tasks: List = None) -> List:
        """智能排序任务列表"""
        if tasks is None:
            tasks = [t for t in self.task_manager.tasks if not t.completed] if self.task_manager else []

        task_scores = [(t, self.calculate_smart_priority(t)) for t in tasks]
        task_scores.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in task_scores]

    def get_priority_breakdown(self, task) -> Dict:
        """获取任务优先级的详细分析"""
        self.now = datetime.now()

        breakdown = {
            "total_score": self.calculate_smart_priority(task),
            "user_priority": (getattr(task, 'priority', 2) / 5.0) * 30,
            "urgency": self._calculate_urgency_score(task),
            "tag_importance": self._calculate_tag_score(task),
            "age": self._calculate_age_score(task),
            "completion_rate": self._calculate_completion_adjustment(task),
        }

        # 生成建议
        suggestions = []
        if breakdown["urgency"] > 30:
            suggestions.append("⚠️ 时间紧迫")
        if breakdown["user_priority"] > 20:
            suggestions.append("⭐ 高优先级")
        if breakdown["tag_importance"] > 10:
            suggestions.append("🏷️ 重要类别")
        if breakdown["age"] > 8:
            suggestions.append("⏰ 较久未处理")

        breakdown["suggestion"] = " | ".join(suggestions) if suggestions else "✅ 正常处理"
        return breakdown


def get_smart_sorted_tasks(task_manager, stats_manager=None, include_completed: bool = False) -> List:
    """快捷函数：获取智能排序后的任务列表"""
    engine = SmartPriorityEngine(task_manager, stats_manager)
    tasks = task_manager.tasks if include_completed else [t for t in task_manager.tasks if not t.completed]
    return engine.sort_tasks_by_priority(tasks)
