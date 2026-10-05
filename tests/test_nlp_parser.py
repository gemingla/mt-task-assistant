"""自然语言任务解析"""
from datetime import datetime

import pytest

from nlp_task_parser import NLPTaskParser

# 固定“现在”为 2026-10-05（周一）10:00，结果可复现
NOW = datetime(2026, 10, 5, 10, 0)


def parse(text):
    return NLPTaskParser().parse(text, now=NOW)


def test_full_example():
    r = parse("明天下午3点开会 #工作 重要")
    assert r["task_name"] == "开会"
    assert r["due_date"] == datetime(2026, 10, 6, 15, 0)
    assert r["priority"] == 4
    assert r["tags"] == ["工作"]


@pytest.mark.parametrize("text, expected", [
    ("不紧急的事", 1),
    ("比较重要的报告", 3),
    ("非常紧急 修复线上问题", 5),
    ("重要 写方案", 4),
    ("普通任务", 2),
])
def test_priority_prefers_longest_keyword(text, expected):
    assert parse(text)["priority"] == expected


@pytest.mark.parametrize("text, expected", [
    ("周日 打扫卫生", datetime(2026, 10, 11, 9, 0)),
    ("周三 交作业", datetime(2026, 10, 7, 9, 0)),
    ("下周三 交作业", datetime(2026, 10, 14, 9, 0)),
    ("下周一 例会", datetime(2026, 10, 12, 9, 0)),
    ("周一 例会", datetime(2026, 10, 12, 9, 0)),  # 今天是周一，指下一个周一
])
def test_weekdays(text, expected):
    assert parse(text)["due_date"] == expected


@pytest.mark.parametrize("text, expected", [
    ("中午12点 吃饭", datetime(2026, 10, 5, 12, 0)),
    ("中午1点 午休", datetime(2026, 10, 5, 13, 0)),
    ("晚上8点 跑步", datetime(2026, 10, 5, 20, 0)),
    ("明天3点半 复习", datetime(2026, 10, 6, 3, 30)),
    ("明天下午3点半 复习", datetime(2026, 10, 6, 15, 30)),
    ("明天9:15 面试", datetime(2026, 10, 6, 9, 15)),
    ("10月20日 体检", datetime(2026, 10, 20, 9, 0)),
    ("3月1日 报税", datetime(2027, 3, 1, 9, 0)),  # 已过的日期指明年
])
def test_times(text, expected):
    assert parse(text)["due_date"] == expected


@pytest.mark.parametrize("text, name", [
    ("下载文件", "下载文件"),
    ("分享报告 #工作", "分享报告"),
    ("时间管理课程", "时间管理课程"),
    ("后端开发 明天", "后端开发"),
    ("明天3点半 复习数学", "复习数学"),
    ("前端页面优化", "前端页面优化"),
])
def test_task_name_is_not_mangled(text, name):
    assert parse(text)["task_name"] == name


@pytest.mark.parametrize("text, minutes", [
    ("写报告 2小时", 120),
    ("读书 45分钟", 45),
    ("整理房间 半小时", 30),
    ("回邮件", 30),
])
def test_duration(text, minutes):
    assert parse(text)["estimated_minutes"] == minutes


def test_no_date_means_no_due_date():
    assert parse("学习 Python")["due_date"] is None
