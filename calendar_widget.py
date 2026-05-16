"""
日历视图组件
以日历形式展示任务和提醒
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush
from datetime import datetime


class DayCell(QFrame):
    """日期格子组件，支持右上角红点"""

    def __init__(self, day, is_today, is_selected, has_task, has_reminder, date, click_callback):
        super().__init__()
        self.day = day
        self.is_today = is_today
        self.is_selected = is_selected
        self.has_task = has_task
        self.has_reminder = has_reminder
        self.date = date
        self.click_callback = click_callback

        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)

        # 背景色和边框
        if is_selected:
            bg_color = "#FFE4E9"
            border = "2px solid #FF8FAB"
        elif is_today:
            bg_color = "#E8F5E9"
            border = "2px solid #4CAF50"
        else:
            bg_color = "#FAFAFA"
            border = "1px solid #E0E0E0"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: {border};
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: #FFF0F3;
            }}
        """)

        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 日期数字
        day_label = QLabel(str(day))
        day_label.setAlignment(Qt.AlignCenter)
        day_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold if is_today else QFont.Normal))
        day_label.setStyleSheet(f"color: {'#FF6B8A' if is_today else '#333'};")
        layout.addWidget(day_label)

    def paintEvent(self, event):
        """绘制事件，添加右上角红点"""
        super().paintEvent(event)

        if self.has_task or self.has_reminder:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 红点颜色
            painter.setBrush(QBrush(QColor("#FF4444")))
            painter.setPen(Qt.NoPen)

            # 绘制右上角红点 (半径4的圆，更靠角落)
            painter.drawEllipse(self.width() - 12, 4, 8, 8)

    def mousePressEvent(self, event):
        """点击事件"""
        if self.click_callback:
            self.click_callback(self.date)


class CalendarWidget(QWidget):
    """日历视图组件"""

    task_clicked = pyqtSignal(object)  # 点击任务时发出信号

    def __init__(self, task_manager=None, reminder_manager=None, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.reminder_manager = reminder_manager
        self.current_date = QDate.currentDate()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 顶部导航
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ 上月")
        self.prev_btn.setFixedHeight(36)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #FF6B8A; }
        """)
        self.prev_btn.clicked.connect(self.prev_month)
        nav_layout.addWidget(self.prev_btn)

        self.month_label = QLabel()
        self.month_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        self.month_label.setAlignment(Qt.AlignCenter)
        self.month_label.setStyleSheet("color: #333;")
        nav_layout.addWidget(self.month_label, stretch=1)

        self.next_btn = QPushButton("下月 ▶")
        self.next_btn.setFixedHeight(36)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #FF6B8A; }
        """)
        self.next_btn.clicked.connect(self.next_month)
        nav_layout.addWidget(self.next_btn)

        self.today_btn = QPushButton("今天")
        self.today_btn.setFixedHeight(36)
        self.today_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.today_btn.clicked.connect(self.go_today)
        nav_layout.addWidget(self.today_btn)

        layout.addLayout(nav_layout)

        # 星期标题
        weekday_layout = QHBoxLayout()
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for day in weekdays:
            label = QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
            if day in ["周六", "周日"]:
                label.setStyleSheet("color: #FF8FAB; padding: 10px;")
            else:
                label.setStyleSheet("color: #666; padding: 10px;")
            weekday_layout.addWidget(label)
        layout.addLayout(weekday_layout)

        # 日历网格
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(2)
        layout.addLayout(self.calendar_grid)

        # 选中日期的任务列表
        self.task_list_label = QLabel("点击日期查看任务")
        self.task_list_label.setFont(QFont("Microsoft YaHei", 12))
        self.task_list_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.task_list_label)

        self.task_scroll = QScrollArea()
        self.task_scroll.setWidgetResizable(True)
        self.task_scroll.setStyleSheet("border: none;")
        self.task_scroll.setMinimumHeight(120)
        self.task_container = QWidget()
        self.task_container_layout = QVBoxLayout(self.task_container)
        self.task_container_layout.setContentsMargins(5, 5, 5, 5)
        self.task_container_layout.setSpacing(5)
        self.task_container_layout.addStretch()
        self.task_scroll.setWidget(self.task_container)
        layout.addWidget(self.task_scroll)

        self.update_calendar()
        self.setStyleSheet("background-color: white;")

    def update_calendar(self):
        """更新日历显示"""
        # 清除现有格子
        while self.calendar_grid.count():
            item = self.calendar_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 更新月份标题
        self.month_label.setText(f"{self.current_date.year()}年 {self.current_date.month()}月")

        # 计算月份第一天是星期几（周一=0）
        first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
        start_weekday = first_day.dayOfWeek() - 1  # 转换为 0=周一

        # 计算天数
        days_in_month = first_day.daysInMonth()

        # 填充日历
        today = QDate.currentDate()
        selected_date = self.selected_date if hasattr(self, 'selected_date') else None

        # 上个月的空白
        for i in range(start_weekday):
            cell = self._create_empty_cell()
            self.calendar_grid.addWidget(cell, 0, i)

        # 当月日期
        row, col = 0, start_weekday
        for day in range(1, days_in_month + 1):
            date = QDate(self.current_date.year(), self.current_date.month(), day)
            is_today = (date == today)
            is_selected = (date == selected_date)
            has_task = self._has_task_on_date(date)
            has_reminder = self._has_reminder_on_date(date)

            cell = self._create_day_cell(day, is_today, is_selected, has_task, has_reminder, date)
            self.calendar_grid.addWidget(cell, row, col)

            col += 1
            if col >= 7:
                col = 0
                row += 1

        # 下个月的空白
        while col < 7 and col > 0:
            cell = self._create_empty_cell()
            self.calendar_grid.addWidget(cell, row, col)
            col += 1

    def _create_day_cell(self, day, is_today, is_selected, has_task, has_reminder, date):
        """创建日期格子"""
        cell = DayCell(day, is_today, is_selected, has_task, has_reminder, date, self._on_date_clicked)
        return cell

    def _create_empty_cell(self):
        """创建空白格子"""
        cell = QFrame()
        cell.setFixedHeight(50)
        cell.setStyleSheet("background-color: transparent;")
        return cell

    def _has_task_on_date(self, date: QDate) -> bool:
        """检查该日期是否有任务"""
        if not self.task_manager:
            return False

        target_date = date.toPyDate()
        for task in self.task_manager.tasks:
            if task.due_date:
                try:
                    # due_date 是字符串格式 "YYYY-MM-DD HH:MM"
                    if isinstance(task.due_date, str):
                        task_date = datetime.strptime(task.due_date[:10], "%Y-%m-%d").date()
                    elif hasattr(task.due_date, 'date'):
                        task_date = task.due_date.date()
                    else:
                        task_date = task.due_date

                    if task_date == target_date:
                        return True
                except (ValueError, TypeError):
                    continue
        return False

    def _has_reminder_on_date(self, date: QDate) -> bool:
        """检查该日期是否有提醒"""
        if not self.reminder_manager:
            return False

        target_date = date.toPyDate()
        for reminder in self.reminder_manager.reminders:
            remind_date = reminder.remind_time.date() if hasattr(reminder.remind_time, 'date') else reminder.remind_time
            if remind_date == target_date:
                return True
        return False

    def _on_date_clicked(self, date: QDate):
        """日期被点击"""
        self.selected_date = date
        self.update_calendar()
        self._show_tasks_for_date(date)

    def _show_tasks_for_date(self, date: QDate):
        """显示指定日期的任务"""
        # 清空现有任务列表
        while self.task_container_layout.count() > 1:
            item = self.task_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        target_date = date.toPyDate()
        tasks_found = []
        reminders_found = []

        # 查找任务
        if self.task_manager:
            for task in self.task_manager.tasks:
                if task.due_date:
                    try:
                        # due_date 是字符串格式 "YYYY-MM-DD HH:MM"
                        if isinstance(task.due_date, str):
                            task_date = datetime.strptime(task.due_date[:10], "%Y-%m-%d").date()
                        elif hasattr(task.due_date, 'date'):
                            task_date = task.due_date.date()
                        else:
                            task_date = task.due_date

                        if task_date == target_date:
                            tasks_found.append(task)
                    except (ValueError, TypeError):
                        continue

        # 查找提醒
        if self.reminder_manager:
            for reminder in self.reminder_manager.reminders:
                try:
                    remind_date = reminder.remind_time.date() if hasattr(reminder.remind_time, 'date') else reminder.remind_time
                    if remind_date == target_date:
                        reminders_found.append(reminder)
                except (ValueError, TypeError):
                    continue

        # 更新标题
        date_str = date.toString("yyyy年MM月dd日")
        self.task_list_label.setText(f"📅 {date_str} 的任务和提醒")

        # 显示任务
        for task in tasks_found:
            task_widget = self._create_task_item(task, "task")
            self.task_container_layout.insertWidget(self.task_container_layout.count() - 1, task_widget)

        for reminder in reminders_found:
            reminder_widget = self._create_task_item(reminder, "reminder")
            self.task_container_layout.insertWidget(self.task_container_layout.count() - 1, reminder_widget)

        if not tasks_found and not reminders_found:
            empty_label = QLabel("暂无任务或提醒")
            empty_label.setStyleSheet("color: #999; padding: 20px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.task_container_layout.insertWidget(0, empty_label)

    def _create_task_item(self, item, item_type):
        """创建任务/提醒条目"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #FFF0F3;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)

        if item_type == "task":
            icon = "📋"
            # 处理 due_date，可能是字符串或 datetime
            time_str = ""
            if item.due_date:
                if isinstance(item.due_date, str):
                    # 字符串格式 "YYYY-MM-DD HH:MM"
                    if len(item.due_date) >= 16:
                        time_str = item.due_date[11:16]  # 提取 "HH:MM"
                elif hasattr(item.due_date, 'strftime'):
                    time_str = item.due_date.strftime("%H:%M")
            title = item.name
            completed = item.completed
        else:
            icon = "⏰"
            # 处理 remind_time，可能是字符串或 datetime
            time_str = ""
            if item.remind_time:
                if isinstance(item.remind_time, str):
                    if len(item.remind_time) >= 16:
                        time_str = item.remind_time[11:16]
                elif hasattr(item.remind_time, 'strftime'):
                    time_str = item.remind_time.strftime("%H:%M")
            title = item.title
            completed = False

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 11))
        title_label.setStyleSheet(f"color: {'#999' if completed else '#333'}; text-decoration: {'line-through' if completed else 'none'};")
        info_layout.addWidget(title_label)

        if time_str:
            time_label = QLabel(time_str)
            time_label.setStyleSheet("color: #888; font-size: 11px;")
            info_layout.addWidget(time_label)

        layout.addLayout(info_layout, stretch=1)

        return widget

    def prev_month(self):
        """上个月"""
        self.current_date = self.current_date.addMonths(-1)
        self.update_calendar()

    def next_month(self):
        """下个月"""
        self.current_date = self.current_date.addMonths(1)
        self.update_calendar()

    def go_today(self):
        """回到今天"""
        self.current_date = QDate.currentDate()
        self.selected_date = self.current_date
        self.update_calendar()
        self._show_tasks_for_date(self.current_date)

    def refresh(self):
        """刷新日历"""
        self.update_calendar()
        if hasattr(self, 'selected_date') and self.selected_date:
            self._show_tasks_for_date(self.selected_date)
