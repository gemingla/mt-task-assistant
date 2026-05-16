"""
提醒管理器
管理提醒的增删改查、定时提醒等功能
"""
import json
import os
import calendar
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QDateTime


class Reminder:
    """提醒类"""
    def __init__(self, reminder_id: int, title: str, remind_time: datetime,
                 description: str = "", repeat_type: str = "none",
                 enabled: bool = True):
        self.id = reminder_id
        self.title = title
        self.remind_time = remind_time
        self.description = description
        self.repeat_type = repeat_type  # none, daily, weekly, monthly
        self.enabled = enabled
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "remind_time": self.remind_time.strftime("%Y-%m-%d %H:%M:%S"),
            "description": self.description,
            "repeat_type": self.repeat_type,
            "enabled": self.enabled,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Reminder':
        """从字典创建"""
        reminder = cls(
            reminder_id=data["id"],
            title=data["title"],
            remind_time=datetime.strptime(data["remind_time"], "%Y-%m-%d %H:%M:%S"),
            description=data.get("description", ""),
            repeat_type=data.get("repeat_type", "none"),
            enabled=data.get("enabled", True)
        )
        reminder.created_at = datetime.strptime(data["created_at"], "%Y-%m-%d %H:%M:%S")
        return reminder
    
    def get_next_remind_time(self) -> Optional[datetime]:
        """获取下一次提醒时间（用于重复提醒）"""
        if self.repeat_type == "none":
            return None

        now = datetime.now()
        next_time = self.remind_time

        if self.repeat_type == "daily":
            # 每天重复
            while next_time <= now:
                next_time += timedelta(days=1)
        elif self.repeat_type == "weekly":
            # 每周重复
            while next_time <= now:
                next_time += timedelta(weeks=1)
        elif self.repeat_type == "monthly":
            # 每月重复 - 正确处理月份
            while next_time <= now:
                year = next_time.year
                month = next_time.month
                day = next_time.day
                hour = next_time.hour
                minute = next_time.minute
                second = next_time.second

                # 计算下个月
                month += 1
                if month > 12:
                    month = 1
                    year += 1

                # 处理月末日期（如1月31日 -> 2月28/29日）
                _, last_day = calendar.monthrange(year, month)
                day = min(day, last_day)

                try:
                    next_time = datetime(year, month, day, hour, minute, second)
                except ValueError:
                    # 如果日期无效，使用该月最后一天
                    next_time = datetime(year, month, last_day, hour, minute, second)

        return next_time


class ReminderManager(QObject):
    """提醒管理器"""
    reminder_triggered = pyqtSignal(object)  # 提醒触发信号

    def __init__(self, data_file: str = "reminders.json"):
        super().__init__()
        self.data_file = data_file
        self.reminders: List[Reminder] = []
        self.next_id = 1
        # 已触发提醒的去重集合: {(reminder_id, remind_time_str)}
        self._triggered_keys: set = set()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(1000)  # 每秒检查一次，到时间立即弹窗

        self.load_reminders()
        # 启动后立即检查一次，补上关闭期间错过的提醒
        QTimer.singleShot(500, self.check_reminders)
    
    def load_reminders(self):
        """加载提醒数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 兼容旧格式：直接是列表
                    if isinstance(data, list):
                        self.reminders = [Reminder.from_dict(r) for r in data]
                        self.next_id = max((r["id"] for r in data), default=0) + 1
                    else:
                        self.reminders = [Reminder.from_dict(r) for r in data.get("reminders", [])]
                        self.next_id = data.get("next_id", 1)
            except Exception as e:
                print(f"加载提醒数据失败: {e}")
                self.reminders = []
                self.next_id = 1
    
    def save_reminders(self):
        """保存提醒数据"""
        try:
            data = {
                "reminders": [r.to_dict() for r in self.reminders],
                "next_id": self.next_id
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存提醒数据失败: {e}")
    
    def add_reminder(self, title: str, remind_time: datetime,
                     description: str = "", repeat_type: str = "none") -> Reminder:
        """添加提醒"""
        reminder = Reminder(
            reminder_id=self.next_id,
            title=title,
            remind_time=remind_time,
            description=description,
            repeat_type=repeat_type
        )
        self.reminders.append(reminder)
        self.next_id += 1
        self.save_reminders()
        return reminder
    
    def update_reminder(self, reminder_id: int, **kwargs) -> Optional[Reminder]:
        """更新提醒"""
        for reminder in self.reminders:
            if reminder.id == reminder_id:
                for key, value in kwargs.items():
                    if hasattr(reminder, key):
                        setattr(reminder, key, value)
                self.save_reminders()
                return reminder
        return None
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """删除提醒"""
        for i, reminder in enumerate(self.reminders):
            if reminder.id == reminder_id:
                self.reminders.pop(i)
                # 清理该提醒的所有触发记录
                self._triggered_keys = {k for k in self._triggered_keys if k[0] != reminder_id}
                self.save_reminders()
                return True
        return False
    
    def toggle_reminder(self, reminder_id: int) -> Optional[Reminder]:
        """切换提醒启用状态"""
        for reminder in self.reminders:
            if reminder.id == reminder_id:
                reminder.enabled = not reminder.enabled
                self.save_reminders()
                return reminder
        return None
    
    def get_reminder(self, reminder_id: int) -> Optional[Reminder]:
        """获取指定提醒"""
        for reminder in self.reminders:
            if reminder.id == reminder_id:
                return reminder
        return None
    
    def get_all_reminders(self) -> List[Reminder]:
        """获取所有提醒"""
        return sorted(self.reminders, key=lambda r: r.remind_time)
    
    def get_active_reminders(self) -> List[Reminder]:
        """获取所有启用的提醒"""
        return [r for r in self.reminders if r.enabled]
    
    def check_reminders(self):
        """检查是否有提醒需要触发（每秒调用，到时间立即弹窗）"""
        # 每30次（约30秒）清理一次过期记录
        if not hasattr(self, '_cleanup_counter'):
            self._cleanup_counter = 0
        self._cleanup_counter += 1
        if self._cleanup_counter % 30 == 0:
            self._cleanup_triggered_keys()

        now = datetime.now()

        for reminder in self.reminders:
            if not reminder.enabled:
                continue

            # 构建唯一键防止重复触发
            time_key = reminder.remind_time.strftime("%Y-%m-%d %H:%M")
            trigger_key = (reminder.id, time_key)

            # 检查是否到达提醒时间（精确到分钟，每秒轮询确保即时性）
            if (reminder.remind_time.year == now.year and
                reminder.remind_time.month == now.month and
                reminder.remind_time.day == now.day and
                reminder.remind_time.hour == now.hour and
                reminder.remind_time.minute == now.minute):

                # 跳过已经触发过的
                if trigger_key in self._triggered_keys:
                    continue
                self._triggered_keys.add(trigger_key)

                # 触发提醒
                self.reminder_triggered.emit(reminder)

                # 如果是重复提醒，更新下一次提醒时间
                if reminder.repeat_type != "none":
                    next_time = reminder.get_next_remind_time()
                    if next_time:
                        reminder.remind_time = next_time
                        self.save_reminders()
                else:
                    # 非重复提醒，自动禁用
                    reminder.enabled = False
                    self.save_reminders()
    
    def _cleanup_triggered_keys(self):
        """清理已过期的触发记录（每分钟由上层调用一次）"""
        now = datetime.now()
        expired = set()
        for key in self._triggered_keys:
            _, time_str = key
            try:
                t = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                # 超过2分钟的记录清除
                if (now - t).total_seconds() > 120:
                    expired.add(key)
            except ValueError:
                expired.add(key)
        self._triggered_keys -= expired

    def get_upcoming_reminders(self, hours: int = 24) -> List[Reminder]:
        """获取接下来的提醒（指定小时内）"""
        now = datetime.now()
        end_time = now + timedelta(hours=hours)
        
        upcoming = []
        for reminder in self.reminders:
            if reminder.enabled and now <= reminder.remind_time <= end_time:
                upcoming.append(reminder)
        
        return sorted(upcoming, key=lambda r: r.remind_time)
