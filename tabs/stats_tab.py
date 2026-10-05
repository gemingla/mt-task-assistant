"""数据统计标签页"""
from ui_common import *  # noqa: F401,F403


class StatsTab(QWidget):
    def __init__(self, stats_manager, task_manager, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.task_manager = task_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stats_widget = StatisticsWidget(self.stats_manager, self.task_manager, self)
        layout.addWidget(self.stats_widget)

    def refresh_stats(self):
        self.stats_widget.refresh_data()
