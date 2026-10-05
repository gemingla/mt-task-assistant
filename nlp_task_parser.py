"""
自然语言任务解析模块
支持中文自然语言输入，自动提取时间、优先级、任务名称

例：「明天下午3点开会 #工作 重要」→ 名称“开会”，明天 15:00，标签 工作，优先级 4
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List


def _longest_first(words):
    """关键词按长度降序，保证“不紧急”优先于“紧急”、“大后天”优先于“后天”"""
    return sorted(words, key=len, reverse=True)


class NLPTaskParser:
    """自然语言任务解析器"""

    # 优先级关键词（合并同类）
    PRIORITY_KEYWORDS = {
        "紧急": 5, "非常紧急": 5, "十万火急": 5, "立刻": 5, "马上": 5,
        "重要": 4, "很关键": 4, "关键": 4, "优先": 4,
        "比较重要": 3, "挺重要": 3,
        "一般": 2, "普通": 2,
        "不急": 1, "不紧急": 1, "有空做": 1, "闲时": 1,
    }

    # 只有时间段、没有具体钟点时使用的默认小时
    TIME_POINT = {
        "早上": 8, "早晨": 8, "上午": 9, "中午": 12, "下午": 14,
        "傍晚": 17, "晚上": 19, "晚间": 19, "夜里": 22, "深夜": 23, "凌晨": 2,
    }
    PM_WORDS = ("下午", "傍晚", "晚上", "晚间", "夜里", "深夜")
    NOON_WORDS = ("中午",)

    RELATIVE_DAYS = {"今天": 0, "今日": 0, "明天": 1, "明日": 1, "后天": 2, "大后天": 3}
    WEEKDAYS = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
    DEFAULT_HOUR = 9  # 只给了日期时默认上午 9 点

    # 预估时长关键词（分钟）
    DURATION_KEYWORDS = {
        "很快": 10, "一小会": 15, "半小时": 30, "一小时": 60, "一个小时": 60,
        "两个小时": 120, "两小时": 120, "半天": 240, "一天": 480,
    }

    _DATE_RE = re.compile(r'(\d{1,2})月(\d{1,2})[日号]?')
    _WEEKDAY_RE = re.compile(r'(下个?|本|这)?(周|星期|礼拜)([一二三四五六日天])')
    # 3点 / 3点半 / 3点15 / 3点15分 / 9:15 / 9：15
    _TIME_RE = re.compile(r'(\d{1,2})\s*(?:[点时](?!间)|[:：])\s*(半|\d{1,2})?\s*分?')
    _DURATION_RE = re.compile(r'(\d+)\s*(分钟|个小时|小时|天)')

    def __init__(self):
        self.now = datetime.now()

    def parse(self, text: str, now: Optional[datetime] = None) -> Dict:
        """解析自然语言任务输入；now 仅用于测试时固定当前时间"""
        self.now = now or datetime.now()
        result = {"task_name": "", "due_date": None, "priority": 2, "estimated_minutes": 30, "tags": []}

        tags, remaining = self._extract_tags(text)
        result["tags"] = tags
        result["priority"] = self._extract_priority(remaining)
        due_date, remaining = self._extract_datetime(remaining)
        result["due_date"] = due_date
        duration, remaining = self._extract_duration(remaining)
        result["estimated_minutes"] = duration
        result["task_name"] = self._clean_task_name(remaining)

        return result

    def _extract_priority(self, text: str) -> int:
        for keyword in _longest_first(self.PRIORITY_KEYWORDS):
            if keyword in text:
                return self.PRIORITY_KEYWORDS[keyword]
        return 2

    @staticmethod
    def _cut(text: str, match) -> str:
        return text[:match.start()] + " " + text[match.end():]

    def _extract_datetime(self, text: str) -> Tuple[Optional[datetime], str]:
        """提取日期时间，返回 (截止时间, 去掉时间描述后的剩余文本)"""
        remaining = text
        day = None  # date 对象

        # 1. X月X日
        match = self._DATE_RE.search(remaining)
        if match:
            try:
                candidate = datetime(self.now.year, int(match.group(1)), int(match.group(2))).date()
                if candidate < self.now.date():
                    candidate = candidate.replace(year=self.now.year + 1)
                day = candidate
                remaining = self._cut(remaining, match)
            except ValueError:
                pass

        # 2. 今天/明天/后天/大后天
        if day is None:
            for keyword in _longest_first(self.RELATIVE_DAYS):
                if keyword in remaining:
                    day = (self.now + timedelta(days=self.RELATIVE_DAYS[keyword])).date()
                    remaining = remaining.replace(keyword, " ", 1)
                    break

        # 3. 周X / 下周X
        if day is None:
            match = self._WEEKDAY_RE.search(remaining)
            if match:
                target = self.WEEKDAYS[match.group(3)]
                today = self.now.weekday()
                prefix = match.group(1) or ""
                if prefix.startswith("下"):
                    days_ahead = (7 - today) + target          # 下周的星期 target
                elif prefix in ("本", "这"):
                    days_ahead = target - today                 # 可以是今天或已过去
                else:
                    days_ahead = (target - today) % 7 or 7      # 下一个星期 target（不含今天）
                day = (self.now + timedelta(days=days_ahead)).date()
                remaining = self._cut(remaining, match)

        # 4. 时间段词（上午/下午/中午…）
        period = None
        for keyword in _longest_first(self.TIME_POINT):
            if keyword in remaining:
                period = keyword
                remaining = remaining.replace(keyword, " ", 1)
                break

        # 5. 具体钟点
        hour = minute = None
        match = self._TIME_RE.search(remaining)
        if match:
            hour = int(match.group(1))
            minute_text = match.group(2)
            minute = 30 if minute_text == "半" else int(minute_text or 0)
            if period in self.PM_WORDS and hour < 12:
                hour += 12
            elif period in self.NOON_WORDS and hour <= 2:
                hour += 12  # 中午1点 = 13:00；中午12点保持 12:00
            if hour > 23 or minute > 59:
                hour = minute = None
            else:
                remaining = self._cut(remaining, match)
        if hour is None and period:
            hour, minute = self.TIME_POINT[period], 0

        if day is None and hour is None:
            return None, remaining

        if day is not None:
            if hour is None:
                hour, minute = self.DEFAULT_HOUR, 0
            return datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute), remaining

        # 只有钟点：今天该时间已过则顺延到明天
        due = self.now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if due <= self.now:
            due += timedelta(days=1)
        return due, remaining

    def _extract_duration(self, text: str) -> Tuple[int, str]:
        """提取预估时长"""
        for keyword in _longest_first(self.DURATION_KEYWORDS):
            if keyword in text:
                return self.DURATION_KEYWORDS[keyword], text.replace(keyword, " ", 1)

        match = self._DURATION_RE.search(text)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            minutes = value if unit == "分钟" else value * 480 if unit == "天" else value * 60
            return minutes, self._cut(text, match)

        return 30, text

    def _extract_tags(self, text: str) -> Tuple[List[str], str]:
        """提取标签（#开头，到空白或下一个 # 为止）"""
        tags = re.findall(r'#([^\s#]+)', text)
        return tags, re.sub(r'#[^\s#]+', " ", text)

    def _clean_task_name(self, text: str) -> str:
        """清理任务名称：只去掉标点和优先级词，不再逐字删除“下/分/时/后”等，避免误伤“下载”“分享”"""
        text = re.sub(r'[，。！？、；：,.!?;:"“”‘’（）()【】\[\]]+', ' ', text)
        for keyword in _longest_first(self.PRIORITY_KEYWORDS):
            text = text.replace(keyword, " ")
        return " ".join(text.split()).strip()


def parse_natural_task(text: str) -> Dict:
    """快捷函数：解析自然语言任务"""
    return NLPTaskParser().parse(text)
