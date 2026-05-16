from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont


class BarChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(220)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        margin_left = 45
        margin_right = 15
        margin_top = 55
        margin_bottom = 45

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        if not self.data or chart_width <= 0 or chart_height <= 0:
            painter.setPen(QColor("#999"))
            painter.setFont(QFont("Microsoft YaHei", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无数据")
            return

        max_value = max((d["focus_minutes"] for d in self.data), default=0)
        if max_value == 0:
            max_value = 1

        painter.setPen(QColor("#555"))
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        painter.drawText(margin_left, 8, int(chart_width), 20, Qt.AlignLeft, "最近7天专注时长(分钟)")

        grid_lines = 5
        painter.setPen(QColor("#E0E0E0"))
        painter.setFont(QFont("Microsoft YaHei", 8))
        for i in range(grid_lines + 1):
            val = max_value * i / grid_lines
            yy = margin_top + chart_height - chart_height * i / grid_lines
            painter.drawLine(margin_left, int(yy), margin_left + chart_width, int(yy))
            painter.setPen(QColor("#888"))
            painter.drawText(5, int(yy) + 4, str(int(val)))
            painter.setPen(QColor("#E0E0E0"))

        bar_slot = chart_width / len(self.data)
        bar_width = max(bar_slot * 0.5, 15)

        for i, d in enumerate(self.data):
            x = margin_left + i * bar_slot + (bar_slot - bar_width) / 2
            bar_h = (d["focus_minutes"] / max_value) * chart_height
            if bar_h < 2 and d["focus_minutes"] > 0:
                bar_h = 2
            y = margin_top + chart_height - bar_h

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#FF8FAB"))
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_h), 4, 4)

            painter.setPen(QColor("#333"))
            painter.setFont(QFont("Microsoft YaHei", 8, QFont.Bold))
            painter.drawText(int(x), int(y) - 5, int(bar_width), 14, Qt.AlignCenter, str(d["focus_minutes"]))

            painter.setPen(QColor("#888"))
            painter.setFont(QFont("Microsoft YaHei", 8))
            date_str = d["date"][5:]
            painter.drawText(int(x), int(margin_top + chart_height + 8), int(bar_width), 14, Qt.AlignCenter, date_str)


class PieChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.completed = 0
        self.total = 0
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(220)

    def set_data(self, completed, total):
        self.completed = completed
        self.total = total
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        painter.setPen(QColor("#555"))
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        painter.drawText(15, 8, width - 30, 20, Qt.AlignLeft, "任务完成率")

        if self.total == 0:
            painter.setPen(QColor("#999"))
            painter.setFont(QFont("Microsoft YaHei", 12))
            painter.drawText(self.rect().adjusted(0, 35, 0, 0), Qt.AlignCenter, "暂无数据")
            return

        rate = self.completed / self.total * 100
        pie_area_top = 35

        pie_area_h = height - pie_area_top - 25
        size = min(width - 40, pie_area_h)
        if size < 70:
            size = 70
        x = (width - size) / 2
        y = pie_area_top + (pie_area_h - size) / 2
        rect = QRectF(x, y, size, size)

        start_angle = 90 * 16
        span_completed = -int(rate / 100 * 360 * 16)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FF8FAB"))
        if rate > 0 and span_completed < -16:
            painter.drawPie(rect, start_angle, span_completed)

        painter.setBrush(QColor("#F0F0F0"))
        if rate < 100:
            span_remaining = -360 * 16 - span_completed
            painter.drawPie(rect, start_angle + span_completed, span_remaining)
        else:
            painter.setBrush(QColor("#FF8FAB"))
            painter.drawPie(rect, start_angle, -360 * 16)

        center_size = size * 0.42
        center_rect = QRectF(x + (size - center_size) / 2, y + (size - center_size) / 2, center_size, center_size)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(center_rect)

        painter.setPen(QColor("#333"))
        painter.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        center_x = int(x + size / 2)
        center_y = int(y + size / 2)
        painter.drawText(center_x - 30, center_y - 8, 60, 18, Qt.AlignCenter, f"{rate:.0f}%")

        painter.setFont(QFont("Microsoft YaHei", 9))
        painter.setPen(QColor("#666"))
        painter.drawText(center_x - 45, center_y + 10, 90, 16, Qt.AlignCenter, f"{self.completed}/{self.total}个")
