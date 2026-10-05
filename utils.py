"""
通用工具函数
避免代码重复，提供统一的日期解析、任务属性获取和数据路径获取
"""

import json
import os
import shutil
import sys
import traceback
from datetime import datetime, timedelta
from typing import Optional, Tuple


def get_data_path(relative_path: str = "") -> str:
    """
    获取数据文件的写入路径（打包后为 exe 同级目录，开发环境为项目目录）
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    if relative_path:
        return os.path.join(base, relative_path)
    return base


LOG_MAX_BYTES = 1024 * 1024


def log_error(message: str):
    """把错误信息追加写入数据目录下的 crash.log（不再依赖当前工作目录），超过 1MB 时轮转"""
    try:
        path = get_data_path("crash.log")
        if os.path.exists(path) and os.path.getsize(path) > LOG_MAX_BYTES:
            os.replace(path, path + ".1")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n===== {datetime.now()} =====\n{message}\n")
    except Exception:
        pass


def atomic_write_json(path: str, data, indent: int = 2):
    """
    原子写入 JSON：先写临时文件并刷盘，再用 os.replace 替换原文件。
    替换前把旧文件复制为 .bak，写到一半崩溃也不会留下空文件。
    失败时抛出异常，由调用方决定如何处理。
    """
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
        f.flush()
        os.fsync(f.fileno())
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            shutil.copyfile(path, f"{path}.bak")
        except OSError:
            pass
    os.replace(tmp_path, path)


def load_json_with_backup(path: str, default=None):
    """
    读取 JSON；主文件缺失、为空或损坏时自动回退到 .bak。
    两者都不可用时返回 default。
    """
    for candidate in (path, f"{path}.bak"):
        if not os.path.exists(candidate) or os.path.getsize(candidate) == 0:
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                data = json.load(f)
            if candidate != path:
                log_error(f"[{path}] 主文件不可用，已从备份 {candidate} 恢复")
            return data
        except Exception:
            log_error(f"读取 JSON 失败 [{candidate}]:\n{traceback.format_exc()}")
    return default


def parse_datetime(value) -> Optional[datetime]:
    """
    统一的日期时间解析

    支持格式：
    - datetime 对象
    - "YYYY-MM-DD HH:MM" 字符串
    - "YYYY-MM-DD HH:MM:SS" 字符串
    - "YYYY-MM-DD" 字符串

    Args:
        value: 日期值（字符串或datetime对象）

    Returns:
        datetime 对象或 None
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        # 尝试多种格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value[:len(datetime.now().strftime(fmt))], fmt)
            except (ValueError, TypeError):
                continue

    return None


def parse_date(value) -> Optional[datetime.date]:
    """
    解析为 date 对象（不含时间）

    Args:
        value: 日期值

    Returns:
        date 对象或 None
    """
    dt = parse_datetime(value)
    return dt.date() if dt else None


def format_datetime(value, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """
    格式化日期时间

    Args:
        value: 日期值
        fmt: 输出格式

    Returns:
        格式化字符串
    """
    dt = parse_datetime(value)
    return dt.strftime(fmt) if dt else ""


def get_date_str(value) -> str:
    """
    获取日期字符串部分 (YYYY-MM-DD)

    Args:
        value: 日期值

    Returns:
        日期字符串
    """
    if isinstance(value, str) and len(value) >= 10:
        return value[:10]
    dt = parse_datetime(value)
    return dt.strftime("%Y-%m-%d") if dt else ""


def get_time_str(value) -> str:
    """
    获取时间字符串部分 (HH:MM)

    Args:
        value: 日期值

    Returns:
        时间字符串
    """
    if isinstance(value, str) and len(value) >= 16:
        return value[11:16]
    dt = parse_datetime(value)
    return dt.strftime("%H:%M") if dt else ""


def get_task_attr(task, attr: str, default=None):
    """
    安全获取任务属性

    Args:
        task: 任务对象
        attr: 属性名
        default: 默认值

    Returns:
        属性值或默认值
    """
    return getattr(task, attr, default)


def is_task_overdue(task) -> bool:
    """
    判断任务是否过期

    Args:
        task: 任务对象

    Returns:
        是否过期
    """
    if task.completed:
        return False

    due_date = get_task_attr(task, 'due_date')
    if not due_date:
        return False

    dt = parse_datetime(due_date)
    return dt < datetime.now() if dt else False


def get_task_due_status(task) -> Tuple[str, int]:
    """
    获取任务截止状态

    Returns:
        (状态描述, 剩余秒数)
        状态: "overdue", "today", "tomorrow", "this_week", "later"
    """
    due_date = get_task_attr(task, 'due_date')
    if not due_date:
        return "no_deadline", 0

    dt = parse_datetime(due_date)
    if not dt:
        return "unknown", 0

    diff = (dt - datetime.now()).total_seconds()

    if diff < 0:
        return "overdue", diff
    elif diff < 86400:  # 24小时
        return "today", diff
    elif diff < 172800:  # 48小时
        return "tomorrow", diff
    elif diff < 604800:  # 7天
        return "this_week", diff
    else:
        return "later", diff


# 优先级名称映射
PRIORITY_NAMES = {
    1: "低",
    2: "普通",
    3: "中高",
    4: "高",
    5: "紧急"
}


def get_priority_name(priority: int) -> str:
    """获取优先级名称"""
    return PRIORITY_NAMES.get(priority, "普通")


def get_weekday_name(weekday: int, short: bool = True) -> str:
    """
    获取星期名称

    Args:
        weekday: 0-6 (周一到周日)
        short: 是否简写

    Returns:
        星期名称
    """
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    full_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return names[weekday] if short else full_names[weekday]
