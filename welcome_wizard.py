"""
快速入门教程
帮助新用户了解软件功能和正确使用 AI
"""

from PyQt5.QtWidgets import (
    QWizard, QWizardPage, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QGroupBox, QTextBrowser
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon
import os
from utils import get_data_path


class WelcomeWizard(QWizard):
    """欢迎向导"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 MT Time Assistant - 快速入门")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.HaveHelpButton, False)
        self.setOption(QWizard.CancelButtonOnLeft, True)
        
        # 设置窗口大小
        self.resize(600, 500)
        
        # 添加页面
        self.addPage(WelcomePage())
        self.addPage(FeaturesPage())
        self.addPage(AIEthicsPage())
        self.addPage(UsageGuidePage())
        self.addPage(GetStartedPage())
        
        # 设置按钮文本
        self.setButtonText(QWizard.NextButton, "下一步 ➡️")
        self.setButtonText(QWizard.BackButton, "⬅️ 上一步")
        self.setButtonText(QWizard.FinishButton, "开始使用 🚀")
        self.setButtonText(QWizard.CancelButton, "跳过")
        
        # 样式
        self.setStyleSheet("""
            QWizard {
                background-color: white;
            }
            QWizardPage {
                background-color: white;
                padding: 20px;
            }
            QLabel {
                color: #333;
            }
            QGroupBox {
                font-weight: bold;
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


class WelcomePage(QWizardPage):
    """欢迎页面"""

    def __init__(self):
        super().__init__()
        self.setTitle("欢迎使用 MT Time Assistant！")

        layout = QVBoxLayout(self)
        layout.setSpacing(25)

        # 欢迎信息
        welcome_label = QLabel(
            "🎉 欢迎使用 MT Time Assistant！\n\n"
            "一个智能时间管理助手，帮助你高效管理学习和任务。"
        )
        welcome_label.setFont(QFont("Microsoft YaHei", 13))
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("color: #333;")
        layout.addWidget(welcome_label)

        # 核心特点
        features_label = QLabel(
            "✨ 核心功能：\n"
            "   🤖 AI 智能分析   📋 任务管理   🍅 番茄钟"
        )
        features_label.setFont(QFont("Microsoft YaHei", 12))
        features_label.setStyleSheet("color: #555; padding: 10px;")
        layout.addWidget(features_label)

        layout.addStretch()


class FeaturesPage(QWizardPage):
    """功能介绍页面"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("主要功能介绍")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 任务管理
        task_group = QGroupBox("📋 任务管理")
        task_layout = QVBoxLayout(task_group)
        task_layout.addWidget(QLabel("• 添加、编辑、删除任务"))
        task_layout.addWidget(QLabel("• 设置截止时间和重要性"))
        task_layout.addWidget(QLabel("• 拖拽排序任务优先级"))
        layout.addWidget(task_group)
        
        # AI 智能分析
        ai_group = QGroupBox("🤖 AI 智能分析")
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.addWidget(QLabel("• 智能分析任务优先级"))
        ai_layout.addWidget(QLabel("• 自动分解复杂任务"))
        ai_layout.addWidget(QLabel("• 提供学习建议"))
        layout.addWidget(ai_group)
        
        # 记忆系统
        memory_group = QGroupBox("🧠 记忆系统")
        memory_layout = QVBoxLayout(memory_group)
        memory_layout.addWidget(QLabel("• 短期记忆：记住最近的对话"))
        memory_layout.addWidget(QLabel("• 长期记忆：记住重要信息"))
        memory_layout.addWidget(QLabel("• 帮助 AI 更好地理解你"))
        layout.addWidget(memory_group)
        
        # 番茄钟
        pomodoro_group = QGroupBox("🍅 番茄钟")
        pomodoro_layout = QVBoxLayout(pomodoro_group)
        pomodoro_layout.addWidget(QLabel("• 25 分钟专注学习"))
        pomodoro_layout.addWidget(QLabel("• 5 分钟休息"))
        pomodoro_layout.addWidget(QLabel("• 提高学习效率"))
        layout.addWidget(pomodoro_group)


class AIEthicsPage(QWizardPage):
    """AI 伦理教育页面"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("⚠️ 重要：AI 伦理与使用规范")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # AI 能做什么
        can_group = QGroupBox("✅ AI 能做什么")
        can_layout = QVBoxLayout(can_group)
        can_items = [
            "• 分析任务优先级",
            "• 制定学习计划",
            "• 估算时间",
            "• 提供建议"
        ]
        for item in can_items:
            can_layout.addWidget(QLabel(item))
        layout.addWidget(can_group)
        
        # AI 不能做什么
        cannot_group = QGroupBox("❌ AI 不能做什么")
        cannot_layout = QVBoxLayout(cannot_group)
        cannot_items = [
            "• 了解你的实际学习状态",
            "• 做道德判断",
            "• 处理隐私信息（密码、账号等）",
            "• 替代你的独立思考"
        ]
        for item in cannot_items:
            cannot_layout.addWidget(QLabel(item))
        layout.addWidget(cannot_group)
        
        # 重要提醒
        warning_label = QLabel(
            "⚠️ 重要提醒：\n"
            "1. 不要向 AI 发送密码、账号等敏感信息\n"
            "2. 不要盲目相信 AI 的建议，要结合实际情况判断\n"
            "3. 重要决策要多方验证，不要只依赖 AI\n"
            "4. 保持批判性思维，理性使用 AI"
        )
        warning_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        warning_label.setStyleSheet("""
            background-color: #FFF3E0;
            color: #F57C00;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #FFB74D;
        """)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)


class UsageGuidePage(QWizardPage):
    """使用指南页面"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("如何正确使用 AI")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 使用步骤
        steps_group = QGroupBox("📝 使用步骤")
        steps_layout = QVBoxLayout(steps_group)
        
        steps = [
            "1️⃣ 输入你的问题或任务",
            "2️⃣ AI 会分析并给出建议",
            "3️⃣ 点击'⚠️ AI 局限性说明'了解详情",
            "4️⃣ 结合实际情况判断是否采纳",
            "5️⃣ 做出最终决策"
        ]
        
        for step in steps:
            label = QLabel(step)
            label.setFont(QFont("Microsoft YaHei", 11))
            label.setStyleSheet("color: #333; padding: 5px;")
            steps_layout.addWidget(label)
        
        layout.addWidget(steps_group)
        
        # 最佳实践
        best_group = QGroupBox("💡 最佳实践")
        best_layout = QVBoxLayout(best_group)
        
        best_items = [
            "✓ 明确描述你的问题",
            "✓ 提供必要的上下文信息",
            "✓ 查看 AI 局限性说明",
            "✓ 结合自己的情况判断",
            "✓ 保持批判性思维"
        ]
        
        for item in best_items:
            label = QLabel(item)
            label.setFont(QFont("Microsoft YaHei", 11))
            label.setStyleSheet("color: #4CAF50; padding: 3px;")
            best_layout.addWidget(label)
        
        layout.addWidget(best_group)
        
        # 示例
        example_label = QLabel(
            "📌 示例：\n"
            "你：'我今天有很多作业，应该先做什么？'\n"
            "AI：'建议先做数学作业，因为明天截止...'\n"
            "你：点击'AI 局限性说明'\n"
            "系统：'AI 不知道你今天的实际学习状态...'\n"
            "你：结合自己的情况做出最终决定"
        )
        example_label.setFont(QFont("Microsoft YaHei", 10))
        example_label.setStyleSheet("""
            background-color: #E3F2FD;
            color: #1976D2;
            padding: 10px;
            border-radius: 5px;
        """)
        example_label.setWordWrap(True)
        layout.addWidget(example_label)


class GetStartedPage(QWizardPage):
    """开始使用页面"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("准备开始！")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 准备就绪
        ready_label = QLabel(
            "🎉 太棒了！你已经了解了软件的基本功能和正确使用 AI 的方法。\n\n"
            "记住：智能向善，理性使用！"
        )
        ready_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        ready_label.setStyleSheet("color: #4CAF50;")
        ready_label.setWordWrap(True)
        layout.addWidget(ready_label)
        
        # 快速开始指南
        guide_group = QGroupBox("🚀 快速开始")
        guide_layout = QVBoxLayout(guide_group)
        
        guide_items = [
            "1. 在左侧添加你的任务",
            "2. 点击任务卡片上的'AI 分析'按钮",
            "3. 在右侧聊天框与 AI 交流",
            "4. 查看'AI 局限性说明'了解详情",
            "5. 使用番茄钟提高学习效率"
        ]
        
        for item in guide_items:
            label = QLabel(item)
            label.setFont(QFont("Microsoft YaHei", 11))
            label.setStyleSheet("color: #333; padding: 5px;")
            guide_layout.addWidget(label)
        
        layout.addWidget(guide_group)
        
        # 帮助提示
        help_label = QLabel(
            "💡 小贴士：\n"
            "• 随时可以查看'AI 使用统计'了解你的使用情况\n"
            "• 每天会显示一条'AI 学习小贴士'\n"
            "• 有问题可以随时询问 AI"
        )
        help_label.setFont(QFont("Microsoft YaHei", 10))
        help_label.setStyleSheet("""
            background-color: #FFF9C4;
            color: #F57F17;
            padding: 10px;
            border-radius: 5px;
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        # 确认复选框
        self.confirm_checkbox = QCheckBox("我已经了解如何正确使用 AI")
        self.confirm_checkbox.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        self.confirm_checkbox.setStyleSheet("color: #1976D2;")
        layout.addWidget(self.confirm_checkbox)
        
        # 注册字段
        self.registerField("confirm*", self.confirm_checkbox)


def show_welcome_wizard(parent=None) -> bool:
    """
    显示欢迎向导
    
    Returns:
        True 如果用户完成了向导，False 如果用户跳过
    """
    wizard = WelcomeWizard(parent)
    result = wizard.exec_()
    return result == WelcomeWizard.Accepted


def should_show_wizard() -> bool:
    """
    判断是否应该显示欢迎向导

    Returns:
        True 如果应该显示，False 如果已经显示过
    """
    # 使用绝对路径，确保开机自启动时也能正确读取
    config_file = get_data_path("welcome_shown.txt")

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content != "true"
        except:
            return True

    return True


def mark_wizard_shown():
    """标记欢迎向导已经显示过"""
    # 使用绝对路径
    config_file = get_data_path("welcome_shown.txt")
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("true")
    except:
        pass
