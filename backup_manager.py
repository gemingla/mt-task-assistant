"""
数据备份与恢复管理器
支持导出/导入所有用户数据
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import shutil
from utils import get_data_path, atomic_write_json

BACKUP_VERSION = "2.0"
AUTO_BACKUP_PREFIX = "backup_auto_"
AUTO_BACKUP_KEEP = 7


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
                "version": BACKUP_VERSION,
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

            # 写入文件（原子写入，避免半截备份）
            atomic_write_json(backup_path, backup_data)

            return True, f"备份成功！", backup_path

        except Exception as e:
            return False, f"备份失败: {str(e)}", ""

    def _backup_tasks(self) -> list:
        """备份任务数据（完整保留 id、优先级、完成时间等全部字段）"""
        tasks = []
        for task in self.task_manager.tasks:
            data = task.to_dict()
            # 内存中的 due_date 偶尔是 datetime，统一转成字符串
            if hasattr(data.get("due_date"), "strftime"):
                data["due_date"] = data["due_date"].strftime("%Y-%m-%d %H:%M")
            tasks.append(data)
        return tasks

    def _backup_reminders(self) -> list:
        """备份提醒数据"""
        return [r.to_dict() for r in self.reminder_manager.reminders]

    def _backup_stats(self) -> dict:
        """备份统计数据（直接取内存中的统计，避免读文件出错时得到空数据）"""
        return dict(self.stats_manager.stats)

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

            # 覆盖之前先把当前数据存一份，误操作时可以找回
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.create_backup(os.path.join(self._backup_dir(), f"backup_before_restore_{timestamp}.json"))

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
        """恢复任务；兼容 1.0 版备份（无 id、日期字段格式不同）"""
        from task_manager import Task
        restored = []
        next_id = 1
        for task_data in tasks_data:
            data = dict(task_data)
            if not data.get("id"):
                data["id"] = next_id
            next_id = max(next_id, data["id"]) + 1
            if data.get("completed") and not data.get("completed_at"):
                data["completed_at"] = (data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            restored.append(Task.from_dict(data))

        # 保证 id 唯一
        seen = set()
        for task in restored:
            if task.id in seen:
                task.id = next_id
                next_id += 1
            seen.add(task.id)

        self.task_manager.tasks = restored
        self.task_manager.save_tasks()
        return len(restored)

    def _restore_reminders(self, reminders_data: list) -> int:
        """恢复提醒；兼容 1.0 版备份（无 id）"""
        from reminder_manager import Reminder
        restored = []
        next_id = 1
        for reminder_data in reminders_data:
            try:
                data = dict(reminder_data)
                data["id"] = data.get("id") or next_id
                data["created_at"] = data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                restored.append(Reminder.from_dict(data))
                next_id = max(next_id, data["id"]) + 1
            except Exception as e:
                print(f"恢复提醒失败: {e}")

        self.reminder_manager.reminders = restored
        self.reminder_manager.next_id = next_id
        self.reminder_manager.save_reminders()
        return len(restored)

    def _restore_stats(self, stats_data: dict):
        """恢复统计数据（同时更新内存，避免之后被旧数据覆盖）"""
        if not isinstance(stats_data, dict):
            return
        self.stats_manager.stats = dict(stats_data)
        self.stats_manager.save_stats()

    def _restore_tags(self, tags_data: dict):
        """恢复标签（保留自定义颜色）"""
        try:
            custom = tags_data.get("custom_tags", {})
            if isinstance(custom, dict):
                for tag, color in custom.items():
                    self.tag_manager.add_custom_tag(tag, color)
            else:  # 兼容列表格式
                for tag in custom:
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

    @staticmethod
    def _backup_dir() -> str:
        backup_dir = get_data_path("backups")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    def auto_backup(self, keep: int = AUTO_BACKUP_KEEP) -> Optional[str]:
        """
        每日自动备份：当天还没有自动备份时创建一份，并只保留最近 keep 份自动备份。
        手动备份不受影响。返回新备份路径；当天已备份或失败时返回 None。
        """
        backup_dir = self._backup_dir()
        today = datetime.now().strftime("%Y%m%d")
        autos = sorted(f for f in os.listdir(backup_dir)
                       if f.startswith(AUTO_BACKUP_PREFIX) and f.endswith(".json"))
        if any(f.startswith(f"{AUTO_BACKUP_PREFIX}{today}") for f in autos):
            return None

        path = os.path.join(backup_dir, f"{AUTO_BACKUP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        success, _, path = self.create_backup(path)
        if not success:
            return None

        autos.append(os.path.basename(path))
        for old_file in sorted(autos)[:-keep]:
            try:
                os.remove(os.path.join(backup_dir, old_file))
            except OSError:
                pass
        return path

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
