"""
高压测试提示词
用于测试系统在极端场景下的稳定性和性能
"""

# 自然语言解析高压测试
NLP_STRESS_TESTS = [
    # 边界时间测试
    "今天23点59分提交报告",
    "明天凌晨0点5分开会",
    "12月31日23点59分完成年终总结",

    # 复杂时间表达
    "下周三下午2点半到4点开会",
    "大后天早上8点45分跑步半小时",
    "5月的第2个周一上午开例会",

    # 多任务解析
    "明天下午3点开会，后天上午10点提交报告，周五晚上看电影",
    "紧急：今天下午5点前完成PPT，明天早上9点演示",

    # 模糊表达
    "有空的时候整理一下桌面",
    "最近把那个文档写完",
    "差不多下周搞定就行",

    # 冲突优先级
    "重要但不紧急的任务：整理文件",
    "紧急但不重要的：回复垃圾邮件",
    "既重要又紧急非常关键十万火急立刻马上处理！",

    # 特殊字符和标签
    "提交代码 #开发 #紧急 #Bug修复 重要！明天中午12点",
    "写周报 #工作##重要## weekly-report ##",

    # 超长任务名
    "这是一个非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的任务名称用于测试系统对超长文本的处理能力",

    # 空白和格式异常
    "   明天   下午   3点    开会   ",
    "明天下午3点开会\n\t\t\t重要\n\n\n",

    # 数字边界
    "99月99日完成任务",  # 无效日期
    "25点61分开会",      # 无效时间
    "完成100000000个任务",  # 大数字
]

# AI对话高压测试
AI_STRESS_TESTS = [
    # 超长上下文
    """请帮我分析以下任务列表并给出优先级建议：
    任务1：完成项目文档
    任务2：修复紧急Bug
    任务3：准备周会材料
    任务4：学习新技术
    任务5：整理邮件
    ...
    （重复100次）
    """,

    # 复杂推理
    "如果任务A依赖于任务B，任务B依赖于任务C，任务C需要2小时，任务B需要3小时，任务A需要1小时，现在距离截止还有5小时，我该怎么安排？请给出详细的时间线和风险分析。",

    # 多轮对话压力
    "继续刚才的讨论，还有如果中途被打断怎么办？如果任务延期呢？如果有新任务插入呢？请分别分析每种情况的影响。",

    # 情绪极端
    "我实在太累了，任务根本做不完，压力好大，怎么办？？？救救我！！！",
    "太棒了！我居然提前完成了所有任务！系统真好用！",

    # 悖论问题
    "这个任务重要但不紧急，那个任务紧急但不重要，还有一个既重要又紧急，但我只有一个小时，怎么做？",

    # 边界条件
    "我一天有0分钟可用，帮我安排任务",
    "我有100个任务，每个需要1小时，但我只有1小时，怎么处理？",
]

# 成就系统高压测试
ACHIEVEMENT_STRESS_TESTS = {
    "快速解锁测试": [
        # 测试连续解锁
        {"action": "complete_task", "count": 500, "desc": "快速完成大量任务"},
        {"action": "pomodoro", "count": 100, "desc": "连续番茄钟"},
        {"action": "ai_call", "count": 100, "desc": "大量AI调用"},
    ],
    "边界条件测试": [
        {"action": "complete_task", "time": "05:59", "desc": "早起鸟儿边界"},
        {"action": "complete_task", "time": "06:00", "desc": "早起鸟儿不触发"},
        {"action": "complete_task", "time": "22:59", "desc": "夜猫子不触发"},
        {"action": "complete_task", "time": "23:00", "desc": "夜猫子边界"},
    ],
    "连续打卡测试": [
        {"action": "streak", "days": 99, "desc": "连续99天"},
        {"action": "streak", "days": 100, "desc": "连续100天解锁"},
        {"action": "streak", "days": 101, "desc": "连续101天"},
    ],
}

# 优先级计算高压测试
PRIORITY_STRESS_TESTS = [
    {
        "name": "过期任务大量堆积",
        "tasks": [
            {"name": f"过期任务{i}", "due_date": "-1", "priority": 5}
            for i in range(50)
        ],
        "expected": "所有过期任务应排在最前",
    },
    {
        "name": "同优先级大量任务",
        "tasks": [
            {"name": f"任务{i}", "priority": 3, "due_date": "+7"}
            for i in range(100)
        ],
        "expected": "应按创建时间等次要因素排序",
    },
    {
        "name": "极端优先级分布",
        "tasks": [
            {"name": "低优先级", "priority": 1, "due_date": "+1"},
            {"name": "高优先级", "priority": 5, "due_date": "+30"},
            {"name": "中优先级过期", "priority": 3, "due_date": "-1"},
        ],
        "expected": "过期任务 > 高优先级 > 低优先级",
    },
]

# 备份恢复高压测试
BACKUP_STRESS_TESTS = [
    {
        "name": "大数据量备份",
        "tasks_count": 10000,
        "reminders_count": 1000,
        "memories_count": 5000,
    },
    {
        "name": "特殊字符测试",
        "data": {
            "task_name": "任务<>&\"'\\n\\t\\x00特殊字符",
            "description": "包含各种特殊字符：\n\t\r\x00\xff",
        },
    },
    {
        "name": "编码测试",
        "data": {
            "task_name": "中文任务🌟🎉💻\n日本語テスト\n한국어 테스트\nÉmojis: 😀🚀✨",
        },
    },
]

# 性能基准测试
PERFORMANCE_BENCHMARKS = {
    "任务列表渲染": {"max_time_ms": 100, "items": 1000},
    "日历月视图渲染": {"max_time_ms": 200, "items": 500},
    "优先级计算": {"max_time_ms": 50, "tasks": 100},
    "自然语言解析": {"max_time_ms": 10, "text_length": 200},
    "周报生成": {"max_time_ms": 100, "tasks": 500},
    "备份创建": {"max_time_ms": 1000, "data_mb": 5},
    "数据恢复": {"max_time_ms": 2000, "data_mb": 5},
}

def run_stress_tests():
    """运行所有高压测试"""
    results = {
        "nlp": [],
        "ai": [],
        "achievement": [],
        "priority": [],
        "backup": [],
    }

    # NLP测试
    from nlp_task_parser import parse_natural_task
    for text in NLP_STRESS_TESTS:
        try:
            result = parse_natural_task(text)
            results["nlp"].append({"input": text[:50], "success": True, "output": result})
        except Exception as e:
            results["nlp"].append({"input": text[:50], "success": False, "error": str(e)})

    # 优先级测试
    from smart_priority import SmartPriorityEngine
    engine = SmartPriorityEngine()
    for test in PRIORITY_STRESS_TESTS:
        try:
            scores = [engine.calculate_smart_priority(t) for t in test["tasks"]]
            results["priority"].append({"name": test["name"], "success": True, "scores": scores})
        except Exception as e:
            results["priority"].append({"name": test["name"], "success": False, "error": str(e)})

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("高压测试提示词")
    print("=" * 60)
    print(f"\nNLP测试用例: {len(NLP_STRESS_TESTS)} 个")
    print(f"AI测试用例: {len(AI_STRESS_TESTS)} 个")
    print(f"成就测试用例: {len(ACHIEVEMENT_STRESS_TESTS)} 组")
    print(f"优先级测试用例: {len(PRIORITY_STRESS_TESTS)} 个")
    print(f"备份测试用例: {len(BACKUP_STRESS_TESTS)} 个")
    print(f"性能基准: {len(PERFORMANCE_BENCHMARKS)} 项")
