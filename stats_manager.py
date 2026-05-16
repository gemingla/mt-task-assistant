import json
import os
from datetime import datetime, timedelta
from utils import get_data_path

STATS_FILE = get_data_path("stats.json")


class StatsManager:
    def __init__(self, stats_path=None):
        self.stats_path = stats_path or STATS_FILE
        self.stats = {}
        self.load_stats()

    def load_stats(self):
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, "r", encoding="utf-8") as f:
                    self.stats = json.load(f)
            except Exception:
                self.stats = {}
        else:
            self.stats = {}

    def save_stats(self):
        try:
            with open(self.stats_path, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存统计失败: {e}")

    def add_focus_time(self, minutes, date=None, task_name=""):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        if date not in self.stats:
            self.stats[date] = {"focus_minutes": 0, "pomodoro_count": 0, "tasks_completed": 0, "pomodoro_logs": []}
        self.stats[date]["focus_minutes"] += minutes
        self.stats[date]["pomodoro_count"] += 1
        if task_name:
            if "pomodoro_logs" not in self.stats[date]:
                self.stats[date]["pomodoro_logs"] = []
            self.stats[date]["pomodoro_logs"].append({
                "duration": minutes,
                "task_name": task_name,
                "time": datetime.now().strftime("%H:%M:%S")
            })
        self.save_stats()

    def add_task_completed(self, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        if date not in self.stats:
            self.stats[date] = {"focus_minutes": 0, "pomodoro_count": 0, "tasks_completed": 0}
        self.stats[date]["tasks_completed"] += 1
        self.save_stats()

    def get_last_7_days(self):
        result = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            data = self.stats.get(date, {"focus_minutes": 0, "pomodoro_count": 0, "tasks_completed": 0})
            result.append({
                "date": date,
                "focus_minutes": data.get("focus_minutes", 0),
                "pomodoro_count": data.get("pomodoro_count", 0),
                "tasks_completed": data.get("tasks_completed", 0)
            })
        return result

    def get_task_completion_rate(self, total_tasks, completed_tasks):
        if total_tasks == 0:
            return 0
        return round(completed_tasks / total_tasks * 100, 1)
