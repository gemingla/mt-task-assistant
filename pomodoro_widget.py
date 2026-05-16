from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QGraphicsOpacityEffect
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QRectF, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from glass_style import apply_glass_style, apply_glass_style_secondary, apply_input_style


class PomodoroWidget(QWidget):
    finished = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 25 * 60
        self.remaining_seconds = self.total_seconds
        self.is_running = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)
        self.animation_progress = 0.0
        self.current_task = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.task_label = QLabel("未选择任务")
        self.task_label.setFont(QFont("Microsoft YaHei", 11))
        self.task_label.setStyleSheet("color: #666; padding: 5px;")
        self.task_label.setAlignment(Qt.AlignCenter)
        self.task_label.setMaximumHeight(30)
        layout.addWidget(self.task_label)

        self.pomodoro_canvas = PomodoroCanvas(self.total_seconds, self)
        self.pomodoro_canvas.setFixedWidth(220)
        self.pomodoro_canvas.setFixedHeight(220)
        layout.addWidget(self.pomodoro_canvas, alignment=Qt.AlignCenter)

        self.time_label = QLabel("00:25:00")
        self.time_label.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
        self.time_label.setStyleSheet("color: #333;")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        self.status_label = QLabel("准备开始")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_label.setStyleSheet("color: #999;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.start_btn = QPushButton("▶ 开始专注")
        apply_glass_style(self.start_btn, border_radius=20, padding="10px 28px")
        self.start_btn.setFixedHeight(44)
        self.start_btn.clicked.connect(self.toggle_timer)
        controls_layout.addWidget(self.start_btn)

        self.reset_btn = QPushButton("↺ 重置")
        apply_glass_style_secondary(self.reset_btn, border_radius=20, padding="10px 24px")
        self.reset_btn.setFixedHeight(44)
        self.reset_btn.clicked.connect(self.reset_timer)
        controls_layout.addWidget(self.reset_btn)

        layout.addLayout(controls_layout)

        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("⏱ 时长(分钟):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 180)
        self.duration_spin.setValue(25)
        self.duration_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #FF8FAB;
            }
        """)
        self.duration_spin.setFixedWidth(80)
        self.duration_spin.valueChanged.connect(self.on_duration_changed)
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        layout.addLayout(duration_layout)

    def set_task(self, task):
        self.current_task = task
        if task:
            self.task_label.setText(f"📋 {task.name}")
            self.task_label.setStyleSheet("color: #FF6B8A; padding: 5px; font-weight: bold;")
        else:
            self.task_label.setText("未选择任务")
            self.task_label.setStyleSheet("color: #666; padding: 5px;")

    def toggle_timer(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText("▶ 继续")
            self.status_label.setText("已暂停")
            self.status_label.setStyleSheet("color: #FFA726;")
        else:
            self.timer.start(1000)
            self.is_running = True
            self.start_btn.setText("⏸ 暂停")
            self.duration_spin.setEnabled(False)
            self.status_label.setText("专注中...")
            self.status_label.setStyleSheet("color: #4CAF50;")

    def reset_timer(self):
        self.timer.stop()
        self.is_running = False
        self.remaining_seconds = self.total_seconds
        self.start_btn.setText("▶ 开始专注")
        self.duration_spin.setEnabled(True)
        self.status_label.setText("准备开始")
        self.status_label.setStyleSheet("color: #999;")
        self.update_display()

    def on_duration_changed(self, value):
        if not self.is_running:
            self.total_seconds = value * 60
            self.remaining_seconds = self.total_seconds
            self.update_display()

    def on_timeout(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()
        if self.remaining_seconds == 0:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText("▶ 开始专注")
            self.duration_spin.setEnabled(True)
            self.status_label.setText("🎉 完成！")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.finished.emit(self.total_seconds // 60, self.current_task)

    def update_display(self):
        hours = self.remaining_seconds // 3600
        minutes = (self.remaining_seconds % 3600) // 60
        seconds = self.remaining_seconds % 60
        if hours > 0:
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
        self.pomodoro_canvas.set_progress(
            1.0 - self.remaining_seconds / self.total_seconds if self.total_seconds > 0 else 0
        )


class PomodoroCanvas(QWidget):
    def __init__(self, total_seconds, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.target_progress = 0.0

    def set_progress(self, value):
        self.target_progress = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        size = min(width, height) - 20
        x = (width - size) / 2
        y = (height - size) / 2
        rect = QRectF(x, y, size, size)

        bg_color = QColor("#F0F0F0")
        pen_bg = QPen(bg_color, 12)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 90 * 16, -360 * 16)

        pen_fg = QPen(QColor("#FF8FAB"), 12)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)

        if self.target_progress > 0:
            span_angle = -int(self.target_progress * 360 * 16)
            painter.drawArc(rect, 90 * 16, span_angle)

        painter.setPen(QColor("#FF6B8A"))
        painter.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        pct = int(self.target_progress * 100)
        painter.drawText(rect, Qt.AlignCenter, f"{pct}%")
