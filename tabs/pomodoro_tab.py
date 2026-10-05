"""番茄钟标签页"""
from ui_common import *  # noqa: F401,F403


class PomodoroTab(QWidget):
    def __init__(self, stats_manager, task_manager=None, refresh_callback=None, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.task_manager = task_manager
        self.refresh_callback = refresh_callback
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        self.pomodoro = PomodoroWidget()
        self.pomodoro.finished.connect(self.on_pomodoro_finished)
        layout.addWidget(self.pomodoro, alignment=Qt.AlignCenter)

        title_label = QLabel("🍅 番茄钟")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.insertWidget(0, title_label)

    def on_pomodoro_finished(self, minutes, task):
        self.stats_manager.add_focus_time(minutes)

        # 成就系统：记录番茄钟完成
        main_window = self.get_main_window() if hasattr(self, 'get_main_window') else None
        if main_window and hasattr(main_window, 'achievement_manager'):
            new_achievements = main_window.achievement_manager.record_pomodoro(minutes)
            if new_achievements:
                from achievement_manager import show_achievement_notification
                show_achievement_notification(new_achievements, main_window)

        if task and self.task_manager and self.refresh_callback:
            self.task_manager.toggle_complete(task.id)
            self.refresh_callback()
            QMessageBox.information(self, "🎉 完成！",
                f"太棒了！你专注了 {minutes} 分钟！\n任务「{task.name}」已自动标记为完成！")
        else:
            QMessageBox.information(self, "🎉 完成！", f"太棒了！你专注了 {minutes} 分钟！")
