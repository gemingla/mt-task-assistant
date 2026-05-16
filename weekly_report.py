"""
AI 周报生成模块
自动生成周报，分析工作效率，提供改进建议
"""

from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
import json
import os


class WeeklyReportGenerator:
    """周报生成器"""

    def __init__(self, task_manager=None, stats_manager=None):
        self.task_manager = task_manager
        self.stats_manager = stats_manager

    def generate_report(self, week_offset: int = 0) -> Dict:
        """生成周报"""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        end_of_week = start_of_week + timedelta(days=6)

        start_str, end_str = start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")

        completed_tasks = self._get_tasks_in_period(start_str, end_str)
        pending_tasks = self._get_pending_tasks(end_str)
        statistics = self._calculate_statistics(completed_tasks)
        suggestions = self._generate_suggestions(statistics, completed_tasks, pending_tasks)
        score = self._calculate_score(statistics, len(pending_tasks))

        report = {
            "period": f"{start_str} 至 {end_str}",
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "statistics": statistics,
            "suggestions": suggestions,
            "score": score,
        }
        report["summary"] = self._generate_summary(report)
        return report

    def _get_tasks_in_period(self, start_str: str, end_str: str) -> List:
        """获取指定时间段内完成的任务"""
        if not self.task_manager:
            return []

        tasks = []
        for task in self.task_manager.tasks:
            completed_at = getattr(task, 'completed_at', None)
            if completed_at and task.completed:
                task_date = completed_at[:10]
                if start_str <= task_date <= end_str:
                    tasks.append(task)
        return tasks

    def _get_pending_tasks(self, end_str: str) -> List:
        """获取待处理任务"""
        if not self.task_manager:
            return []

        pending = []
        for task in self.task_manager.tasks:
            if task.completed:
                continue
            due_date = getattr(task, 'due_date', None)
            if due_date:
                due_str = due_date.strftime("%Y-%m-%d") if isinstance(due_date, datetime) else due_date[:10]
                if due_str <= end_str:
                    pending.append(task)
        return pending

    def _calculate_statistics(self, completed_tasks: List) -> Dict:
        """计算统计数据"""
        stats = {
            "total_completed": len(completed_tasks),
            "total_estimated_minutes": 0,
            "by_priority": defaultdict(int),
            "by_tag": defaultdict(int),
            "by_day": defaultdict(int),
            "completion_rate": 0.0,
        }

        for task in completed_tasks:
            stats["total_estimated_minutes"] += getattr(task, 'estimated_minutes', 0) or 0
            stats["by_priority"][getattr(task, 'priority', 2)] += 1
            for tag in getattr(task, 'tags', []):
                stats["by_tag"][tag] += 1
            completed_at = getattr(task, 'completed_at', '')
            if completed_at:
                stats["by_day"][completed_at[:10]] += 1

        if self.task_manager:
            total = len([t for t in self.task_manager.tasks if not t.completed]) + len(completed_tasks)
            stats["completion_rate"] = len(completed_tasks) / total if total > 0 else 0

        return stats

    def _generate_suggestions(self, statistics: Dict, completed_tasks: List, pending_tasks: List) -> List:
        """生成改进建议"""
        suggestions = []

        # 完成率建议
        rate = statistics["completion_rate"]
        if rate < 0.5:
            suggestions.append({"type": "warning", "title": "完成率偏低",
                               "content": f"本周完成率 {rate*100:.1f}%，建议减少任务或分解大任务"})
        elif rate > 0.8:
            suggestions.append({"type": "success", "title": "完成率优秀",
                               "content": f"本周完成率 {rate*100:.1f}%，继续保持！"})

        # 待办任务建议
        pending_count = len(pending_tasks)
        if pending_count > 5:
            suggestions.append({"type": "warning", "title": "待办任务堆积",
                               "content": f"有 {pending_count} 个待处理任务"})

        # 高峰时段建议
        by_day = statistics.get("by_day", {})
        if len(by_day) < 3 and len(completed_tasks) > 3:
            suggestions.append({"type": "info", "title": "工作分布不均",
                               "content": "建议更均匀地分配任务"})

        if not suggestions:
            suggestions.append({"type": "success", "title": "工作状态良好",
                               "content": "继续保持当前的工作节奏！"})

        return suggestions

    def _calculate_score(self, statistics: Dict, pending_count: int) -> float:
        """计算效率评分 (0-100)"""
        score = 50 + statistics["completion_rate"] * 30

        task_count = statistics["total_completed"]
        if task_count >= 10:
            score += 10
        elif task_count >= 5:
            score += 5

        if pending_count > 10:
            score -= 15
        elif pending_count > 5:
            score -= 10

        high_priority = statistics["by_priority"].get(4, 0) + statistics["by_priority"].get(5, 0)
        score += min(high_priority * 2, 10)

        return min(max(score, 0), 100)

    def _generate_summary(self, report: Dict) -> str:
        """生成总结文字"""
        stats = report["statistics"]
        score = report["score"]
        rating = "优秀" if score >= 80 else "良好" if score >= 60 else "一般" if score >= 40 else "需改进"

        summary = f"""📅 报告周期：{report['period']}

📊 本周总结：
• 完成任务：{stats['total_completed']} 个
• 待处理任务：{len(report['pending_tasks'])} 个
• 效率评分：{score:.0f} 分 ({rating})
• 预计用时：{stats['total_estimated_minutes'] // 60} 小时 {stats['total_estimated_minutes'] % 60} 分钟
"""
        if stats["by_tag"]:
            top_tags = sorted(stats["by_tag"].items(), key=lambda x: x[1], reverse=True)[:3]
            summary += "🏷️ 主要类别：" + "、".join([f"{t}({c})" for t, c in top_tags]) + "\n"

        if report["suggestions"]:
            summary += "\n💡 建议：\n"
            for sug in report["suggestions"][:3]:
                summary += f"  • {sug['title']}：{sug['content']}\n"

        return summary

    def format_report_text(self, report: Dict) -> str:
        """格式化报告为纯文本"""
        lines = [f"{'='*50}", "          📋 周 报", f"{'='*50}", "", report["summary"], "",
                 f"✅ 已完成任务 ({len(report['completed_tasks'])} 个)："]

        for task in report['completed_tasks'][:10]:
            lines.append(f"  ✓ {task.name}")
        if len(report['completed_tasks']) > 10:
            lines.append(f"  ... 还有 {len(report['completed_tasks']) - 10} 个")

        lines.extend(["", f"⏳ 待处理任务 ({len(report['pending_tasks'])} 个)："])
        for task in report['pending_tasks'][:5]:
            due_val = getattr(task, 'due_date', '无')
            if due_val and due_val != '无':
                due = due_val.strftime("%Y-%m-%d") if isinstance(due_val, datetime) else due_val[:10]
            else:
                due = '无'
            lines.append(f"  • {task.name} (截止: {due})")

        lines.extend([f"{'='*50}", f"📈 效率评分：{report['score']:.0f}/100"])
        return "\n".join(lines)


def generate_weekly_report(task_manager, stats_manager=None, week_offset: int = 0) -> Dict:
    """快捷函数：生成周报"""
    return WeeklyReportGenerator(task_manager, stats_manager).generate_report(week_offset)
