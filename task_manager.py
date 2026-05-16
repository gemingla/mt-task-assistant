import json
import os
from datetime import datetime
from utils import get_data_path

TASKS_FILE = get_data_path("tasks.json")


class Task:
    def __init__(self, id, name, estimated_minutes, completed=False, created_date=None,
                 actual_minutes=0, completed_at=None, source="manual", due_date=None, reminded=False,
                 priority=2, status="pending", tags=None):
        self.id = id
        self.name = name
        self.estimated_minutes = estimated_minutes
        self.completed = completed
        self.created_date = created_date or datetime.now().strftime("%Y-%m-%d")
        self.actual_minutes = actual_minutes
        self.completed_at = completed_at
        self.source = source
        self.due_date = due_date
        self.reminded = reminded
        self.priority = priority  # 1-5: LOW, NORMAL, HIGH, URGENT, CRITICAL
        self.status = status  # pending, in_progress, paused, completed, cancelled
        self.tags = tags or []  # 标签列表

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "estimated_minutes": self.estimated_minutes,
            "completed": self.completed,
            "created_date": self.created_date,
            "actual_minutes": self.actual_minutes,
            "completed_at": self.completed_at,
            "source": self.source,
            "due_date": self.due_date,
            "reminded": self.reminded,
            "priority": self.priority,
            "status": self.status,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data):
        created_date = data.get("created_date") or data.get("created_at", "")
        if created_date and len(created_date) > 10:
            created_date = created_date[:10]
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            estimated_minutes=data.get("estimated_minutes", 0),
            completed=data.get("completed", False),
            created_date=created_date,
            actual_minutes=data.get("actual_minutes", 0),
            completed_at=data.get("completed_at"),
            source=data.get("source", "manual"),
            due_date=data.get("due_date"),
            reminded=data.get("reminded", False),
            priority=data.get("priority", 2),
            status=data.get("status", "pending"),
            tags=data.get("tags", [])
        )


class TaskManager:
    def __init__(self, tasks_path=None):
        self.tasks_path = tasks_path or TASKS_FILE
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.tasks_path):
            try:
                with open(self.tasks_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.tasks = [Task.from_dict(t) for t in data]
            except Exception as e:
                print(f"加载任务失败: {e}")
                self.tasks = []
        else:
            self.tasks = []

    def save_tasks(self):
        try:
            data = [t.to_dict() for t in self.tasks]
            with open(self.tasks_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            import traceback
            err_msg = f"保存任务失败 [{self.tasks_path}]: {e}\n{traceback.format_exc()}"
            print(err_msg)
            # 同时写入 crash.log
            try:
                with open("crash.log", "a", encoding="utf-8") as lf:
                    lf.write(f"\n===== {__import__('datetime').datetime.now()} =====\n{err_msg}\n")
            except Exception:
                pass

    def add_task(self, name, estimated_minutes, source="manual", due_date=None, tags=None):
        task = Task(
            id=self._generate_id(),
            name=name,
            estimated_minutes=estimated_minutes,
            source=source,
            due_date=due_date,
            tags=tags or []
        )
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def get_all_tags(self):
        """获取所有使用过的标签"""
        tags_set = set()
        for task in self.tasks:
            tags_set.update(task.tags)
        return sorted(list(tags_set))
    
    def get_tasks_by_tag(self, tag):
        """根据标签筛选任务"""
        return [t for t in self.tasks if tag in t.tags]
    
    def search_tasks(self, keyword):
        """搜索任务（按名称、标签）"""
        keyword = keyword.lower().strip()
        if not keyword:
            return self.tasks
        return [t for t in self.tasks if 
                keyword in t.name.lower() or 
                any(keyword in tag.lower() for tag in t.tags)]

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.save_tasks()

    def update_task(self, task_id, **kwargs):
        for task in self.tasks:
            if task.id == task_id:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                self.save_tasks()
                return task
        return None

    def toggle_complete(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                task.completed = not task.completed
                if task.completed:
                    task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    task.completed_at = None
                self.save_tasks()
                return task
        return None

    def get_task_by_id(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_tasks(self, filter_completed=None):
        if filter_completed is None:
            return self.tasks
        return [t for t in self.tasks if t.completed == filter_completed]

    def get_today_tasks(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return [t for t in self.tasks if t.created_date == today]

    def get_today_completed(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return [t for t in self.tasks if t.completed_at and (
            (isinstance(t.completed_at, str) and t.completed_at.startswith(today)) or
            (isinstance(t.completed_at, datetime) and t.completed_at.strftime("%Y-%m-%d") == today)
        )]

    def get_tasks_sorted_by_due(self):
        tasks_with_due = [t for t in self.tasks if t.due_date]
        tasks_without_due = [t for t in self.tasks if not t.due_date]
        tasks_with_due.sort(key=lambda t: t.due_date.strftime("%Y-%m-%d %H:%M") if isinstance(t.due_date, datetime) else str(t.due_date))
        return tasks_with_due + tasks_without_due

    def get_upcoming_tasks(self, minutes=5):
        now = datetime.now()
        upcoming = []
        for task in self.tasks:
            if task.completed or not task.due_date or task.reminded:
                continue
            try:
                due = task.due_date if isinstance(task.due_date, datetime) else datetime.strptime(task.due_date, "%Y-%m-%d %H:%M")
                diff = (due - now).total_seconds() / 60
                if 0 < diff <= minutes:
                    upcoming.append((task, diff))
            except:
                continue
        return upcoming

    def mark_task_reminded(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                task.reminded = True
                self.save_tasks()
                return True
        return False

    def _generate_id(self):
        if not self.tasks:
            return 1
        return max(t.id for t in self.tasks) + 1
    
    def clear_completed_tasks(self):
        """删除所有已完成的任务"""
        completed_count = len([t for t in self.tasks if t.completed])
        self.tasks = [t for t in self.tasks if not t.completed]
        self.save_tasks()
        return completed_count
    
    def delete_multiple_tasks(self, task_ids):
        """批量删除指定ID的任务"""
        original_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id not in task_ids]
        deleted_count = original_count - len(self.tasks)
        self.save_tasks()
        return deleted_count
