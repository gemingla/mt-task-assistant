"""
数据备份与恢复管理器
支持导出/导入所有用户数据
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import shutil
from utils import get_data_path


class BackupManager:
    """数据备份管理器"""

    def __init__(self, task_manager=None, reminder_manager=None,
                 stats_manager=None, tag_manager=None, config_manager=None,
                 memory_manager=None):
        self.task_manager = task_manager
        self.reminder_manager = reminder_manager
        self.stats_manager = stats_manager
        self.tag_manager = tag_manager
        self.config_manager = config_manager
        self.memory_manager = memory_manager

    def create_backup(self, backup_path: str = None) -> tuple:
        """
        创建备份

        Returns:
            (success: bool, message: str, backup_path: str)
        """
        try:
            # 生成备份文件名
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = get_data_path("backups")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                backup_path = os.path.join(backup_dir, f"backup_{timestamp}.json")

            backup_data = {
                "version": "1.0",
                "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {}
            }

            # 备份任务
            if self.task_manager:
                backup_data["data"]["tasks"] = self._backup_tasks()

            # 备份提醒
            if self.reminder_manager:
                backup_data["data"]["reminders"] = self._backup_reminders()

            # 备份统计
            if self.stats_manager:
                backup_data["data"]["stats"] = self._backup_stats()

            # 备份标签
            if self.tag_manager:
                backup_data["data"]["tags"] = self._backup_tags()

            # 备份配置
            if self.config_manager:
                backup_data["data"]["config"] = self._backup_config()

            # 备份记忆
            if self.memory_manager:
                backup_data["data"]["memories"] = self._backup_memories()

            # 写入文件
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            return True, f"备份成功！", backup_path

        except Exception as e:
            return False, f"备份失败: {str(e)}", ""

    def _backup_tasks(self) -> list:
        """备份任务数据"""
        tasks = []
        for task in self.task_manager.tasks:
            # 处理 due_date，可能是 datetime 对象或字符串
            due_date_str = None
            if task.due_date:
                if isinstance(task.due_date, str):
                    due_date_str = task.due_date
                elif hasattr(task.due_date, 'strftime'):
                    due_date_str = task.due_date.strftime("%Y-%m-%d %H:%M")

            task_data = {
                "name": task.name,
                "completed": task.completed,
                "estimated_minutes": task.estimated_minutes,
                "source": getattr(task, 'source', 'manual'),
                "due_date": due_date_str,
                "tags": task.tags if hasattr(task, 'tags') else [],
                "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(task, 'created_at') else None
            }
            tasks.append(task_data)
        return tasks

    def _backup_reminders(self) -> list:
        """备份提醒数据"""
        reminders = []
        for reminder in self.reminder_manager.reminders:
            # 处理 remind_time，可能是 datetime 对象或字符串
            remind_time_str = None
            if reminder.remind_time:
                if isinstance(reminder.remind_time, str):
                    remind_time_str = reminder.remind_time
                elif hasattr(reminder.remind_time, 'strftime'):
                    remind_time_str = reminder.remind_time.strftime("%Y-%m-%d %H:%M:%S")

            reminder_data = {
                "title": reminder.title,
                "remind_time": remind_time_str,
                "description": reminder.description,
                "repeat_type": reminder.repeat_type,
                "enabled": reminder.enabled,
                "created_at": reminder.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(reminder, 'created_at') else None
            }
            reminders.append(reminder_data)
        return reminders

    def _backup_stats(self) -> dict:
        """备份统计数据"""
        try:
            stats_file = self.stats_manager.data_file
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"备份统计数据失败: {e}")
        return {}

    def _backup_tags(self) -> dict:
        """备份标签数据"""
        return {
            "preset_tags": self.tag_manager.get_preset_tags(),
            "custom_tags": self.tag_manager.get_custom_tags()
        }

    def _backup_config(self) -> dict:
        """备份配置"""
        return self.config_manager.load_config()

    def _backup_memories(self) -> dict:
        """备份记忆数据"""
        if not self.memory_manager:
            return {}

        try:
            # 直接从 MemoryManager 获取记忆数据
            return {
                "short_term": [m.to_dict() for m in self.memory_manager.short_term_memories],
                "long_term": [m.to_dict() for m in self.memory_manager.long_term_memories]
            }
        except Exception as e:
            print(f"备份记忆失败: {e}")
            return {}

    def restore_backup(self, backup_path: str) -> tuple:
        """
        从备份恢复数据

        Returns:
            (success: bool, message: str)
        """
        try:
            if not os.path.exists(backup_path):
                return False, "备份文件不存在"

            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            data = backup_data.get("data", {})
            restored_items = []

            # 恢复任务
            if "tasks" in data and self.task_manager:
                count = self._restore_tasks(data["tasks"])
                restored_items.append(f"{count} 个任务")

            # 恢复提醒
            if "reminders" in data and self.reminder_manager:
                count = self._restore_reminders(data["reminders"])
                restored_items.append(f"{count} 个提醒")

            # 恢复统计
            if "stats" in data and self.stats_manager:
                self._restore_stats(data["stats"])
                restored_items.append("统计数据")

            # 恢复标签
            if "tags" in data and self.tag_manager:
                self._restore_tags(data["tags"])
                restored_items.append("标签")

            # 恢复配置
            if "config" in data and self.config_manager:
                self._restore_config(data["config"])
                restored_items.append("配置")

            # 恢复记忆
            if "memories" in data and self.memory_manager:
                self._restore_memories(data["memories"])
                restored_items.append("记忆")

            message = f"恢复成功！已恢复：{', '.join(restored_items)}"
            return True, message

        except Exception as e:
            return False, f"恢复失败: {str(e)}"

    def _restore_tasks(self, tasks_data: list) -> int:
        """恢复任务"""
        from datetime import datetime
        count = 0
        # 清空现有任务
        self.task_manager.tasks = []

        for task_data in tasks_data:
            due_date = None
            if task_data.get("due_date"):
                try:
                    due_date = datetime.strptime(task_data["due_date"], "%Y-%m-%d %H:%M")
                except ValueError as e:
                    print(f"解析任务日期失败: {e}")

            task = self.task_manager.add_task(
                name=task_data["name"],
                estimated_minutes=task_data.get("estimated_minutes", 30),
                source=task_data.get("source", "manual"),
                due_date=due_date,
                tags=task_data.get("tags", [])
            )

            if task_data.get("completed"):
                task.completed = True

            count += 1

        self.task_manager.save_tasks()
        return count

    def _restore_reminders(self, reminders_data: list) -> int:
        """恢复提醒"""
        from datetime import datetime
        count = 0
        # 清空现有提醒
        self.reminder_manager.reminders = []
        self.reminder_manager.next_id = 1

        for reminder_data in reminders_data:
            try:
                remind_time = datetime.strptime(reminder_data["remind_time"], "%Y-%m-%d %H:%M:%S")
                self.reminder_manager.add_reminder(
                    title=reminder_data["title"],
                    remind_time=remind_time,
                    description=reminder_data.get("description", ""),
                    repeat_type=reminder_data.get("repeat_type", "none")
                )
                count += 1
            except Exception as e:
                print(f"恢复提醒失败: {e}")

        # 确保持久化
        self.reminder_manager.save_reminders()
        return count

    def _restore_stats(self, stats_data: dict):
        """恢复统计数据"""
        try:
            stats_file = self.stats_manager.data_file
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"恢复统计数据失败: {e}")

    def _restore_tags(self, tags_data: dict):
        """恢复标签"""
        try:
            # 恢复自定义标签
            for tag in tags_data.get("custom_tags", []):
                self.tag_manager.add_custom_tag(tag)
        except Exception as e:
            print(f"恢复标签失败: {e}")

    def _restore_config(self, config_data: dict):
        """恢复配置"""
        try:
            self.config_manager.save_config(config_data)
        except Exception as e:
            print(f"恢复配置失败: {e}")

    def _restore_memories(self, memories_data: dict):
        """恢复记忆"""
        if not self.memory_manager or not memories_data:
            return

        try:
            # 导入 Memory 类
            from memory_manager import Memory

            # 清空现有记忆
            self.memory_manager.short_term_memories = []
            self.memory_manager.long_term_memories = []

            # 恢复短期记忆
            for mem_data in memories_data.get("short_term", []):
                try:
                    memory = Memory.from_dict(mem_data)
                    self.memory_manager.short_term_memories.append(memory)
                except Exception as e:
                    print(f"恢复短期记忆失败: {e}")

            # 恢复长期记忆
            for mem_data in memories_data.get("long_term", []):
                try:
                    memory = Memory.from_dict(mem_data)
                    self.memory_manager.long_term_memories.append(memory)
                except Exception as e:
                    print(f"恢复长期记忆失败: {e}")

            # 重建索引并保存
            self.memory_manager._rebuild_indexes()
            self.memory_manager._save_memories()
        except Exception as e:
            print(f"恢复记忆失败: {e}")

    def get_backup_list(self) -> list:
        """获取备份文件列表"""
        backup_dir = get_data_path("backups")
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith(".json") and filename.startswith("backup_"):
                filepath = os.path.join(backup_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    backups.append({
                        "filename": filename,
                        "path": filepath,
                        "time": data.get("backup_time", "未知时间"),
                        "size": os.path.getsize(filepath)
                    })
                except Exception as e:
                    print(f"读取备份文件 {filename} 失败: {e}")

        # 按时间倒序排列
        backups.sort(key=lambda x: x["time"], reverse=True)
        return backups

    def delete_backup(self, backup_path: str) -> bool:
        """删除备份文件"""
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                return True
        except Exception as e:
            print(f"删除备份文件失败: {e}")
        return False
