"""
自然语言任务解析模块
支持中文自然语言输入，自动提取时间、优先级、任务名称
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List


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

    # 时间点关键词
    TIME_POINT = {
        "早上": 8, "上午": 9, "中午": 12, "下午": 14,
        "傍晚": 17, "晚上": 19, "夜里": 22, "深夜": 23, "凌晨": 2,
    }

    # 预估时长关键词（分钟）
    DURATION_KEYWORDS = {
        "很快": 10, "一小会": 15, "半小时": 30, "一小时": 60,
        "两个小时": 120, "半天": 240, "一天": 480,
    }

    def __init__(self):
        self.now = datetime.now()

    def parse(self, text: str) -> Dict:
        """解析自然语言任务输入"""
        self.now = datetime.now()
        result = {"task_name": "", "due_date": None, "priority": 2, "estimated_minutes": 30, "tags": []}

        result["priority"] = self._extract_priority(text)
        due_date, remaining = self._extract_datetime(text)
        result["due_date"] = due_date
        duration, remaining = self._extract_duration(remaining)
        result["estimated_minutes"] = duration
        tags, remaining = self._extract_tags(remaining)
        result["tags"] = tags
        result["task_name"] = self._clean_task_name(remaining)

        return result

    def _extract_priority(self, text: str) -> int:
        for keyword, priority in self.PRIORITY_KEYWORDS.items():
            if keyword in text:
                return priority
        return 2

    def _extract_datetime(self, text: str) -> Tuple[Optional[datetime], str]:
        """提取日期时间"""
        due_date = None
        remaining = text
        time_period = None  # 记录时间段（上午/下午等）

        # 匹配 X月X日
        match = re.search(r'(\d{1,2})月(\d{1,2})[日号]?', remaining)
        if match:
            try:
                due_date = datetime(self.now.year, int(match.group(1)), int(match.group(2)))
                if due_date < self.now:
                    due_date = due_date.replace(year=self.now.year + 1)
                remaining = remaining[:match.start()] + remaining[match.end():]
            except ValueError:
                pass

        # 匹配相对日期
        relative_days = {"今天": 0, "今日": 0, "明天": 1, "明日": 1, "后天": 2, "大后天": 3}
        for keyword, days in relative_days.items():
            if keyword in remaining:
                due_date = self.now + timedelta(days=days)
                due_date = due_date.replace(hour=9, minute=0, second=0)
                remaining = remaining.replace(keyword, "", 1)
                break

        # 匹配星期几
        match = re.search(r'(下周|本)?(周|星期)(一|二|三|四|五|六|日|天)', remaining)
        if match:
            weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 5, "天": 6}
            target = weekday_map.get(match.group(3))
            if target is not None:
                days_ahead = target - self.now.weekday()
                if days_ahead <= 0 or match.group(1) == "下周":
                    days_ahead += 7
                if match.group(1) == "下周":
                    days_ahead += 7
                due_date = self.now + timedelta(days=days_ahead)
                due_date = due_date.replace(hour=9, minute=0, second=0)
                remaining = remaining[:match.start()] + remaining[match.end():]

        # 检测时间段关键词（用于下午时间+12小时）
        for keyword in ["下午", "傍晚", "晚上", "晚间", "夜里", "深夜"]:
            if keyword in remaining:
                time_period = "pm"
                remaining = remaining.replace(keyword, "", 1)
                break

        for keyword in ["上午", "早上", "早晨", "中午"]:
            if keyword in remaining:
                time_period = "am"
                remaining = remaining.replace(keyword, "", 1)
                break

        # 匹配时间点 X点/X点X分
        match = re.search(r'(\d{1,2})[点:时](\d{1,2})?分?', remaining)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2) or 0)

            # 如果是下午且小时数<12，则+12
            if time_period == "pm" and hour < 12:
                hour += 12
            # 如果是中午且小时数<12，保持原样（中午12点就是12点）
            elif time_period == "am" and hour == 12:
                hour = 0  # 上午12点=凌晨0点

            if due_date:
                due_date = due_date.replace(hour=hour, minute=minute)
            else:
                temp = self.now.replace(hour=hour, minute=minute, second=0)
                due_date = temp if temp > self.now else temp + timedelta(days=1)
            remaining = remaining[:match.start()] + remaining[match.end():]
        else:
            # 匹配时间段关键词（作为小时数）
            for keyword, hour in self.TIME_POINT.items():
                if keyword in remaining:
                    if due_date:
                        due_date = due_date.replace(hour=hour)
                    else:
                        temp = self.now.replace(hour=hour, minute=0, second=0)
                        due_date = temp if temp > self.now else temp + timedelta(days=1)
                    remaining = remaining.replace(keyword, "", 1)
                    break

        return due_date, remaining

    def _extract_duration(self, text: str) -> Tuple[int, str]:
        """提取预估时长"""
        for keyword, minutes in self.DURATION_KEYWORDS.items():
            if keyword in text:
                return minutes, text.replace(keyword, "", 1)

        match = re.search(r'(\d+)\s*(分钟|小时|天)', text)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            minutes = value if unit == "分钟" else value * 60 if unit == "小时" else value * 480
            return minutes, text[:match.start()] + text[match.end():]

        return 30, text

    def _extract_tags(self, text: str) -> Tuple[List[str], str]:
        """提取标签（#开头）"""
        tags = re.findall(r'#(\S+)', text)
        return tags, re.sub(r'#\S+', "", text)

    def _clean_task_name(self, text: str) -> str:
        """清理任务名称"""
        # 移除标点符号
        text = re.sub(r'[，。！？、；：""''（）【】\s：]+', ' ', text)

        # 移除优先级关键词
        for keyword in self.PRIORITY_KEYWORDS:
            text = text.replace(keyword, "")

        # 移除时间点关键词
        for keyword in self.TIME_POINT:
            text = text.replace(keyword, "")

        # 移除相对日期关键词
        for keyword in ["今天", "今日", "明天", "明日", "后天", "大后天", "下周", "本周", "周五", "周一", "周二", "周三", "周四", "周六", "周日"]:
            text = text.replace(keyword, "")

        # 移除时间段词汇
        time_words = ["上午", "下午", "中午", "早上", "晚上", "傍晚", "半夜", "凌晨"]
        for word in time_words:
            text = text.replace(word, "")

        # 移除时间相关词汇
        misc_words = ["前", "后", "半", "点", "分", "时", "下"]
        for word in misc_words:
            text = text.replace(word, "")

        # 移除数字+时间单位组合
        text = re.sub(r'\d+[点时分半前后]+', '', text)

        return " ".join(text.split()).strip()


def parse_natural_task(text: str) -> Dict:
    """快捷函数：解析自然语言任务"""
    return NLPTaskParser().parse(text)
