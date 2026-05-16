"""
AI 伦理与局限性展示模块
- AI 决策解释
- 局限性提示
- 隐私保护
- AI 置信度评估
- 伦理提醒
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class AIEthicsAnalyzer:
    """AI 伦理分析器"""
    
    # AI 局限性模板
    LIMITATIONS = {
        "priority_adjustment": {
            "limitation": "AI 不了解你的实际学习进度和个人情况",
            "suggestion": "建议结合自己的实际情况判断",
            "alternatives": ["手动调整优先级", "重新评估任务重要性"]
        },
        "task_decomposition": {
            "limitation": "AI 可能无法完全理解任务的复杂性",
            "suggestion": "建议根据自己的能力调整分解方式",
            "alternatives": ["手动调整任务步骤", "咨询老师或同学"]
        },
        "time_estimation": {
            "limitation": "AI 的时间估算基于一般情况，可能不准确",
            "suggestion": "建议根据自己的实际速度调整",
            "alternatives": ["记录实际用时", "逐步优化估算"]
        },
        "study_plan": {
            "limitation": "AI 不了解你的学习风格和偏好",
            "suggestion": "建议根据自己的学习习惯调整",
            "alternatives": ["尝试不同的学习方法", "咨询学习顾问"]
        }
    }
    
    # 敏感场景检测
    SENSITIVE_SCENARIOS = {
        "privacy": ["密码", "账号", "身份证", "银行卡", "手机号"],
        "safety": ["紧急", "危险", "报警", "求助"],
        "moral": ["作弊", "抄袭", "代写", "考试答案"],
        "health": ["疾病", "症状", "药物", "治疗"]
    }
    
    # AI 适用场景
    AI_SUITABLE_SCENARIOS = [
        "任务优先级分析",
        "时间管理建议",
        "学习计划制定",
        "信息整理总结",
        "任务分解建议"
    ]
    
    # AI 不适用场景
    AI_UNSUITABLE_SCENARIOS = [
        "涉及个人隐私的决策",
        "紧急情况处理",
        "道德判断",
        "重要考试答案",
        "医疗健康建议"
    ]
    
    def __init__(self):
        self.decision_history = []
    
    def explain_decision(self, decision_type: str, decision_data: Dict) -> Dict[str, Any]:
        """
        解释 AI 决策的原因
        
        Args:
            decision_type: 决策类型（如 "priority_adjustment"）
            decision_data: 决策数据
            
        Returns:
            包含解释、局限性、建议的字典
        """
        limitation_info = self.LIMITATIONS.get(decision_type, {})
        
        explanation = {
            "decision_type": decision_type,
            "timestamp": datetime.now().isoformat(),
            "explanation": self._generate_explanation(decision_type, decision_data),
            "limitation": limitation_info.get("limitation", ""),
            "suggestion": limitation_info.get("suggestion", ""),
            "alternatives": limitation_info.get("alternatives", []),
            "confidence": self._calculate_confidence(decision_type, decision_data),
            "ethics_note": self._generate_ethics_note(decision_type)
        }
        
        # 记录决策历史
        self.decision_history.append(explanation)
        
        return explanation
    
    def _generate_explanation(self, decision_type: str, decision_data: Dict) -> str:
        """生成决策解释"""
        explanations = {
            "priority_adjustment": f"AI 根据任务截止时间（{decision_data.get('due_date', '未知')}）和重要性（{decision_data.get('importance', '未知')}）调整了优先级",
            "task_decomposition": f"AI 根据任务类型（{decision_data.get('task_type', '未知')}）和复杂度（{decision_data.get('complexity', '未知')}）提供了分解建议",
            "time_estimation": f"AI 基于任务类型和一般情况估算需要 {decision_data.get('estimated_time', '未知')} 分钟",
            "study_plan": f"AI 根据你的学习目标和时间安排制定了计划"
        }
        return explanations.get(decision_type, "AI 基于已有信息做出了建议")
    
    def _calculate_confidence(self, decision_type: str, decision_data: Dict) -> float:
        """
        计算 AI 决策的置信度
        
        Returns:
            置信度（0.0-1.0）
        """
        # 基础置信度
        base_confidence = {
            "priority_adjustment": 0.7,  # 优先级调整相对可靠
            "task_decomposition": 0.6,  # 任务分解需要人工判断
            "time_estimation": 0.5,     # 时间估算不太准确
            "study_plan": 0.6           # 学习计划需要个性化
        }
        
        confidence = base_confidence.get(decision_type, 0.5)
        
        # 根据数据完整性调整
        if decision_data.get("has_due_date"):
            confidence += 0.1
        if decision_data.get("has_importance"):
            confidence += 0.1
        if decision_data.get("user_feedback"):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_ethics_note(self, decision_type: str) -> str:
        """生成伦理提醒"""
        notes = {
            "priority_adjustment": "确保优先级调整不会影响其他重要任务或休息时间",
            "task_decomposition": "任务分解应合理，避免过度压力",
            "time_estimation": "时间估算仅供参考，实际用时可能因个人情况而异",
            "study_plan": "学习计划应平衡学习和休息，避免过度疲劳"
        }
        return notes.get(decision_type, "")
    
    def check_sensitive_scenario(self, user_input: str) -> Dict[str, Any]:
        """
        检测敏感场景
        
        Args:
            user_input: 用户输入
            
        Returns:
            敏感场景检测结果
        """
        detected = []
        
        for scenario_type, keywords in self.SENSITIVE_SCENARIOS.items():
            if any(keyword in user_input for keyword in keywords):
                detected.append({
                    "type": scenario_type,
                    "keywords": [kw for kw in keywords if kw in user_input],
                    "recommendation": self._get_recommendation(scenario_type)
                })
        
        return {
            "is_sensitive": len(detected) > 0,
            "detected_scenarios": detected,
            "ai_suitable": len(detected) == 0,
            "warning": "检测到敏感信息，建议谨慎使用 AI" if detected else ""
        }
    
    def _get_recommendation(self, scenario_type: str) -> str:
        """获取场景推荐"""
        recommendations = {
            "privacy": "涉及隐私信息，建议手动处理，不要交给 AI",
            "safety": "紧急情况请直接联系相关部门或人员，不要依赖 AI",
            "moral": "涉及道德问题，请遵循诚信原则，AI 不应参与",
            "health": "健康问题请咨询专业医生，AI 无法提供医疗建议"
        }
        return recommendations.get(scenario_type, "")
    
    def get_ai_usage_guide(self, scenario: str = None) -> Dict[str, Any]:
        """
        获取 AI 使用指南
        
        Args:
            scenario: 具体场景（可选）
            
        Returns:
            使用指南
        """
        guide = {
            "suitable_scenarios": self.AI_SUITABLE_SCENARIOS,
            "unsuitable_scenarios": self.AI_UNSUITABLE_SCENARIOS,
            "best_practices": [
                "将 AI 作为辅助工具，而非决策者",
                "重要决策需要人工确认",
                "验证 AI 提供的信息",
                "保护个人隐私，避免输入敏感信息",
                "理解 AI 的局限性，合理使用"
            ],
            "ethics_principles": [
                "透明性：了解 AI 如何做出决策",
                "可控性：用户可以随时干预或拒绝 AI 建议",
                "隐私保护：AI 不应收集或泄露个人隐私",
                "公平性：AI 不应有偏见或歧视",
                "责任性：最终决策权在用户手中"
            ]
        }
        
        if scenario:
            guide["scenario_specific"] = self._get_scenario_advice(scenario)
        
        return guide
    
    def _get_scenario_advice(self, scenario: str) -> Dict[str, Any]:
        """获取特定场景的建议"""
        # 这里可以根据具体场景提供更详细的建议
        return {
            "scenario": scenario,
            "ai_role": "辅助建议",
            "user_role": "最终决策",
            "notes": "请根据自己的实际情况调整 AI 建议"
        }
    
    def get_decision_history(self, limit: int = 10) -> List[Dict]:
        """获取决策历史"""
        return self.decision_history[-limit:]
    
    def export_ethics_report(self) -> Dict[str, Any]:
        """导出伦理报告"""
        return {
            "total_decisions": len(self.decision_history),
            "decision_types": list(set(d["decision_type"] for d in self.decision_history)),
            "average_confidence": sum(d["confidence"] for d in self.decision_history) / len(self.decision_history) if self.decision_history else 0,
            "recent_decisions": self.get_decision_history(5),
            "generated_at": datetime.now().isoformat()
        }


class AIEthicsWidget:
    """AI 伦理展示组件（用于 UI 集成）"""
    
    @staticmethod
    def format_limitation_warning(explanation: Dict) -> str:
        """格式化局限性警告（用于 UI 显示）"""
        warning = f"""
⚠️ AI 局限性说明：

{explanation['limitation']}

💡 建议：{explanation['suggestion']}

🔄 替代方案：
"""
        for i, alt in enumerate(explanation['alternatives'], 1):
            warning += f"  {i}. {alt}\n"
        
        warning += f"\n📊 AI 置信度：{explanation['confidence']:.0%}"
        
        if explanation['ethics_note']:
            warning += f"\n\n⚖️ 伦理提醒：{explanation['ethics_note']}"
        
        return warning
    
    @staticmethod
    def format_sensitive_warning(check_result: Dict) -> str:
        """格式化敏感场景警告"""
        if not check_result['is_sensitive']:
            return ""
        
        warning = "🚨 检测到敏感信息！\n\n"
        
        for scenario in check_result['detected_scenarios']:
            warning += f"类型：{scenario['type']}\n"
            warning += f"关键词：{', '.join(scenario['keywords'])}\n"
            warning += f"建议：{scenario['recommendation']}\n\n"
        
        warning += "⚠️ 建议：不要将此类信息交给 AI 处理"
        
        return warning
    
    @staticmethod
    def format_usage_guide() -> str:
        """格式化使用指南"""
        guide = """
📚 AI 使用指南

✅ 适合使用 AI 的场景：
"""
        for scenario in AIEthicsAnalyzer.AI_SUITABLE_SCENARIOS:
            guide += f"  • {scenario}\n"
        
        guide += "\n❌ 不适合使用 AI 的场景：\n"
        for scenario in AIEthicsAnalyzer.AI_UNSUITABLE_SCENARIOS:
            guide += f"  • {scenario}\n"
        
        guide += "\n💡 最佳实践：\n"
        guide += "  1. 将 AI 作为辅助工具，而非决策者\n"
        guide += "  2. 重要决策需要人工确认\n"
        guide += "  3. 验证 AI 提供的信息\n"
        guide += "  4. 保护个人隐私\n"
        
        return guide


# 使用示例
if __name__ == "__main__":
    analyzer = AIEthicsAnalyzer()
    
    # 示例 1：解释 AI 决策
    decision = analyzer.explain_decision(
        "priority_adjustment",
        {
            "due_date": "明天",
            "importance": "高",
            "has_due_date": True,
            "has_importance": True
        }
    )
    
    print("AI 决策解释：")
    print(AIEthicsWidget.format_limitation_warning(decision))
    
    # 示例 2：检测敏感场景
    check = analyzer.check_sensitive_scenario("我的密码是123456")
    print("\n" + "="*50)
    print("敏感场景检测：")
    print(AIEthicsWidget.format_sensitive_warning(check))
    
    # 示例 3：使用指南
    print("\n" + "="*50)
    print(AIEthicsWidget.format_usage_guide())
