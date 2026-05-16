"""
成就激励系统
完成任务获得成就，增加使用动力
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QPushButton, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class Achievement:
    """成就类"""
    def __init__(self, achievement_id: str, name: str, description: str,
                 icon: str, condition_type: str, condition_value: int,
                 points: int = 10):
        self.id = achievement_id
        self.name = name
        self.description = description
        self.icon = icon
        self.condition_type = condition_type  # tasks_completed, streak_days, pomodoros, etc.
        self.condition_value = condition_value
        self.points = points
        self.unlocked = False
        self.unlocked_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "unlocked": self.unlocked,
            "unlocked_at": self.unlocked_at.strftime("%Y-%m-%d %H:%M:%S") if self.unlocked_at else None
        }


# 定义所有成就
ACHIEVEMENTS = {
    # 任务完成成就
    "first_task": Achievement("first_task", "初出茅庐", "完成第一个任务", "🌟", "tasks_completed", 1, 5),
    "task_10": Achievement("task_10", "小试牛刀", "累计完成10个任务", "⭐", "tasks_completed", 10, 15),
    "task_50": Achievement("task_50", "渐入佳境", "累计完成50个任务", "💫", "tasks_completed", 50, 30),
    "task_100": Achievement("task_100", "任务达人", "累计完成100个任务", "🏆", "tasks_completed", 100, 50),
    "task_500": Achievement("task_500", "任务大师", "累计完成500个任务", "👑", "tasks_completed", 500, 100),

    # 连续打卡成就
    "streak_3": Achievement("streak_3", "三天成习", "连续3天使用软件", "🔥", "streak_days", 3, 10),
    "streak_7": Achievement("streak_7", "周而复始", "连续7天使用软件", "💪", "streak_days", 7, 20),
    "streak_30": Achievement("streak_30", "月月坚持", "连续30天使用软件", "🏅", "streak_days", 30, 50),
    "streak_100": Achievement("streak_100", "百日筑基", "连续100天使用软件", "💎", "streak_days", 100, 100),

    # 番茄钟成就
    "pomodoro_10": Achievement("pomodoro_10", "番茄新手", "完成10个番茄钟", "🍅", "pomodoros", 10, 10),
    "pomodoro_50": Achievement("pomodoro_50", "番茄熟手", "完成50个番茄钟", "🍅", "pomodoros", 50, 25),
    "pomodoro_100": Achievement("pomodoro_100", "番茄达人", "完成100个番茄钟", "🍅", "pomodoros", 100, 40),
    "pomodoro_500": Achievement("pomodoro_500", "番茄大师", "完成500个番茄钟", "🍅", "pomodoros", 500, 80),

    # 专注时长成就
    "focus_1h": Achievement("focus_1h", "专注一小时", "累计专注1小时", "⏱️", "focus_minutes", 60, 10),
    "focus_10h": Achievement("focus_10h", "专注达人", "累计专注10小时", "⏱️", "focus_minutes", 600, 20),
    "focus_100h": Achievement("focus_100h", "专注大师", "累计专注100小时", "⏱️", "focus_minutes", 6000, 50),

    # 特殊成就
    "early_bird": Achievement("early_bird", "早起鸟儿", "早上6点前完成任务", "🐦", "special", 1, 15),
    "night_owl": Achievement("night_owl", "夜猫子", "晚上11点后完成任务", "🦉", "special", 1, 15),
    "ai_helper": Achievement("ai_helper", "AI助手", "使用AI分析100次", "🤖", "ai_calls", 100, 30),
}


class AchievementManager:
    """成就管理器"""

    def __init__(self, data_file: str = "achievements.json"):
        from utils import get_data_path
        self.data_file = get_data_path(data_file)
        self.achievements: Dict[str, Achievement] = {}
        self.stats = {
            "tasks_completed": 0,
            "streak_days": 0,
            "pomodoros": 0,
            "focus_minutes": 0,
            "ai_calls": 0,
            "last_active_date": None
        }
        self.total_points = 0
        self._init_achievements()
        self.load_data()

    def _init_achievements(self):
        """初始化成就"""
        for achievement_id, achievement in ACHIEVEMENTS.items():
            self.achievements[achievement_id] = Achievement(
                achievement.id, achievement.name, achievement.description,
                achievement.icon, achievement.condition_type, achievement.condition_value,
                achievement.points
            )

    def load_data(self):
        """加载数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 加载统计
                self.stats = data.get("stats", self.stats)
                if self.stats.get("last_active_date"):
                    self.stats["last_active_date"] = datetime.strptime(
                        self.stats["last_active_date"], "%Y-%m-%d"
                    ).date()

                # 加载成就状态
                for achievement_data in data.get("achievements", []):
                    achievement_id = achievement_data.get("id")
                    if achievement_id in self.achievements:
                        self.achievements[achievement_id].unlocked = achievement_data.get("unlocked", False)
                        if achievement_data.get("unlocked_at"):
                            self.achievements[achievement_id].unlocked_at = datetime.strptime(
                                achievement_data["unlocked_at"], "%Y-%m-%d %H:%M:%S"
                            )

                self._calculate_total_points()
            except Exception as e:
                print(f"加载成就数据失败: {e}")

    def save_data(self):
        """保存数据"""
        try:
            data = {
                "stats": {
                    **self.stats,
                    "last_active_date": self.stats["last_active_date"].strftime("%Y-%m-%d") if self.stats.get("last_active_date") else None
                },
                "achievements": [a.to_dict() for a in self.achievements.values()],
                "total_points": self.total_points
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存成就数据失败: {e}")

    def _calculate_total_points(self):
        """计算总积分"""
        self.total_points = sum(
            a.points for a in self.achievements.values() if a.unlocked
        )

    def record_task_completed(self) -> List[Achievement]:
        """记录任务完成，返回新解锁的成就"""
        new_unlocks = []
        today = datetime.now().date()

        # 更新任务数
        self.stats["tasks_completed"] += 1

        # 更新连续天数
        self._update_streak(today)

        # 检查特殊成就
        hour = datetime.now().hour
        if hour < 6:
            new_unlocks.extend(self._check_and_unlock("early_bird", 1))
        if hour >= 23:
            new_unlocks.extend(self._check_and_unlock("night_owl", 1))

        # 检查任务成就
        new_unlocks.extend(self._check_achievements("tasks_completed", self.stats["tasks_completed"]))

        # 检查连续天数成就
        new_unlocks.extend(self._check_achievements("streak_days", self.stats["streak_days"]))

        if new_unlocks:
            self._calculate_total_points()
            self.save_data()

        return new_unlocks

    def record_pomodoro(self, minutes: int) -> List[Achievement]:
        """记录番茄钟完成"""
        new_unlocks = []
        self.stats["pomodoros"] += 1
        self.stats["focus_minutes"] += minutes

        new_unlocks.extend(self._check_achievements("pomodoros", self.stats["pomodoros"]))
        new_unlocks.extend(self._check_achievements("focus_minutes", self.stats["focus_minutes"]))

        if new_unlocks:
            self._calculate_total_points()
            self.save_data()

        return new_unlocks

    def record_ai_call(self) -> List[Achievement]:
        """记录AI调用"""
        new_unlocks = []
        self.stats["ai_calls"] += 1

        new_unlocks.extend(self._check_achievements("ai_calls", self.stats["ai_calls"]))

        if new_unlocks:
            self._calculate_total_points()
            self.save_data()

        return new_unlocks

    def _update_streak(self, today):
        """更新连续天数"""
        last_date = self.stats.get("last_active_date")

        if last_date is None:
            self.stats["streak_days"] = 1
        elif last_date == today - timedelta(days=1):
            self.stats["streak_days"] += 1
        elif last_date != today:
            self.stats["streak_days"] = 1

        self.stats["last_active_date"] = today

    def _check_achievements(self, condition_type: str, value: int) -> List[Achievement]:
        """检查是否解锁成就"""
        new_unlocks = []
        for achievement in self.achievements.values():
            if achievement.condition_type == condition_type and not achievement.unlocked:
                if value >= achievement.condition_value:
                    achievement.unlocked = True
                    achievement.unlocked_at = datetime.now()
                    new_unlocks.append(achievement)
        return new_unlocks

    def _check_and_unlock(self, achievement_id: str, value: int) -> List[Achievement]:
        """检查并解锁特定成就"""
        new_unlocks = []
        achievement = self.achievements.get(achievement_id)
        if achievement and not achievement.unlocked and value >= achievement.condition_value:
            achievement.unlocked = True
            achievement.unlocked_at = datetime.now()
            new_unlocks.append(achievement)
        return new_unlocks

    def get_unlocked_count(self) -> int:
        """获取已解锁成就数量"""
        return sum(1 for a in self.achievements.values() if a.unlocked)

    def get_total_count(self) -> int:
        """获取总成就数量"""
        return len(self.achievements)

    def get_progress(self) -> float:
        """获取完成进度"""
        return self.get_unlocked_count() / self.get_total_count() * 100


class AchievementWidget(QWidget):
    """成就展示组件"""

    def __init__(self, achievement_manager: AchievementManager, parent=None):
        super().__init__(parent)
        self.achievement_manager = achievement_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("🏆 成就殿堂")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #FF8FAB;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 积分显示
        points_label = QLabel(f"⭐ {self.achievement_manager.total_points} 积分")
        points_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        points_label.setStyleSheet("color: #FFB800;")
        title_layout.addWidget(points_label)

        layout.addLayout(title_layout)

        # 进度条
        progress_widget = QFrame()
        progress_widget.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        progress_layout = QVBoxLayout(progress_widget)

        progress_text = QLabel(
            f"已解锁 {self.achievement_manager.get_unlocked_count()} / "
            f"{self.achievement_manager.get_total_count()} 个成就 "
            f"({self.achievement_manager.get_progress():.1f}%)"
        )
        progress_text.setFont(QFont("Microsoft YaHei", 12))
        progress_text.setStyleSheet("color: #666;")
        progress_layout.addWidget(progress_text)
        layout.addWidget(progress_widget)

        # 成就列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        container = QWidget()
        container_layout = QGridLayout(container)
        container_layout.setSpacing(12)

        row, col = 0, 0
        for achievement in self.achievement_manager.achievements.values():
            card = self._create_achievement_card(achievement)
            container_layout.addWidget(card, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1

        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

    def _create_achievement_card(self, achievement: Achievement) -> QFrame:
        """创建成就卡片"""
        card = QFrame()
        card.setMinimumHeight(140)

        if achievement.unlocked:
            bg_color = "#FFF0F3"
            border_color = "#FF8FAB"
            icon_opacity = "1.0"
        else:
            bg_color = "#F5F5F5"
            border_color = "#E0E0E0"
            icon_opacity = "0.3"

        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)

        # 图标
        icon_label = QLabel(achievement.icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 36px; opacity: {icon_opacity};")
        layout.addWidget(icon_label)

        # 名称
        name_label = QLabel(achievement.name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        name_label.setStyleSheet(f"color: {'#333' if achievement.unlocked else '#999'};")
        layout.addWidget(name_label)

        # 描述
        desc_label = QLabel(achievement.description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {'#666' if achievement.unlocked else '#AAA'}; font-size: 11px;")
        layout.addWidget(desc_label)

        # 积分
        if achievement.unlocked:
            points_label = QLabel(f"+{achievement.points}⭐")
            points_label.setAlignment(Qt.AlignCenter)
            points_label.setStyleSheet("color: #FFB800; font-size: 11px; font-weight: bold;")
            layout.addWidget(points_label)

        return card


class AchievementDialog(QDialog):
    """成就对话框"""

    def __init__(self, achievement_manager: AchievementManager, parent=None):
        super().__init__(parent)
        self.achievement_manager = achievement_manager
        self.setWindowTitle("🏆 成就殿堂")
        self.setFixedSize(750, 850)
        self.setStyleSheet("background-color: #FAFAFA;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.widget = AchievementWidget(achievement_manager, self)
        layout.addWidget(self.widget)

        # 关闭按钮
        close_btn = QPushButton("✕ 关闭")
        close_btn.setFixedHeight(44)
        close_btn.setFixedWidth(120)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 13px;
                font-weight: bold;
                margin: 8px;
            }
            QPushButton:hover { background-color: #FF6B8A; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


def show_achievement_notification(achievements: List[Achievement], parent=None):
    """显示成就解锁通知"""
    if not achievements:
        return

    from PyQt5.QtWidgets import QMessageBox

    messages = []
    for achievement in achievements:
        messages.append(f"{achievement.icon} {achievement.name}\n   +{achievement.points} 积分")

    message = "🎉 恭喜解锁新成就！\n\n" + "\n\n".join(messages)

    msg = QMessageBox(parent)
    msg.setWindowTitle("🏆 成就解锁！")
    msg.setText(message)
    msg.setStyleSheet("""
        QMessageBox {
            font-size: 14px;
        }
    """)
    msg.exec_()
