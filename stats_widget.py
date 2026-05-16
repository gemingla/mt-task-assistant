import json
import os
from datetime import datetime, timedelta
from utils import get_data_path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 获取数据文件的正确路径（已移至 utils.get_data_path）


class StatisticsWidget(QWidget):
    def __init__(self, stats_manager=None, task_manager=None, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.task_manager = task_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("📊 数据统计")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedSize(90, 36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFB3CC, stop:1 #FF8FAB);
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF6B8A, stop:1 #FF8FAB);
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor='#F8F8F8')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumHeight(400)
        layout.addWidget(self.canvas)
        
        self.refresh_data()
        
    def load_stats_data(self):
        stats_file = get_data_path("stats.json")
        if os.path.exists(stats_file):
            try:
                with open(stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def load_tasks_data(self):
        tasks_file = get_data_path("tasks.json")
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def get_last_7_days_data(self, stats_data):
        result = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            data = stats_data.get(date, {"focus_minutes": 0})
            result.append({
                "date": date,
                "focus_minutes": data.get("focus_minutes", 0)
            })
        return result
    
    def refresh_data(self):
        self.figure.clear()

        stats_data = self.load_stats_data()
        tasks_data = self.load_tasks_data()

        has_focus_data = any(
            stats_data.get(date, {}).get("focus_minutes", 0) > 0
            for date in stats_data
        )

        total_tasks = len(tasks_data)
        completed_tasks = len([t for t in tasks_data if t.get("completed", False)])

        if not has_focus_data and total_tasks == 0:
            self.show_no_data_message()
            return

        try:
            gs = self.figure.add_gridspec(1, 2, width_ratios=[1.2, 1], wspace=0.25,
                                           left=0.08, right=0.95, top=0.9, bottom=0.15)

            ax1 = self.figure.add_subplot(gs[0, 0])
            self.draw_bar_chart(ax1, stats_data)

            ax2 = self.figure.add_subplot(gs[0, 1])
            self.draw_pie_chart(ax2, total_tasks, completed_tasks)

            self.canvas.draw()
        except Exception as e:
            import traceback, datetime
            err_msg = f"图表渲染失败: {e}\n{traceback.format_exc()}"
            print(err_msg)
            try:
                with open("crash.log", "a", encoding="utf-8") as lf:
                    lf.write(f"\n===== {datetime.datetime.now()} =====\n{err_msg}\n")
            except Exception:
                pass
            self.show_no_data_message()
    
    def show_no_data_message(self):
        ax = self.figure.add_subplot(111)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.text(0.5, 0.5, '暂无统计数据\n\n开始使用番茄钟或添加任务后\n这里将显示统计图表', 
                ha='center', va='center', fontsize=14, color='#999',
                fontfamily='Microsoft YaHei')
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.canvas.draw()
    
    def draw_bar_chart(self, ax, stats_data):
        data = self.get_last_7_days_data(stats_data)
        dates = [d["date"][5:] for d in data]
        minutes = [d["focus_minutes"] for d in data]
        
        colors = ['#FFB3CC' if m == 0 else '#FF8FAB' for m in minutes]
        
        bars = ax.bar(dates, minutes, color=colors, edgecolor='white', linewidth=1.2)
        
        ax.set_title('最近7天专注时长(分钟)', fontsize=12, fontweight='bold', color='#333', pad=10)
        ax.set_xlabel('日期', fontsize=10, color='#666')
        ax.set_ylabel('专注时长(分钟)', fontsize=10, color='#666')
        
        ax.set_ylim(0, max(minutes) * 1.2 if max(minutes) > 0 else 60)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#E0E0E0')
        ax.spines['bottom'].set_color('#E0E0E0')
        
        ax.tick_params(axis='both', colors='#666', labelsize=9)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color='#E0E0E0')
        ax.set_axisbelow(True)
        
        for bar, val in zip(bars, minutes):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                       str(int(val)), ha='center', va='bottom', fontsize=9,
                       color='#333', fontweight='bold')
    
    def draw_pie_chart(self, ax, total, completed):
        if total == 0:
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            ax.text(0.5, 0.5, '暂无任务数据', ha='center', va='center', 
                   fontsize=12, color='#999', fontfamily='Microsoft YaHei')
            return
        
        uncompleted = total - completed
        rate = completed / total * 100
        
        sizes = [completed, uncompleted]
        labels = [f'已完成\n{completed}个', f'未完成\n{uncompleted}个']
        colors = ['#FF8FAB', '#E8E8E8']
        explode = (0.03, 0)
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors,
                                          explode=explode, autopct='',
                                          startangle=90, 
                                          wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        
        for text in texts:
            text.set_fontsize(9)
            text.set_color('#666')
        
        ax.set_title(f'任务完成率 ({rate:.1f}%)', fontsize=12, fontweight='bold', 
                    color='#333', pad=10)
        
        centre_circle = plt.Circle((0, 0), 0.5, fc='white', edgecolor='white')
        ax.add_patch(centre_circle)
        
        ax.text(0, 0.05, f'{rate:.0f}%', ha='center', va='center', 
               fontsize=18, fontweight='bold', color='#FF6B8A')
        ax.text(0, -0.15, f'{completed}/{total}', ha='center', va='center',
               fontsize=10, color='#666')
        
        ax.axis('equal')


class StatisticsWindow(QWidget):
    def __init__(self, stats_manager=None, task_manager=None, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        self.task_manager = task_manager
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("📊 统计图表")
        self.setMinimumSize(800, 550)
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stats_widget = StatisticsWidget(
            self.stats_manager, 
            self.task_manager, 
            self
        )
        layout.addWidget(self.stats_widget)
        
        self.setStyleSheet("background-color: #F8F8F8;")
    
    def refresh_data(self):
        self.stats_widget.refresh_data()
