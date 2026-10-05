"""任务管理：增删改、完成状态、持久化"""
from task_manager import TaskManager


def make_manager(data_dir):
    return TaskManager(str(data_dir / "tasks.json"))


def test_add_and_reload(data_dir):
    tm = make_manager(data_dir)
    task = tm.add_task("写周报", 30, due_date="2026-10-06 18:00", tags=["工作"])
    reloaded = make_manager(data_dir)
    assert len(reloaded.tasks) == 1
    loaded = reloaded.tasks[0]
    assert (loaded.id, loaded.name, loaded.estimated_minutes, loaded.due_date, loaded.tags) == \
        (task.id, "写周报", 30, "2026-10-06 18:00", ["工作"])


def test_ids_are_unique_and_increasing(data_dir):
    tm = make_manager(data_dir)
    ids = [tm.add_task(f"任务{i}", 10).id for i in range(3)]
    assert ids == [1, 2, 3]
    tm.delete_task(2)
    assert tm.add_task("新任务", 10).id == 4


def test_toggle_complete_sets_and_clears_completed_at(data_dir):
    tm = make_manager(data_dir)
    task = tm.add_task("跑步", 30)
    tm.toggle_complete(task.id)
    assert task.completed and task.completed_at
    tm.toggle_complete(task.id)
    assert not task.completed and task.completed_at is None


def test_completed_tasks_survive_reload(data_dir):
    """2.0：已完成任务不再在启动时被删除"""
    tm = make_manager(data_dir)
    task = tm.add_task("读书", 45)
    tm.toggle_complete(task.id)
    reloaded = make_manager(data_dir)
    assert reloaded.get_task_by_id(task.id).completed


def test_clear_completed_and_batch_delete(data_dir):
    tm = make_manager(data_dir)
    a, b, c = (tm.add_task(n, 10) for n in "abc")
    tm.toggle_complete(a.id)
    assert tm.clear_completed_tasks() == 1
    assert tm.delete_multiple_tasks([b.id, c.id]) == 2
    assert make_manager(data_dir).tasks == []


def test_sorted_by_due_puts_undated_last(data_dir):
    tm = make_manager(data_dir)
    tm.add_task("无截止", 10)
    tm.add_task("晚", 10, due_date="2026-10-07 09:00")
    tm.add_task("早", 10, due_date="2026-10-06 09:00")
    assert [t.name for t in tm.get_tasks_sorted_by_due()] == ["早", "晚", "无截止"]
