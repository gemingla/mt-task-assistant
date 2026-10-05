"""备份与恢复：字段完整、兼容 1.0 备份、自动备份轮转"""
import json
import os

import pytest

from backup_manager import BackupManager, AUTO_BACKUP_PREFIX
from config import ConfigManager
from stats_manager import StatsManager
from tag_manager import TagManager
from task_manager import TaskManager


@pytest.fixture
def managers(data_dir, qapp):
    from reminder_manager import ReminderManager
    return {
        "task_manager": TaskManager(str(data_dir / "tasks.json")),
        "reminder_manager": ReminderManager(str(data_dir / "reminders.json")),
        "stats_manager": StatsManager(str(data_dir / "stats.json")),
        "tag_manager": TagManager(),
        "config_manager": ConfigManager(str(data_dir / "config.json")),
    }


def test_backup_restore_preserves_all_task_fields(managers, data_dir):
    tm = managers["task_manager"]
    task = tm.add_task("写周报", 30, due_date="2026-10-06 18:00", tags=["工作"])
    tm.update_task(task.id, priority=4)
    tm.toggle_complete(task.id)
    before = task.to_dict()
    managers["stats_manager"].add_focus_time(25)
    stats_before = dict(managers["stats_manager"].stats)

    bm = BackupManager(**managers)
    ok, _, path = bm.create_backup()
    assert ok

    tm.tasks = []
    tm.save_tasks()
    managers["stats_manager"].stats = {}
    ok, _ = bm.restore_backup(path)
    assert ok

    restored = TaskManager(str(data_dir / "tasks.json")).tasks
    assert [t.to_dict() for t in restored] == [before]
    assert managers["stats_manager"].stats == stats_before
    assert StatsManager(str(data_dir / "stats.json")).stats == stats_before


def test_restore_v1_backup_format(managers, data_dir):
    """1.0 版备份没有 id/priority/completed_at，恢复后仍能正常保存"""
    v1 = {
        "version": "1.0",
        "data": {"tasks": [
            {"name": "旧任务A", "completed": True, "estimated_minutes": 20,
             "source": "manual", "due_date": "2026-01-02 09:00", "tags": [], "created_at": None},
            {"name": "旧任务B", "completed": False, "estimated_minutes": 15,
             "source": "manual", "due_date": None, "tags": ["学习"], "created_at": None},
        ]},
    }
    path = data_dir / "v1.json"
    path.write_text(json.dumps(v1, ensure_ascii=False), encoding="utf-8")

    ok, _ = BackupManager(**managers).restore_backup(str(path))
    assert ok
    tasks = TaskManager(str(data_dir / "tasks.json")).tasks
    assert [t.name for t in tasks] == ["旧任务A", "旧任务B"]
    assert len({t.id for t in tasks}) == 2
    assert tasks[0].completed and tasks[0].completed_at
    assert tasks[0].due_date == "2026-01-02 09:00"  # 仍是字符串，可正常写入 JSON


def test_restore_takes_safety_snapshot_first(managers, data_dir):
    managers["task_manager"].add_task("当前数据", 10)
    bm = BackupManager(**managers)
    ok, _, path = bm.create_backup()
    bm.restore_backup(path)
    names = os.listdir(data_dir / "backups")
    assert any(n.startswith("backup_before_restore_") for n in names)


def test_restore_tags_keeps_custom_colors(managers):
    bm = BackupManager(**managers)
    bm._restore_tags({"custom_tags": {"健身": "#123456"}})
    assert managers["tag_manager"].get_custom_tags()["健身"] == "#123456"


def test_auto_backup_once_per_day_and_prunes(managers, data_dir):
    backup_dir = data_dir / "backups"
    backup_dir.mkdir()
    for day in range(1, 10):  # 预置 9 份旧的自动备份
        (backup_dir / f"{AUTO_BACKUP_PREFIX}202601{day:02d}_080000.json").write_text("{}", encoding="utf-8")
    (backup_dir / "backup_20260101_080000.json").write_text("{}", encoding="utf-8")  # 手动备份

    bm = BackupManager(**managers)
    assert bm.auto_backup(keep=7) is not None
    assert bm.auto_backup(keep=7) is None  # 当天已备份

    names = os.listdir(backup_dir)
    autos = [n for n in names if n.startswith(AUTO_BACKUP_PREFIX)]
    assert len(autos) == 7
    assert "backup_20260101_080000.json" in names  # 手动备份不受影响
