from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont


class PomodoroTimerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._target_progress = 0.0
        self.setFixedSize(240, 240)

    def get_progress(self):
        return self._progress

    def set_progress(self, value):
        self._progress = value
        self.update()

    progress = pyqtProperty(float, get_progress, set_progress)

    def set_target_progress(self, value):
        self._target_progress = value
        self._progress = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        size = min(width, height) - 30
        x = (width - size) / 2
        y = (height - size) / 2
        rect = QRectF(x, y, size, size)

        pen_bg = QPen(QColor("#F0F0F0"), 14)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 90 * 16, -360 * 16)

        if self._progress > 0:
            gradient_color = QColor("#FF8FAB")
            pen_fg = QPen(gradient_color, 14)
            pen_fg.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_fg)
            span_angle = -int(self._progress * 360 * 16)
            painter.drawArc(rect, 90 * 16, span_angle)

        painter.setPen(QColor("#FF6B8A"))
        painter.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        pct = int(self._progress * 100)
        painter.drawText(rect, Qt.AlignCenter, f"{pct}%")


class PomodoroDialog(QDialog):
    finished = pyqtSignal(int, str)

    def __init__(self, duration_minutes=25, task_name="", parent=None):
        super().__init__(parent)
        self.duration_minutes = duration_minutes
        self.task_name = task_name
        self.total_seconds = duration_minutes * 60
        self.remaining_seconds = self.total_seconds
        self.is_running = False
        self.is_paused = False

        self.setWindowTitle("🍅 番茄钟")
        self.setFixedSize(380, 480)
        self.setStyleSheet("background-color: white;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)

        self.progress_animation = QPropertyAnimation(self, b"progress")
        self.progress_animation.setDuration(300)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        if self.task_name:
            task_label = QLabel(f"📋 {self.task_name}")
            task_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            task_label.setStyleSheet("color: #333;")
            task_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(task_label)

        self.timer_widget = PomodoroTimerWidget()
        layout.addWidget(self.timer_widget, alignment=Qt.AlignCenter)

        self.time_label = QLabel(self.format_time(self.remaining_seconds))
        self.time_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        self.time_label.setStyleSheet("color: #333;")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        self.status_label = QLabel("点击开始专注")
        self.status_label.setFont(QFont("Microsoft YaHei", 12))
        self.status_label.setStyleSheet("color: #999;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.start_btn = QPushButton("▶ 开始")
        self.start_btn.setFixedSize(120, 44)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFB3CC, stop:1 #FF8FAB);
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF6B8A, stop:1 #FF8FAB);
            }
        """)
        self.start_btn.clicked.connect(self.toggle_timer)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setFixedSize(120, 44)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #B0BEC5;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #90A4AE;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_timer)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def toggle_timer(self):
        if self.is_paused:
            self.timer.start(1000)
            self.is_paused = False
            self.is_running = True
            self.start_btn.setText("⏸ 暂停")
            self.status_label.setText("专注中...")
            self.status_label.setStyleSheet("color: #4CAF50;")
        elif self.is_running:
            self.timer.stop()
            self.is_paused = True
            self.is_running = False
            self.start_btn.setText("▶ 继续")
            self.status_label.setText("已暂停")
            self.status_label.setStyleSheet("color: #FFA726;")
        else:
            self.timer.start(1000)
            self.is_running = True
            self.start_btn.setText("⏸ 暂停")
            self.status_label.setText("专注中...")
            self.status_label.setStyleSheet("color: #4CAF50;")

    def stop_timer(self):
        self.timer.stop()
        self.is_running = False
        self.is_paused = False
        self.remaining_seconds = self.total_seconds
        self.start_btn.setText("▶ 开始")
        self.status_label.setText("点击开始专注")
        self.status_label.setStyleSheet("color: #999;")
        self.update_display()

    def on_timeout(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()

        if self.remaining_seconds == 0:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText("▶ 开始")
            self.status_label.setText("🎉 完成！")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            self.finished.emit(self.duration_minutes, self.task_name)
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "专注时间到！", "🎉 专注时间到！休息一下吧。")
            self.accept()

    def update_display(self):
        self.time_label.setText(self.format_time(self.remaining_seconds))
        progress = 1.0 - (self.remaining_seconds / self.total_seconds) if self.total_seconds > 0 else 0
        self.timer_widget.set_target_progress(progress)
