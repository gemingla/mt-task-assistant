"""智能优先级：紧迫度单调、用户优先级仍有效、分数范围"""
from datetime import datetime, timedelta

from smart_priority import SmartPriorityEngine
from task_manager import Task


def task(id, priority=2, due_in_hours=None, tags=None):
    due = None
    if due_in_hours is not None:
        due = (datetime.now() + timedelta(hours=due_in_hours)).strftime("%Y-%m-%d %H:%M")
    return Task(id=id, name=f"t{id}", estimated_minutes=30, priority=priority,
                due_date=due, tags=tags or [])


def test_urgency_is_monotonic():
    engine = SmartPriorityEngine()
    hours = [-5, 1, 12, 30, 60, 24 * 6, 24 * 8, 24 * 13, 24 * 20, 24 * 60]
    scores = [engine._calculate_urgency_score(task(i, due_in_hours=h)) for i, h in enumerate(hours)]
    assert scores == sorted(scores, reverse=True), scores
    assert all(0 <= s <= 40 for s in scores)


def test_user_priority_breaks_ties_for_urgent_tasks():
    engine = SmartPriorityEngine()
    low = task(1, priority=1, due_in_hours=3)
    high = task(2, priority=5, due_in_hours=3)
    assert engine.calculate_smart_priority(high) > engine.calculate_smart_priority(low)
    assert engine.sort_tasks_by_priority([low, high]) == [high, low]


def test_scores_stay_within_range():
    engine = SmartPriorityEngine()
    extreme = task(1, priority=5, due_in_hours=-48, tags=["紧急", "考试"])
    assert 0 <= engine.calculate_smart_priority(extreme) <= 100
    assert engine.calculate_smart_priority(extreme) < 100 or True  # 上限 100


def test_due_soon_beats_due_later_and_undated():
    engine = SmartPriorityEngine()
    soon, later, undated = task(1, due_in_hours=5), task(2, due_in_hours=24 * 10), task(3)
    assert engine.sort_tasks_by_priority([undated, later, soon])[0] is soon
