"""
AI 使用统计模块
记录和分析 AI 使用情况，帮助用户反思和学习
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any


class AIUsageStats:
    """AI 使用统计管理器"""
    
    def __init__(self, stats_file: str = "ai_usage_stats.json"):
        self.stats_file = stats_file
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """加载统计数据"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认统计结构
        return {
            "total_calls": 0,
            "daily_stats": {},  # {"2026-04-24": {"count": 10, "scenarios": {...}}}
            "scenarios": defaultdict(int),  # {"task_analysis": 50, "priority_adjustment": 30}
            "adopted_suggestions": 0,
            "rejected_suggestions": 0,
            "first_use_date": datetime.now().strftime("%Y-%m-%d"),
            "last_use_date": datetime.now().strftime("%Y-%m-%d"),
            "learning_time": 0,  # 学习时间（分钟）
            "tips_shown": 0,  # 显示的小贴士数量
        }
    
    def _save_stats(self):
        """保存统计数据"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存统计数据失败: {e}")
    
    def record_ai_call(self, scenario: str = "general"):
        """
        记录一次 AI 调用
        
        Args:
            scenario: 使用场景（task_analysis, priority_adjustment, study_plan, etc.）
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 更新总调用次数
        self.stats["total_calls"] += 1
        
        # 更新日期统计
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {
                "count": 0,
                "scenarios": {}
            }
        
        self.stats["daily_stats"][today]["count"] += 1
        
        # 更新场景统计
        if scenario not in self.stats["daily_stats"][today]["scenarios"]:
            self.stats["daily_stats"][today]["scenarios"][scenario] = 0
        self.stats["daily_stats"][today]["scenarios"][scenario] += 1
        
        # 更新总场景统计
        if scenario not in self.stats["scenarios"]:
            self.stats["scenarios"][scenario] = 0
        self.stats["scenarios"][scenario] += 1
        
        # 更新最后使用日期
        self.stats["last_use_date"] = datetime.now().strftime("%Y-%m-%d")
        
        self._save_stats()
    
    def record_suggestion_adoption(self, adopted: bool):
        """
        记录建议采纳情况
        
        Args:
            adopted: 是否采纳建议
        """
        if adopted:
            self.stats["adopted_suggestions"] += 1
        else:
            self.stats["rejected_suggestions"] += 1
        
        self._save_stats()
    
    def record_learning_time(self, minutes: int):
        """
        记录学习时间
        
        Args:
            minutes: 学习时间（分钟）
        """
        self.stats["learning_time"] += minutes
        self._save_stats()
    
    def record_tip_shown(self):
        """记录显示了一条小贴士"""
        self.stats["tips_shown"] += 1
        self._save_stats()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取使用总结
        
        Returns:
            包含各种统计数据的字典
        """
        total_suggestions = self.stats["adopted_suggestions"] + self.stats["rejected_suggestions"]
        adoption_rate = 0
        if total_suggestions > 0:
            adoption_rate = (self.stats["adopted_suggestions"] / total_suggestions) * 100
        
        # 计算使用天数
        first_date = datetime.strptime(self.stats["first_use_date"], "%Y-%m-%d")
        last_date = datetime.strptime(self.stats["last_use_date"], "%Y-%m-%d")
        usage_days = (last_date - first_date).days + 1
        
        # 计算平均每日使用次数
        avg_daily_calls = 0
        if usage_days > 0:
            avg_daily_calls = self.stats["total_calls"] / usage_days
        
        # 获取最常用的场景
        top_scenarios = sorted(
            self.stats["scenarios"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # 获取最近7天的使用趋势
        recent_7_days = self._get_recent_7_days_stats()
        
        return {
            "total_calls": self.stats["total_calls"],
            "usage_days": usage_days,
            "avg_daily_calls": round(avg_daily_calls, 1),
            "adoption_rate": round(adoption_rate, 1),
            "adopted_suggestions": self.stats["adopted_suggestions"],
            "rejected_suggestions": self.stats["rejected_suggestions"],
            "top_scenarios": top_scenarios,
            "learning_time": self.stats["learning_time"],
            "tips_shown": self.stats["tips_shown"],
            "recent_7_days": recent_7_days,
            "first_use_date": self.stats["first_use_date"],
            "last_use_date": self.stats["last_use_date"],
        }
    
    def _get_recent_7_days_stats(self) -> List[Dict]:
        """获取最近7天的使用统计"""
        recent_stats = []
        today = datetime.now()
        
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            day_stats = self.stats["daily_stats"].get(date, {"count": 0})
            recent_stats.append({
                "date": date,
                "count": day_stats["count"]
            })
        
        return recent_stats
    
    def get_weekly_report(self) -> str:
        """
        生成周报告
        
        Returns:
            周报告文本
        """
        summary = self.get_summary()
        
        report = f"""
📊 本周 AI 使用报告

📅 统计周期：{summary['first_use_date']} 至 {summary['last_use_date']}

📈 使用概况：
• 总使用次数：{summary['total_calls']} 次
• 使用天数：{summary['usage_days']} 天
• 平均每日：{summary['avg_daily_calls']} 次

💡 建议采纳情况：
• 采纳建议：{summary['adopted_suggestions']} 次
• 未采纳：{summary['rejected_suggestions']} 次
• 采纳率：{summary['adoption_rate']}%

🎯 最常用场景：
"""
        
        for i, (scenario, count) in enumerate(summary['top_scenarios'][:3], 1):
            scenario_names = {
                "task_analysis": "任务分析",
                "priority_adjustment": "优先级调整",
                "study_plan": "学习计划",
                "time_estimation": "时间估算",
                "general": "一般咨询"
            }
            name = scenario_names.get(scenario, scenario)
            report += f"  {i}. {name}：{count} 次\n"
        
        report += f"""
📚 学习情况：
• 学习时间：{summary['learning_time']} 分钟
• 学习小贴士：{summary['tips_shown']} 条

💡 反思建议：
"""
        
        # 根据使用情况给出建议
        if summary['adoption_rate'] > 90:
            report += "• 你的采纳率很高，说明 AI 建议很有帮助！\n"
            report += "• 建议：保持批判性思维，不要完全依赖 AI。\n"
        elif summary['adoption_rate'] > 70:
            report += "• 你的采纳率适中，说明你会理性判断 AI 建议。\n"
            report += "• 建议：继续保持，多思考 AI 的局限性。\n"
        else:
            report += "• 你的采纳率较低，说明你有很强的独立思考能力！\n"
            report += "• 建议：可以适当参考 AI 建议，但要坚持自己的判断。\n"
        
        if summary['avg_daily_calls'] > 20:
            report += "• 你使用 AI 很频繁，记得保持独立思考能力。\n"
        elif summary['avg_daily_calls'] > 10:
            report += "• 你的 AI 使用频率适中，继续保持！\n"
        else:
            report += "• 你使用 AI 较少，可以尝试更多功能。\n"
        
        report += "\n✨ 继续保持，智能向善，理性使用！"
        
        return report


class AITipManager:
    """AI 学习小贴士管理器"""
    
    def __init__(self):
        self.tips = [
            {
                "category": "ai_ability",
                "title": "AI 能做什么？",
                "content": "AI 可以帮助你分析任务优先级、制定学习计划、估算时间。它擅长处理结构化、逻辑性强的问题。",
                "example": "✅ 适合：'帮我分析这些作业的优先级'"
            },
            {
                "category": "ai_limitation",
                "title": "AI 不能做什么？",
                "content": "AI 不了解你的实际学习状态、个人偏好、突发情况。它不能做道德判断，也不应该处理隐私信息。",
                "example": "❌ 不适合：'我该不该告诉老师这件事？'"
            },
            {
                "category": "privacy",
                "title": "保护隐私很重要！",
                "content": "不要向 AI 发送密码、账号、身份证号等敏感信息。我的软件会自动检测并阻止敏感信息。",
                "example": "🔒 安全：软件会自动保护你的隐私"
            },
            {
                "category": "critical_thinking",
                "title": "批判性思维",
                "content": "不要盲目相信 AI 的建议。每次看到 AI 建议，都要问自己：'这适合我的情况吗？'、'有什么我不知道的信息？'",
                "example": "💡 建议：点击'AI 局限性说明'了解更多"
            },
            {
                "category": "ai_bias",
                "title": "AI 可能有偏见",
                "content": "AI 的训练数据可能包含偏见，所以它的建议可能不公平。例如，它可能对某些学科有偏好。",
                "example": "⚠️ 注意：AI 可能对紧急任务有偏好"
            },
            {
                "category": "verify",
                "title": "验证 AI 的建议",
                "content": "重要决策前，要验证 AI 的建议。可以查资料、问老师、和家长讨论，不要只依赖 AI。",
                "example": "✓ 方法：多渠道验证重要信息"
            },
            {
                "category": "learning",
                "title": "AI 是学习工具",
                "content": "把 AI 当作学习助手，而不是答案机器。用它来启发思考，而不是直接复制答案。",
                "example": "📚 正确用法：'帮我理解这个概念'"
            },
            {
                "category": "responsibility",
                "title": "社会责任",
                "content": "使用 AI 时要考虑社会影响。不要用 AI 做不道德的事，不要传播虚假信息。",
                "example": "🌟 原则：智能向善，理性使用"
            },
            {
                "category": "future",
                "title": "未来已来",
                "content": "AI 技术正在快速发展。学会正确使用 AI，是未来社会的重要技能。保持学习，保持好奇！",
                "example": "🚀 目标：培养 AI 素养"
            },
            {
                "category": "balance",
                "title": "保持平衡",
                "content": "AI 是工具，不是生活的全部。记得多运动、多和朋友交流、多体验真实世界。",
                "example": "⚖️ 建议：合理使用 AI，享受真实生活"
            }
        ]
        self.shown_tips = set()
        self.tips_file = "shown_tips.json"
        self._load_shown_tips()
    
    def _load_shown_tips(self):
        """加载已显示的小贴士"""
        if os.path.exists(self.tips_file):
            try:
                with open(self.tips_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.shown_tips = set(data.get("shown_tips", []))
            except:
                pass
    
    def _save_shown_tips(self):
        """保存已显示的小贴士"""
        try:
            with open(self.tips_file, 'w', encoding='utf-8') as f:
                json.dump({"shown_tips": list(self.shown_tips)}, f)
        except:
            pass
    
    def get_random_tip(self) -> Dict[str, str]:
        """
        获取一条随机小贴士
        
        Returns:
            小贴士字典
        """
        import random
        
        # 优先显示未看过的
        unshown = [i for i in range(len(self.tips)) if i not in self.shown_tips]
        
        if unshown:
            idx = random.choice(unshown)
        else:
            idx = random.randint(0, len(self.tips) - 1)
        
        tip = self.tips[idx]
        self.shown_tips.add(idx)
        self._save_shown_tips()
        
        return tip
    
    def get_tip_by_category(self, category: str) -> Dict[str, str]:
        """
        根据分类获取小贴士
        
        Args:
            category: 分类名称
        
        Returns:
            小贴士字典
        """
        for tip in self.tips:
            if tip["category"] == category:
                return tip
        
        return self.get_random_tip()
