"""
AI 使用统计面板组件
展示 AI 使用情况和学习报告
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QFrame, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from ai_usage_stats import AIUsageStats, AITipManager


class AIStatsWidget(QWidget):
    """AI 使用统计面板"""
    
    def __init__(self, stats_manager: AIUsageStats, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.tip_manager = AITipManager()
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("📊 AI 使用统计")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1976D2;")
        layout.addWidget(title)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新数据")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        layout.addWidget(refresh_btn)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # 概览卡片
        overview_group = self._create_overview_group()
        scroll_layout.addWidget(overview_group)
        
        # 建议采纳情况
        adoption_group = self._create_adoption_group()
        scroll_layout.addWidget(adoption_group)
        
        # 最常用场景
        scenarios_group = self._create_scenarios_group()
        scroll_layout.addWidget(scenarios_group)
        
        # 学习情况
        learning_group = self._create_learning_group()
        scroll_layout.addWidget(learning_group)
        
        # 最近7天趋势
        trend_group = self._create_trend_group()
        scroll_layout.addWidget(trend_group)
        
        # 周报告按钮
        report_btn = QPushButton("📄 查看周报告")
        report_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        report_btn.clicked.connect(self.show_weekly_report)
        scroll_layout.addWidget(report_btn)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def _create_overview_group(self) -> QGroupBox:
        """创建概览卡片"""
        group = QGroupBox("📈 使用概览")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QHBoxLayout(group)
        
        summary = self.stats_manager.get_summary()
        
        # 总使用次数
        total_card = self._create_stat_card(
            "🎯 总使用次数",
            f"{summary['total_calls']} 次",
            "#2196F3"
        )
        layout.addWidget(total_card)
        
        # 使用天数
        days_card = self._create_stat_card(
            "📅 使用天数",
            f"{summary['usage_days']} 天",
            "#4CAF50"
        )
        layout.addWidget(days_card)
        
        # 平均每日
        avg_card = self._create_stat_card(
            "📊 平均每日",
            f"{summary['avg_daily_calls']} 次",
            "#FF9800"
        )
        layout.addWidget(avg_card)
        
        return group
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 11))
        title_label.setStyleSheet(f"color: {color};")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        value_label.setStyleSheet("color: #333;")
        layout.addWidget(value_label)
        
        return card
    
    def _create_adoption_group(self) -> QGroupBox:
        """创建建议采纳情况卡片"""
        group = QGroupBox("💡 建议采纳情况")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        summary = self.stats_manager.get_summary()
        
        # 采纳率标题行
        rate_header = QHBoxLayout()
        rate_label = QLabel(f"采纳率：{summary['adoption_rate']}%")
        rate_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        rate_label.setStyleSheet("color: #4CAF50;")
        rate_header.addWidget(rate_label)
        
        # 添加解释按钮
        help_btn = QPushButton("❓")
        help_btn.setFixedSize(24, 24)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #E3F2FD;
                color: #1976D2;
                border: 1px solid #1976D2;
                border-radius: 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
        """)
        help_btn.setToolTip("点击查看采纳率计算说明")
        help_btn.clicked.connect(self._show_adoption_rate_explanation)
        rate_header.addWidget(help_btn)
        rate_header.addStretch()
        
        layout.addLayout(rate_header)
        
        # 详细数据
        details = QLabel(
            f"✅ 采纳建议：{summary['adopted_suggestions']} 次\n"
            f"❌ 未采纳：{summary['rejected_suggestions']} 次"
        )
        details.setFont(QFont("Microsoft YaHei", 12))
        details.setStyleSheet("color: #666;")
        layout.addWidget(details)
        
        # 评价
        if summary['adoption_rate'] > 90:
            comment = "🌟 采纳率很高，说明 AI 建议很有帮助！"
        elif summary['adoption_rate'] > 70:
            comment = "👍 采纳率适中，说明你会理性判断 AI 建议。"
        else:
            comment = "💪 采纳率较低，说明你有很强的独立思考能力！"
        
        comment_label = QLabel(comment)
        comment_label.setFont(QFont("Microsoft YaHei", 11))
        comment_label.setStyleSheet("color: #FF9800;")
        comment_label.setWordWrap(True)
        layout.addWidget(comment_label)
        
        return group
    
    def _show_adoption_rate_explanation(self):
        """显示采纳率计算说明"""
        explanation = """
📊 采纳率计算说明

【计算公式】
采纳率 = (采纳的建议数 / 总建议数) × 100%

【数据来源】
• 采纳建议：你点击"采纳"按钮的次数
• 未采纳：你点击"忽略"按钮的次数
• 总建议数：采纳 + 未采纳的总和

【如何记录】
在 AI 给出建议后，你可以：
1. 点击"✅ 采纳"按钮 - 表示你接受了 AI 的建议
2. 点击"❌ 忽略"按钮 - 表示你决定不采纳 AI 的建议

【重要说明】
• 采纳率不是越高越好！
• 适中（70-90%）表示你会理性判断 AI 建议
• 较低（<70%）说明你有很强的独立思考能力
• 较高（>90%）说明 AI 建议很有帮助

【设计理念】
这个功能帮助你反思如何更好地使用 AI：
• 不要盲目相信 AI
• 保持批判性思维
• 结合实际情况判断
• 理性使用 AI 工具

💡 记住：智能向善，理性使用！
        """
        
        QMessageBox.information(
            self,
            "📊 采纳率计算说明",
            explanation
        )
    
    def _create_scenarios_group(self) -> QGroupBox:
        """创建最常用场景卡片"""
        group = QGroupBox("🎯 最常用场景")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        summary = self.stats_manager.get_summary()
        
        scenario_names = {
            "task_analysis": "任务分析",
            "priority_adjustment": "优先级调整",
            "study_plan": "学习计划",
            "time_estimation": "时间估算",
            "general": "一般咨询"
        }
        
        for i, (scenario, count) in enumerate(summary['top_scenarios'][:5], 1):
            name = scenario_names.get(scenario, scenario)
            label = QLabel(f"{i}. {name}：{count} 次")
            label.setFont(QFont("Microsoft YaHei", 12))
            label.setStyleSheet("color: #333;")
            layout.addWidget(label)
        
        return group
    
    def _create_learning_group(self) -> QGroupBox:
        """创建学习情况卡片"""
        group = QGroupBox("📚 学习情况")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        summary = self.stats_manager.get_summary()
        
        # 学习时间
        time_label = QLabel(f"⏱️ 学习时间：{summary['learning_time']} 分钟")
        time_label.setFont(QFont("Microsoft YaHei", 12))
        time_label.setStyleSheet("color: #333;")
        layout.addWidget(time_label)
        
        # 小贴士
        tips_label = QLabel(f"💡 学习小贴士：{summary['tips_shown']} 条")
        tips_label.setFont(QFont("Microsoft YaHei", 12))
        tips_label.setStyleSheet("color: #333;")
        layout.addWidget(tips_label)
        
        return group
    
    def _create_trend_group(self) -> QGroupBox:
        """创建最近7天趋势卡片"""
        group = QGroupBox("📈 最近7天使用趋势")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        summary = self.stats_manager.get_summary()
        
        # 简单的文本展示（可以用图表库优化）
        for day_stat in summary['recent_7_days']:
            date_str = day_stat['date']
            count = day_stat['count']
            
            # 日期格式化
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
            
            # 创建进度条效果
            bar_length = min(count, 20)  # 最多显示20个方块
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            label = QLabel(f"{date_str} ({weekday}): {bar} {count} 次")
            label.setFont(QFont("Consolas", 10))
            label.setStyleSheet("color: #333;")
            layout.addWidget(label)
        
        return group
    
    def _on_refresh_clicked(self):
        """刷新按钮点击事件"""
        # 重新加载统计数据
        self.stats_manager.stats = self.stats_manager._load_stats()
        
        # 显示提示
        QMessageBox.information(
            self, 
            "✅ 刷新成功", 
            "统计数据已更新！\n\n请关闭此窗口后重新打开查看最新数据。"
        )
        
        # 关闭父对话框
        parent_dialog = self.parent()
        while parent_dialog and not isinstance(parent_dialog, QDialog):
            parent_dialog = parent_dialog.parent()
        
        if parent_dialog:
            parent_dialog.close()
    
    def show_weekly_report(self):
        """显示周报告"""
        report = self.stats_manager.get_weekly_report()
        
        msg = QMessageBox(self)
        msg.setWindowTitle("📊 周报告")
        msg.setText(report)
        msg.setStyleSheet("""
            QMessageBox {
                font-size: 13px;
            }
        """)
        msg.exec_()


class AITipWidget(QWidget):
    """AI 学习小贴士组件"""
    
    tip_closed = pyqtSignal()
    
    def __init__(self, tip_manager: AITipManager, parent=None):
        super().__init__(parent)
        self.tip_manager = tip_manager
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 获取一条小贴士
        tip = self.tip_manager.get_random_tip()
        
        # 标题
        title = QLabel(f"💡 {tip['title']}")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setStyleSheet("color: #1976D2;")
        layout.addWidget(title)
        
        # 内容
        content = QLabel(tip['content'])
        content.setFont(QFont("Microsoft YaHei", 12))
        content.setStyleSheet("color: #333;")
        content.setWordWrap(True)
        layout.addWidget(content)
        
        # 示例
        example = QLabel(tip['example'])
        example.setFont(QFont("Microsoft YaHei", 11))
        example.setStyleSheet("color: #666; font-style: italic;")
        example.setWordWrap(True)
        layout.addWidget(example)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        next_btn = QPushButton("下一条 ➡️")
        next_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        next_btn.clicked.connect(self.show_next_tip)
        btn_layout.addWidget(next_btn)
        
        close_btn = QPushButton("关闭 ✖️")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # 整体样式
        self.setStyleSheet("""
            QWidget {
                background-color: #E3F2FD;
                border: 2px solid #2196F3;
                border-radius: 10px;
                padding: 15px;
            }
        """)
    
    def show_next_tip(self):
        """显示下一条小贴士"""
        # 清空当前布局
        layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 重新初始化界面
        self.init_ui()
    
    def close(self):
        """关闭小贴士"""
        self.tip_closed.emit()
        super().close()
