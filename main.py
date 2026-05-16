import sys
import os
import json
import ctypes
from datetime import datetime

# PyInstaller 资源路径处理
def resource_path(relative_path):
    """获取资源文件的正确路径（开发环境或打包后）"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Windows 系统通知
try:
    from winotify import Notification, audio
    WINOTIFY_AVAILABLE = True
except ImportError:
    WINOTIFY_AVAILABLE = False

# ===== Windows 原生弹窗（ctypes 方式，exe 环境最可靠）=====
def show_native_toast(title: str, message: str) -> bool:
    """
    使用 PowerShell 调用 Windows Toast 通知，不依赖 winotify 的 Python 路径注册。
    在 PyInstaller 打包的 exe 中也能正常工作。
    """
    import subprocess
    try:
        # 转义单引号
        title_escaped = title.replace("'", "''")
        msg_escaped = message.replace("'", "''")
        ps_script = (
            '& {'
            f'$title = \'{title_escaped}\';'
            f'$msg = \'{msg_escaped}\';'
            '$load = [Windows.UI.Notifications.ToastNotificationManager,'
            'Windows.UI.Notifications,ContentType=WindowsRuntime];'
            '$template = [Windows.UI.Notifications.ToastNotificationManager]'
            '::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);'
            '$textNodes = $template.GetElementsByTagName("text");'
            '$textNodes.Item(0).AppendChild($template.CreateTextNode($title)) | Out-Null;'
            '$textNodes.Item(1).AppendChild($template.CreateTextNode($msg)) | Out-Null;'
            '$toast = [Windows.UI.Notifications.ToastNotification]::new($template);'
            '[Windows.UI.Notifications.ToastNotificationManager]'
            '::CreateToastNotifier("MT任务助手").Show($toast);'
            '}'
        )
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_script],
            capture_output=True, timeout=10
        )
        return True
    except Exception:
        return False
# ============================================================

try:
    import PyQt5
    pyqt5_path = os.path.dirname(PyQt5.__file__)
    plugins_path = os.path.join(pyqt5_path, "Qt5", "plugins", "platforms")
    if os.path.exists(plugins_path):
        ctypes.windll.kernel32.SetDllDirectoryW(plugins_path)
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path
except Exception:
    pass
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QTextEdit, QPushButton, QLineEdit, QLabel,
    QDialog, QGridLayout, QMessageBox, QInputDialog, QApplication,
    QTabWidget, QFrame, QStackedWidget, QCheckBox, QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect, QSpinBox, QComboBox, QDateTimeEdit,
    QListWidget, QListWidgetItem, QAbstractItemView, QWizard, QSystemTrayIcon,
    QWizardPage, QTextBrowser, QColorDialog, QGroupBox, QVBoxLayout as QGVBoxLayout,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QVariantAnimation, pyqtSignal, QPoint, QMimeData, QTimer, QSize, QThread, QDateTime, QTime
from PyQt5.QtGui import QFont, QColor, QDrag, QPixmap, QIcon
import webbrowser

from config import ConfigManager
from task_manager import TaskManager
from stats_manager import StatsManager
from reminder_manager import ReminderManager, Reminder
from tag_manager import TagManager
from ai_client import AIClient, call_ai, call_ai_stream, get_models, render_latex
# 优化版 AI 客户端
from ai_client_optimized import call_ai_optimized, call_ai_stream_optimized, get_optimized_client
from pomodoro_widget import PomodoroWidget
from pomodoro_dialog import PomodoroDialog
from stats_chart_widget import BarChartWidget, PieChartWidget
from stats_widget import StatisticsWidget
from utils import get_data_path
from memory_manager import MemoryManager
try:
    from voice_input import get_voice_input, get_default_model_path
    HAS_VOICE_INPUT = True
except ImportError:
    HAS_VOICE_INPUT = False
    get_voice_input = None
    get_default_model_path = None
# AI 伦理模块
from ai_ethics_module import AIEthicsAnalyzer, AIEthicsWidget
# 快速入门教程
from welcome_wizard import show_welcome_wizard, should_show_wizard, mark_wizard_shown, WelcomeWizard
# 数据备份
from backup_manager import BackupManager
# 日历视图
from calendar_widget import CalendarWidget
# 成就系统
from achievement_manager import AchievementManager, AchievementDialog, show_achievement_notification


class AsyncAPICall(QThread):
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, messages, parent=None, use_optimized=True):
        super().__init__(parent)
        self.messages = messages
        self.use_optimized = use_optimized

    def run(self):
        try:
            # 使用优化版 API 调用
            if self.use_optimized:
                result = call_ai_optimized(self.messages)
            else:
                result = call_ai(self.messages)
            
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit("API 返回为空")
        except Exception as e:
            self.error_occurred.emit(str(e))


class AsyncAPICallStream(QThread):
    chunk_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)
    stream_finished = pyqtSignal(str)

    def __init__(self, messages, parent=None, use_optimized=True):
        super().__init__(parent)
        self.messages = messages
        self.use_optimized = use_optimized

    def run(self):
        try:
            # 使用优化版流式 API 调用
            if self.use_optimized:
                call_ai_stream_optimized(
                    self.messages,
                    on_chunk=lambda chunk, acc: self.chunk_ready.emit(chunk, acc),
                    on_error=lambda e: self.error_occurred.emit(e),
                    on_complete=lambda r: self.stream_finished.emit(r)
                )
            else:
                call_ai_stream(
                    self.messages,
                    on_chunk=lambda chunk, acc: self.chunk_ready.emit(chunk, acc),
                    on_error=lambda e: self.error_occurred.emit(e),
                    on_complete=lambda r: self.stream_finished.emit(r)
                )
        except Exception as e:
            self.error_occurred.emit(str(e))


from glass_style import (
    apply_glass_style, apply_glass_style_secondary, apply_glass_style_danger,
    apply_glass_style_light, apply_glass_style_icon, apply_input_style, apply_checkbox_style,
    apply_card_style, apply_scrollbar_style, apply_tab_style, apply_spinbox_style,
    apply_combobox_style, apply_textedit_style, set_completed_style, FadeAnimation,
    GLOBAL_BG_COLOR, THEME_COLOR, HOVER_COLOR, CARD_BG_COLOR, TEXT_COLOR, SUBTEXT_COLOR, COMPLETED_BG_COLOR
)

try:
    import speech_recognition as sr
    HAS_SPEECH = True
except ImportError:
    HAS_SPEECH = False

TASK_CARD_STYLE = """
QFrame#task-card {
    background-color: white;
    border-radius: 12px;
    border: 1px solid #E8E8E8;
}
QFrame#task-card:hover {
    border: 1px solid #FFB3CC;
    background-color: #FFFAFB;
}
"""

TASK_CARD_COMPLETED_STYLE = """
QFrame#task-card {
    background-color: #F8F8F8;
    border-radius: 12px;
    border: 1px solid #E0E0E0;
}
QFrame#task-card:hover {
    border: 1px solid #C8E6C9;
}
"""

class TaskCardWidget(QFrame):
    deleteRequested = pyqtSignal(object)
    completionToggled = pyqtSignal(object)
    focusRequested = pyqtSignal(object)
    renameRequested = pyqtSignal(object, str)
    tagClicked = pyqtSignal(str)  # 标签点击信号

    def __init__(self, task, task_manager, stats_manager, tag_manager, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.task = task
        self.task_manager = task_manager
        self.stats_manager = stats_manager
        self.tag_manager = tag_manager
        self._delete_anim = None
        self._check_anim = None
        self._bounce_anim = None
        self.init_ui()
        self.update_completed_style()

    def format_time(self, minutes):
        if minutes >= 60:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours}小时"
            return f"{hours}小时{mins}分钟"
        return f"{minutes}分钟"

    def init_ui(self):
        self.setObjectName("taskCardWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Plain)
        self.setMinimumHeight(85)
        self.setMinimumWidth(450)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(15)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.setFixedSize(28, 28)
        apply_checkbox_style(self.checkbox)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox, 0, Qt.AlignVCenter)

        self.name_label = QLabel(self.task.name)
        self.name_label.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        self.name_label.setStyleSheet("color: #999; text-decoration: line-through; background-color: transparent;" if self.task.completed else "color: #333; background-color: transparent;")
        self.name_label.setCursor(Qt.PointingHandCursor)
        self.name_label.setWordWrap(True)  # 允许文本换行
        self.name_label.setToolTip(self.task.name)  # 鼠标悬停显示完整文本
        self.name_label.mouseDoubleClickEvent = self.on_name_double_click
        layout.addWidget(self.name_label, stretch=1)
        
        # 添加标签显示
        if hasattr(self.task, 'tags') and self.task.tags:
            tags_widget = QWidget()
            tags_layout = QHBoxLayout(tags_widget)
            tags_layout.setContentsMargins(0, 0, 0, 0)
            tags_layout.setSpacing(6)
            
            for tag in self.task.tags[:3]:  # 最多显示3个标签
                tag_label = QLabel(tag)  # 去掉"#"符号
                tag_label.setCursor(Qt.PointingHandCursor)  # 鼠标悬停时显示手型
                tag_label.setToolTip(f"点击筛选「{tag}」标签的任务")
                # 使用tag_manager获取标签样式（可点击）
                tag_label.setStyleSheet(self.tag_manager.get_tag_style(tag, clickable=True))
                # 启用鼠标跟踪
                tag_label.setMouseTracking(True)
                # 使用事件过滤器处理点击
                tag_label.installEventFilter(self)
                # 存储标签名称用于事件过滤
                tag_label.setProperty("tag_name", tag)
                tags_layout.addWidget(tag_label)
            
            tags_layout.addStretch()
            layout.addWidget(tags_widget)

        due_date_text = self.format_due_date(self.task.due_date)
        if due_date_text:
            self.due_label = QLabel(due_date_text)
            self.due_label.setObjectName("dueLabel")
            self.due_label.setStyleSheet("color: #EF4444; font-size: 12px; background-color: transparent; font-weight: bold;")
            self.due_label.setAlignment(Qt.AlignVCenter)
            self.due_label.setCursor(Qt.PointingHandCursor)
            self.due_label.setToolTip("双击修改截止时间")
            self.due_label.mouseDoubleClickEvent = self.on_due_date_double_click
            layout.addWidget(self.due_label, alignment=Qt.AlignVCenter)

        time_text = self.format_time(self.task.estimated_minutes)
        self.time_label = QLabel(f"⏱ {time_text}")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setStyleSheet("color: #666666; font-size: 12px; background-color: transparent;")
        self.time_label.setAlignment(Qt.AlignVCenter)
        self.time_label.setCursor(Qt.PointingHandCursor)
        self.time_label.setToolTip("双击修改预估时长")
        self.time_label.mouseDoubleClickEvent = self.on_time_double_click
        layout.addWidget(self.time_label, alignment=Qt.AlignVCenter)

        self.focus_btn = QPushButton("🎯")
        self.focus_btn.setFixedSize(44, 44)
        self.focus_btn.setCursor(Qt.PointingHandCursor)
        self.focus_btn.setToolTip("开始专注")
        self.focus_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #EC407A;
            }
        """)
        self.focus_btn.clicked.connect(self.on_focus_clicked)
        if self.task.completed:
            self.focus_btn.hide()
        layout.addWidget(self.focus_btn)

        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(36, 36)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setToolTip("删除任务")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #BBBBBB;
                border: 1px solid #DDDDDD;
                border-radius: 18px;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
                color: #EF4444;
                border: 1px solid #FFCDD2;
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.delete_btn)

    def format_due_date(self, due_date):
        if not due_date:
            return ""
        try:
            if isinstance(due_date, datetime):
                due = due_date
            else:
                due = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            now = datetime.now()
            if due.date() == now.date():
                return f"今日 {due.strftime('%H:%M')}"
            elif (due.date() - now.date()).days == 1:
                return f"明日 {due.strftime('%H:%M')}"
            elif due.year == now.year:
                return due.strftime("%m月%d日 %H:%M")
            else:
                return due.strftime("%Y年%m月%d日 %H:%M")
        except:
            return due_date

    def update_completed_style(self):
        if self.task.completed:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F0FDF4;
                    border: 1.5px solid #86EFAC;
                    border-radius: 14px;
                }
            """)
            self.name_label.setStyleSheet("color: #166534; text-decoration: line-through; background-color: transparent;")
            self.time_label.setStyleSheet("color: #22C55E; font-size: 12px; background-color: transparent;")
            self.focus_btn.hide()
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 1px solid #E8E8E8;
                    border-radius: 14px;
                }
                QFrame:hover {
                    border: 1.5px solid #FFB3CC;
                    background-color: #FFFAFB;
                }
            """)
            self.name_label.setStyleSheet("color: #333333; background-color: transparent;")
            self.time_label.setStyleSheet("color: #666666; font-size: 12px; background-color: transparent;")

    def animate_checkbox(self):
        pulse_effect = QGraphicsDropShadowEffect(self.checkbox)
        pulse_effect.setBlurRadius(20)
        pulse_effect.setColor(QColor(76, 175, 80))
        pulse_effect.setOffset(0, 0)
        self.checkbox.setGraphicsEffect(pulse_effect)
        self._check_anim = QPropertyAnimation(pulse_effect, b"blurRadius")
        self._check_anim.setDuration(400)
        self._check_anim.setStartValue(20)
        self._check_anim.setEndValue(0)
        self._check_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._check_anim.finished.connect(lambda: self.checkbox.setGraphicsEffect(None))
        self._check_anim.start()

    def start_fade_out(self, callback):
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)
        
        self._delete_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._delete_anim.setDuration(300)
        self._delete_anim.setStartValue(1.0)
        self._delete_anim.setEndValue(0.0)
        self._delete_anim.setEasingCurve(QEasingCurve.InCubic)
        self._delete_anim.finished.connect(callback)
        self._delete_anim.start()

    def on_checkbox_changed(self, state):
        self.animate_checkbox()
        # 完成任务时播放弹跳动画
        if state == Qt.Checked:
            self._play_complete_bounce()
        QTimer.singleShot(100, self._do_checkbox_change)

    def _play_complete_bounce(self):
        """完成任务时的弹跳庆祝效果"""
        from animation_utils import BounceAnimation
        self._bounce_anim = BounceAnimation(self, 400)
        self._bounce_anim.bounce()

    def _do_checkbox_change(self):
        task = self.task_manager.toggle_complete(self.task.id)
        if task:
            self.task = task
            self.update_completed_style()
            if task.completed:
                self.stats_manager.add_task_completed()
                # 成就系统：记录任务完成
                main_window = self.get_main_window()
                if main_window and hasattr(main_window, 'achievement_manager'):
                    new_achievements = main_window.achievement_manager.record_task_completed()
                    if new_achievements:
                        from achievement_manager import show_achievement_notification
                        show_achievement_notification(new_achievements, main_window)
            self.completionToggled.emit(self.task)

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理标签点击"""
        from PyQt5.QtCore import QEvent
        # 检查是否是标签的鼠标点击事件
        if event.type() == QEvent.MouseButtonPress:
            # 检查对象是否有 tag_name 属性
            if hasattr(obj, 'property') and obj.property("tag_name"):
                tag = obj.property("tag_name")
                self.on_tag_clicked(tag)
                return True
        return super().eventFilter(obj, event)

    def on_tag_clicked(self, tag: str):
        """标签点击事件"""
        if self.task.completed:
            return
        self.tagClicked.emit(tag)
    
    def on_focus_clicked(self):
        self.focusRequested.emit(self.task)

    def on_delete_clicked(self):
        self.start_fade_out(lambda: self.deleteRequested.emit(self.task))

    def on_name_double_click(self, event):
        if self.task.completed:
            return
        self.name_edit = QLineEdit(self.task.name)
        self.name_edit.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #FF8FAB;
                border-radius: 5px;
                padding: 2px 5px;
            }
        """)
        self.name_edit.selectAll()
        self.name_edit.returnPressed.connect(self.save_name_edit)
        self.name_edit.focusOutEvent = lambda e: self.save_name_edit()

        layout = self.layout()
        layout.replaceWidget(self.name_label, self.name_edit)
        self.name_label.hide()
        self.name_edit.setFocus()

    def save_name_edit(self):
        new_name = self.name_edit.text().strip()
        if new_name:
            self.task_manager.update_task(self.task.id, name=new_name)
            self.task.name = new_name
        self.name_label.setText(self.task.name)
        layout = self.layout()
        layout.replaceWidget(self.name_edit, self.name_label)
        self.name_edit.deleteLater()
        self.name_label.show()
        if new_name:
            self.renameRequested.emit(self.task, new_name)

    def on_due_date_double_click(self, event):
        """双击截止时间进行编辑"""
        if self.task.completed:
            return
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QDateTimeEdit, QPushButton, QCheckBox

        # 获取主窗口作为父级
        main_window = self.get_main_window() if hasattr(self, 'get_main_window') else self.window()

        dialog = QDialog(main_window)
        dialog.setWindowTitle("修改截止时间")
        dialog.setFixedSize(320, 220)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground, False)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #FF8FAB;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel("修改截止时间")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setStyleSheet("color: #333333; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 时间选择器
        datetime_edit = QDateTimeEdit()
        datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        datetime_edit.setCalendarPopup(True)
        datetime_edit.setFixedHeight(36)

        # 设置当前值
        if self.task.due_date:
            try:
                due_str = self.task.due_date.strftime("%Y-%m-%d %H:%M") if isinstance(self.task.due_date, datetime) else self.task.due_date[:16]
                dt = QDateTime.fromString(due_str, "yyyy-MM-dd HH:mm")
                datetime_edit.setDateTime(dt)
            except:
                datetime_edit.setDateTime(QDateTime.currentDateTime())
        else:
            datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))

        datetime_edit.setStyleSheet("""
            QDateTimeEdit {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QDateTimeEdit:focus { border-color: #FF8FAB; }
        """)
        layout.addWidget(datetime_edit)

        # 无截止时间选项
        no_due_checkbox = QCheckBox("无截止时间")
        no_due_checkbox.setStyleSheet("QCheckBox { font-size: 12px; color: #666666; background: transparent; }")
        layout.addWidget(no_due_checkbox)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(70, 32)
        cancel_btn.setStyleSheet("""
            QPushButton { background: #F5F5F5; color: #666666; border: none; border-radius: 6px; font-size: 13px; }
            QPushButton:hover { background: #E0E0E0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(70, 32)
        ok_btn.setStyleSheet("""
            QPushButton { background: #FF8FAB; color: white; border: none; border-radius: 6px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background: #FF6B8A; }
        """)

        def save_due():
            if no_due_checkbox.isChecked():
                new_due = None
            else:
                new_due = datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm")

            self.task_manager.update_task(self.task.id, due_date=new_due)
            self.task.due_date = new_due

            # 更新显示
            due_text = self.format_due_date(new_due)
            if hasattr(self, 'due_label') and self.due_label:
                self.due_label.setText(due_text)

            dialog.accept()

        ok_btn.clicked.connect(save_due)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 居中显示
        dialog.move(
            main_window.geometry().center().x() - dialog.width() // 2,
            main_window.geometry().center().y() - dialog.height() // 2
        )

        dialog.exec_()

    def on_time_double_click(self, event):
        """双击预估时长进行编辑"""
        if self.task.completed:
            return
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSpinBox, QLabel, QPushButton

        # 获取主窗口作为父级
        main_window = self.get_main_window() if hasattr(self, 'get_main_window') else self.window()

        dialog = QDialog(main_window)
        dialog.setWindowTitle("修改预估时长")
        dialog.setFixedSize(300, 180)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground, False)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #FF8FAB;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel("修改预估时长")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setStyleSheet("color: #333333; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 时长选择
        time_layout = QHBoxLayout()
        time_layout.addStretch()

        hours_spin = QSpinBox()
        hours_spin.setRange(0, 24)
        hours_spin.setValue(self.task.estimated_minutes // 60)
        hours_spin.setFixedSize(60, 32)
        hours_spin.setAlignment(Qt.AlignCenter)
        hours_spin.setStyleSheet("""
            QSpinBox { background: #F5F5F5; border: 1px solid #E0E0E0; border-radius: 6px; padding: 4px; font-size: 14px; }
            QSpinBox:focus { border-color: #FF8FAB; }
        """)
        time_layout.addWidget(hours_spin)
        time_layout.addWidget(QLabel("小时"))

        minutes_spin = QSpinBox()
        minutes_spin.setRange(0, 59)
        minutes_spin.setValue(self.task.estimated_minutes % 60)
        minutes_spin.setFixedSize(60, 32)
        minutes_spin.setAlignment(Qt.AlignCenter)
        minutes_spin.setStyleSheet(hours_spin.styleSheet())
        time_layout.addWidget(minutes_spin)
        time_layout.addWidget(QLabel("分钟"))
        time_layout.addStretch()

        layout.addLayout(time_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(70, 32)
        cancel_btn.setStyleSheet("""
            QPushButton { background: #F5F5F5; color: #666666; border: none; border-radius: 6px; font-size: 13px; }
            QPushButton:hover { background: #E0E0E0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(70, 32)
        ok_btn.setStyleSheet("""
            QPushButton { background: #FF8FAB; color: white; border: none; border-radius: 6px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background: #FF6B8A; }
        """)

        def save_time():
            total_minutes = hours_spin.value() * 60 + minutes_spin.value()
            if total_minutes == 0:
                total_minutes = 30

            self.task_manager.update_task(self.task.id, estimated_minutes=total_minutes)
            self.task.estimated_minutes = total_minutes

            time_text = self.format_time(total_minutes)
            self.time_label.setText(f"⏱ {time_text}")

            dialog.accept()

        ok_btn.clicked.connect(save_time)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 居中显示
        dialog.move(
            main_window.geometry().center().x() - dialog.width() // 2,
            main_window.geometry().center().y() - dialog.height() // 2
        )

        dialog.exec_()

    def get_main_window(self):
        """获取主窗口对象"""
        widget = self.parent()
        while widget:
            if isinstance(widget, MainWindow):
                return widget
            widget = widget.parent()
        return None


class TaskCard(QFrame):
    """已弃用 - 保留仅为兼容性，请使用 TaskCardWidget"""
    opacityChanged = pyqtSignal(float)

    def __init__(self, task, task_manager, stats_manager, refresh_callback, focus_callback=None, parent=None):
        super().__init__(parent)
        # 转发到新的 TaskCardWidget
        self._delegate = TaskCardWidget(task, task_manager, stats_manager, parent)

    def update_completed_style(self):
        if self.task.completed:
            self.setStyleSheet("""
                QFrame#taskCard {
                    background-color: #E8F5E9;
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#taskCard {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 10px;
                }
                QFrame#taskCard:hover {
                    border: 1px solid #FFB6C1;
                }
            """)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        if self.opacity_effect:
            self.opacity_effect.setOpacity(value)
        self.opacityChanged.emit(value)

    opacity = pyqtProperty(float, get_opacity, set_opacity, notify=opacityChanged)

    @property
    def animations(self):
        if self._animation_manager is None:
            self._animation_manager = AnimationManager(self)
        return self._animation_manager

    def start_fade_in(self):
        self.opacity_effect.setOpacity(0.0)
        self._opacity = 0.0
        self.fade_anim = QVariantAnimation(self)
        self.fade_anim.setDuration(400)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_anim.valueChanged.connect(lambda v: self.opacity_effect.setOpacity(v))
        self.fade_anim.start()

    def start_fade_out(self, callback):
        self.fade_anim = QVariantAnimation(self)
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.fade_anim.valueChanged.connect(lambda v: self.opacity_effect.setOpacity(v))
        self.fade_anim.finished.connect(callback)
        self.fade_anim.start()

    def animate_completion(self, completed):
        self.update_completed_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_start_pos:
            diff = event.pos() - self.drag_start_pos
            if diff.manhattanLength() > 10:
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(str(id(self)))
                drag.setMimeData(mime_data)
                drag.setPixmap(self.grab())
                drag.setHotSpot(self.rect().center())
                self.setOpacity(0.5)
                drag.exec_(Qt.MoveAction)
                self.setOpacity(1.0)
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFF8E1;
                    border: 2px dashed #FFC107;
                    border-radius: 10px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.update_completed_style()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.update_completed_style()
        event.acceptProposedAction()

        source_card = None
        parent_widget = self.parent()
        if parent_widget and isinstance(parent_widget, QWidget):
            task_layout = parent_widget.layout()
            if task_layout:
                for i in range(task_layout.count()):
                    widget = task_layout.itemAt(i).widget()
                    if widget and isinstance(widget, TaskCard) and widget != self:
                        card_rect = widget.rect().translated(widget.pos())
                        if card_rect.contains(self.mapTo(widget, event.pos())):
                            source_card = widget
                            break

        if source_card:
            parent_widget = self.parent()
            if parent_widget and isinstance(parent_widget, QWidget):
                task_layout = parent_widget.layout()
                if task_layout:
                    from_idx = task_layout.indexOf(source_card)
                    to_idx = task_layout.indexOf(self)
                    if from_idx != -1 and to_idx != -1 and from_idx != to_idx:
                        QTimer.singleShot(100, self.refresh_callback)

    def setOpacity(self, opacity):
        if self.opacity_effect:
            self.opacity_effect.setOpacity(opacity)

    def format_time(self, minutes):
        if minutes >= 60:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours}小时"
            return f"{hours}小时{mins}分钟"
        return f"{minutes}分钟"

    def init_ui(self):
        self.setObjectName("taskCard")
        self.setMinimumHeight(70)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.setFixedSize(28, 28)
        apply_checkbox_style(self.checkbox)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox, 0, Qt.AlignVCenter)

        self.name_label = QLabel(self.task.name)
        self.name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.name_label.setStyleSheet("color: #999; text-decoration: line-through;" if self.task.completed else "color: #333;")
        self.name_label.setCursor(Qt.PointingHandCursor)
        self.name_label.setWordWrap(True)  # 允许文本换行
        self.name_label.setToolTip(self.task.name)  # 鼠标悬停显示完整文本
        self.name_label.mouseDoubleClickEvent = self.on_name_double_click
        layout.addWidget(self.name_label, stretch=1)

        time_text = self.format_time(self.task.estimated_minutes)
        self.time_label = QLabel(f"⏱ {time_text}")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.time_label)

        self.focus_btn = QPushButton("🎯")
        self.focus_btn.setFixedSize(38, 38)
        self.focus_btn.setCursor(Qt.PointingHandCursor)
        self.focus_btn.setToolTip("开始专注")
        self.focus_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 182, 193, 0.7);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 19px;
                font-size: 18px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(229, 57, 89, 0.8);
            }
        """)
        self.focus_btn.clicked.connect(self.on_focus_clicked)
        if self.task.completed:
            self.focus_btn.hide()
        layout.addWidget(self.focus_btn)

        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setToolTip("删除任务")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(255, 107, 138, 0.6);
                border: 1px solid rgba(255, 107, 138, 0.3);
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 235, 238, 0.9);
                color: rgba(229, 57, 53, 0.95);
                border: 1px solid rgba(255, 107, 138, 0.7);
            }
        """)
        self.delete_btn.clicked.connect(self.delete_card)
        layout.addWidget(self.delete_btn)

        self.bg_animation = QVariantAnimation(self)
        self.bg_animation.setDuration(400)
        self.bg_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.bg_animation.valueChanged.connect(self.on_bg_color_changed)

    def on_checkbox_changed(self, state):
        task = self.task_manager.toggle_complete(self.task.id)
        if task:
            self.task = task
            if task.completed:
                self.stats_manager.add_task_completed()
                self.animate_bg_color(QColor(255, 255, 255), QColor(232, 245, 233))
                self.name_label.setStyleSheet("color: #999; text-decoration: line-through;")
                self.focus_btn.hide()
            else:
                self.animate_bg_color(QColor(232, 245, 233), QColor(255, 255, 255))
                self.name_label.setStyleSheet("color: #333;")
                self.focus_btn.show()

            if self.refresh_callback:
                main_window = self.get_main_window()
                if main_window and hasattr(main_window, 'stats_tab'):
                    main_window.stats_tab.refresh_stats()

    def get_main_window(self):
        widget = self.parent()
        while widget:
            if isinstance(widget, MainWindow):
                return widget
            widget = widget.parent()
        return None

    def animate_bg_color(self, from_color, to_color):
        self.bg_animation.stop()
        self.bg_animation.setStartValue(from_color)
        self.bg_animation.setEndValue(to_color)
        self.bg_animation.start()

    def on_bg_color_changed(self, color):
        r, g, b, a = color.getRgb()
        is_completed = g > 240
        border_color = "#4CAF50" if is_completed else "#E0E0E0"
        border_width = "2px" if is_completed else "1px"
        self.setStyleSheet(f"""
            QFrame#taskCard {{
                background-color: rgb({r}, {g}, {b});
                border: {border_width} solid {border_color};
                border-radius: 10px;
            }}
        """)

    def on_name_double_click(self, event):
        self.name_edit = QLineEdit(self.task.name)
        self.name_edit.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #FF8FAB;
                border-radius: 5px;
                padding: 2px 5px;
            }
        """)
        self.name_edit.selectAll()
        self.name_edit.returnPressed.connect(self.save_name_edit)
        self.name_edit.focusOutEvent = lambda e: self.save_name_edit()

        layout = self.layout()
        layout.replaceWidget(self.name_label, self.name_edit)
        self.name_label.hide()
        self.name_edit.setFocus()

    def save_name_edit(self):
        new_name = self.name_edit.text().strip()
        if new_name:
            self.task_manager.update_task(self.task.id, name=new_name)
            self.task.name = new_name
        self.name_label.setText(self.task.name)
        layout = self.layout()
        layout.replaceWidget(self.name_edit, self.name_label)
        self.name_edit.deleteLater()
        self.name_label.show()

    def on_focus_clicked(self):
        if self.focus_callback:
            self.focus_callback(self.task)

    def delete_card(self):
        self.task_manager.delete_task(self.task.id)
        self.start_fade_out(self.refresh_callback)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.setWindowTitle("设置")
        self.setFixedSize(600, 700)
        self.setStyleSheet("background-color: #FAFAFA;")
        self.init_ui()
        self.load_config()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # ========== 基础设置分组 ==========
        api_group = QGroupBox("⚙️ 基础设置")
        api_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                color: #FF8FAB;
                border: 2px solid #FFE4E9;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """)
        api_layout = QGridLayout(api_group)
        api_layout.setSpacing(12)
        api_layout.setContentsMargins(15, 20, 15, 15)

        api_layout.addWidget(QLabel("API 地址:"), 0, 0)
        self.api_address_edit = QLineEdit()
        self.api_address_edit.setPlaceholderText("https://api.example.com/v1")
        apply_input_style(self.api_address_edit)
        api_layout.addWidget(self.api_address_edit, 0, 1)

        api_layout.addWidget(QLabel("API Key:"), 1, 0)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("输入你的 API Key")
        apply_input_style(self.api_key_edit)
        api_layout.addWidget(self.api_key_edit, 1, 1)

        api_layout.addWidget(QLabel("模型名称:"), 2, 0)
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setPlaceholderText("选择或输入模型名称")
        apply_combobox_style(self.model_combo)
        self.model_combo.setMinimumWidth(200)
        self.model_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        model_layout.addWidget(self.model_combo)

        self.fetch_models_btn = QPushButton("获取")
        self.fetch_models_btn.setFixedSize(60, 36)
        apply_glass_style_secondary(self.fetch_models_btn, border_radius=8, padding="6px 12px", font_size=12)
        self.fetch_models_btn.clicked.connect(self.fetch_models)
        model_layout.addWidget(self.fetch_models_btn)
        api_layout.addLayout(model_layout, 2, 1)

        api_layout.addWidget(QLabel("系统人设:"), 3, 0)
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setPlaceholderText("输入 AI 的系统提示词...")
        self.system_prompt_edit.setMaximumHeight(100)
        apply_textedit_style(self.system_prompt_edit)
        api_layout.addWidget(self.system_prompt_edit, 3, 1)

        main_layout.addWidget(api_group)

        # ========== 启动设置分组 ==========
        startup_group = QGroupBox("⚡ 启动设置")
        startup_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                color: #FF8FAB;
                border: 2px solid #FFE4E9;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """)
        startup_layout = QVBoxLayout(startup_group)
        startup_layout.setContentsMargins(15, 20, 15, 15)

        self.auto_start_checkbox = QCheckBox("🖥️ 开机自动启动")
        self.auto_start_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #E0E0E0;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #FF8FAB;
                border-color: #FF8FAB;
            }
            QCheckBox::indicator:hover {
                border-color: #FFB6C1;
            }
        """)
        startup_layout.addWidget(self.auto_start_checkbox)

        main_layout.addWidget(startup_group)

        # ========== 按钮 ==========
        main_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.wizard_button = QPushButton("🧭 打开向导")
        self.wizard_button.setFixedHeight(42)
        apply_glass_style_secondary(self.wizard_button)
        self.wizard_button.clicked.connect(self.open_wizard)
        btn_layout.addWidget(self.wizard_button)
        self.save_button = QPushButton("💾 保存配置")
        self.save_button.setFixedHeight(42)
        apply_glass_style(self.save_button)
        self.save_button.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_button)
        main_layout.addLayout(btn_layout)

    def open_wizard(self):
        from PyQt5.QtWidgets import QDialog
        wizard = ApiWizard(self)
        wizard.exec_()

    def fetch_models(self):
        api_url = self.api_address_edit.text().strip()
        api_key = self.api_key_edit.text().strip()

        if not api_url or not api_key:
            QMessageBox.warning(self, "提示", "请先输入 API 地址和 API Key")
            return

        self.fetch_models_btn.setText("获取中...")
        self.fetch_models_btn.setEnabled(False)
        QApplication.processEvents()

        def on_error(msg):
            QMessageBox.warning(self, "错误", msg)

        models = get_models(api_url, api_key, callback=on_error)

        self.fetch_models_btn.setText("获取")
        self.fetch_models_btn.setEnabled(True)

        if models:
            self.model_combo.clear()
            self.model_combo.addItems(models)
            self.model_combo.setCurrentIndex(0)
            self.model_combo.showPopup()
            QMessageBox.information(self, "成功", f"已获取 {len(models)} 个模型\n请点击下拉框选择模型")

    def load_config(self):
        config = self.config_manager.load_config()
        self.api_address_edit.setText(config.get("api_url", ""))
        self.api_key_edit.setText(config.get("api_key", ""))
        current_model = config.get("model", "")
        if current_model:
            self.model_combo.setCurrentText(current_model)
        self.system_prompt_edit.setPlainText(config.get("system_prompt", ""))
        # 加载开机自启动设置
        self.auto_start_checkbox.setChecked(config.get("auto_start", False))

    def save_config(self):
        config = {
            "api_url": self.api_address_edit.text(),
            "api_key": self.api_key_edit.text(),
            "model": self.model_combo.currentText(),
            "system_prompt": self.system_prompt_edit.toPlainText(),
            "auto_start": self.auto_start_checkbox.isChecked()
        }
        self.config_manager.save_config(config)

        # 设置或取消开机自启动
        self.set_auto_start(self.auto_start_checkbox.isChecked())

        QMessageBox.information(self, "成功", "配置已保存！")
        self.accept()

    def set_auto_start(self, enable: bool):
        """设置开机自启动"""
        import winreg
        app_name = "MT任务助手"
        app_path = os.path.abspath(sys.argv[0])

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )

            if enable:
                # 添加开机自启动
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
            else:
                # 删除开机自启动
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # 值不存在，忽略

            winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"设置开机自启动失败: {e}")

    def get_config(self):
        return {
            "api_url": self.api_address_edit.text(),
            "api_key": self.api_key_edit.text(),
            "model": self.model_combo.currentText(),
            "system_prompt": self.system_prompt_edit.toPlainText()
        }


class IntroPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("介绍")
        self.setSubTitle("欢迎使用 API 配置向导")

        layout = QVBoxLayout()
        title_label = QLabel("<h2>🔑 API 配置向导</h2>")
        title_label.setStyleSheet("color: #FF8FAB;")
        layout.addWidget(title_label)

        desc_label = QLabel(
            "<p>本向导将帮助您完成以下步骤：</p>"
            "<ul>"
            "<li>📝 注册 DeepSeek 账号</li>"
            "<li>🔐 创建 API Key</li>"
            "<li>⚙️ 配置 API 参数</li>"
            "<li>✅ 测试连接</li>"
            "</ul>"
            "<p>请点击「下一步」继续。</p>"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; line-height: 1.8;")
        layout.addWidget(desc_label)
        layout.addStretch()
        self.setLayout(layout)


class RegisterPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("注册 DeepSeek")
        self.setSubTitle("第一步：创建 DeepSeek 账号")

        layout = QVBoxLayout()

        desc_label = QLabel(
            "<p>要使用 DeepSeek API，您需要先注册一个 DeepSeek 账号。</p>"
            "<p><b>操作步骤：</b></p>"
            "<ol>"
            "<li>访问 DeepSeek 开放平台</li>"
            "<li>使用手机号注册账号（支持 +86 中国手机号）</li>"
            "<li>登录后即可获取 API Key</li>"
            "</ol>"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; line-height: 1.8;")
        layout.addWidget(desc_label)

        self.register_btn = QPushButton("🌐 打开 DeepSeek 注册页面")
        self.register_btn.setFixedHeight(45)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
        """)
        self.register_btn.clicked.connect(self.open_register_page)
        layout.addWidget(self.register_btn)

        hint_label = QLabel("💡 提示：注册需要中国手机号（+86）")
        hint_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(hint_label)
        layout.addStretch()
        self.setLayout(layout)

    def open_register_page(self):
        webbrowser.open("https://platform.deepseek.com/")


class CreateKeyPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("创建 API Key")
        self.setSubTitle("第二步：在 DeepSeek 平台创建 API Key")

        layout = QVBoxLayout()

        desc_label = QLabel(
            "<p><b>创建 API Key 步骤：</b></p>"
            "<ol>"
            "<li>登录 <a href='https://platform.deepseek.com/'>DeepSeek 开放平台</a></li>"
            "<li>进入「API Keys」页面</li>"
            "<li>点击「创建 API Key」按钮</li>"
            "<li>输入 Key 名称（如：MT助手）</li>"
            "<li>复制生成的 API Key</li>"
            "</ol>"
            "<p>⚠️ 请妥善保管您的 API Key，不要泄露给他人。</p>"
        )
        desc_label.setWordWrap(True)
        desc_label.setOpenExternalLinks(True)
        desc_label.setStyleSheet("font-size: 14px; line-height: 1.8;")
        layout.addWidget(desc_label)

        self.open_key_btn = QPushButton("🔑 打开 API Keys 管理页面")
        self.open_key_btn.setFixedHeight(40)
        self.open_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: white;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        self.open_key_btn.clicked.connect(lambda: webbrowser.open("https://platform.deepseek.com/api_keys"))
        layout.addWidget(self.open_key_btn)

        layout.addStretch()
        self.setLayout(layout)


class InputKeyPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("填写 API 配置")
        self.setSubTitle("第三步：填入您的 API 信息")

        self.api_url = "https://api.deepseek.com/v1"
        self.default_model = "deepseek-chat"

        main_layout = QVBoxLayout()
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(30, 20, 30, 20)

        # API 地址
        url_section = QVBoxLayout()
        url_section.setSpacing(8)
        url_label = QLabel("🌐 API 地址")
        url_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        url_section.addWidget(url_label)
        self.url_edit = QLineEdit()
        self.url_edit.setText(self.api_url)
        self.url_edit.setReadOnly(True)
        self.url_edit.setFixedHeight(40)
        self.url_edit.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #666;
            }
        """)
        url_section.addWidget(self.url_edit)
        main_layout.addLayout(url_section)

        # API Key
        key_section = QVBoxLayout()
        key_section.setSpacing(8)
        key_label = QLabel("🔑 API Key")
        key_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        key_section.addWidget(key_label)
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("请输入您的 API Key，格式如：sk-xxxxxxxxxxxxxxxxxxxxxxxx")
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setFixedHeight(40)
        self.key_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #FFB6C1;
            }
        """)
        key_section.addWidget(self.key_edit)
        main_layout.addLayout(key_section)

        # 模型选择
        model_section = QVBoxLayout()
        model_section.setSpacing(8)
        model_label = QLabel("🤖 模型选择")
        model_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        model_section.addWidget(model_label)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([self.default_model, "deepseek-coder", "deepseek-math"])
        self.model_combo.setCurrentText(self.default_model)
        self.model_combo.setFixedHeight(40)
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox:focus {
                border-color: #FFB6C1;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #FFE4E9;
            }
        """)
        model_section.addWidget(self.model_combo)
        main_layout.addLayout(model_section)

        # 测试按钮
        test_section = QVBoxLayout()
        test_section.setSpacing(10)
        test_btn_layout = QHBoxLayout()
        test_btn_layout.addStretch()
        self.test_btn = QPushButton("🧪 测试连接")
        self.test_btn.setFixedSize(140, 42)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #999;
            }
        """)
        self.test_btn.clicked.connect(self.test_connection)
        test_btn_layout.addWidget(self.test_btn)
        test_btn_layout.addStretch()
        test_section.addLayout(test_btn_layout)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 12px 15px;
                border-radius: 8px;
                font-size: 13px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        test_section.addWidget(self.status_label)
        main_layout.addLayout(test_section)

        main_layout.addStretch()
        self.setLayout(main_layout)

        self.registerField("api_key_required", self.key_edit)

    def test_connection(self):
        api_key = self.key_edit.text().strip()
        if not api_key:
            self.status_label.setText("❌ 请先输入 API Key")
            self.status_label.setStyleSheet("background-color: #FFE0E0; color: #C00; padding: 10px; border-radius: 5px;")
            return

        self.test_btn.setText("测试中...")
        self.test_btn.setEnabled(False)
        self.status_label.setText("⏳ 正在测试连接...")
        self.status_label.setStyleSheet("background-color: #FFF3E0; color: #E65100; padding: 10px; border-radius: 5px;")
        QApplication.processEvents()

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            import requests
            response = requests.get(
                f"{self.api_url}/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                self.status_label.setText("✅ 连接成功！API Key 有效")
                self.status_label.setStyleSheet("background-color: #E8F5E9; color: #2E7D32; padding: 10px; border-radius: 5px;")
            else:
                self.status_label.setText(f"❌ 连接失败：HTTP {response.status_code}")
                self.status_label.setStyleSheet("background-color: #FFE0E0; color: #C00; padding: 10px; border-radius: 5px;")
        except Exception as e:
            self.status_label.setText(f"❌ 连接失败：{str(e)}")
            self.status_label.setStyleSheet("background-color: #FFE0E0; color: #C00; padding: 10px; border-radius: 5px;")

        self.test_btn.setText("🧪 测试连接")
        self.test_btn.setEnabled(True)


class FinishPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("完成")
        self.setSubTitle("第四步：保存配置")

        layout = QVBoxLayout()

        self.config_summary = QTextBrowser()
        self.config_summary.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
            }
        """)
        self.config_summary.setFixedHeight(150)
        layout.addWidget(QLabel("<b>配置摘要：</b>"))
        layout.addWidget(self.config_summary)

        self.save_btn = QPushButton("💾 保存配置到 config.json")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.save_btn.clicked.connect(self.save_config)
        layout.addWidget(self.save_btn)

        self.save_status = QLabel("")
        self.save_status.setWordWrap(True)
        layout.addWidget(self.save_status)

        layout.addStretch()
        self.setLayout(layout)

    def set_config_summary(self, api_url, api_key, model):
        # 确保参数不为None
        api_url = api_url or ""
        api_key = api_key or ""
        model = model or ""
        
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "****"
        summary = f"""
        <p><b>API 地址：</b>{api_url}</p>
        <p><b>API Key：</b>{masked_key}</p>
        <p><b>模型：</b>{model}</p>
        """
        self.config_summary.setHtml(summary)

    def save_config(self):
        wizard = self.wizard()
        config_manager = ConfigManager()
        config = config_manager.load_config()
        config["api_url"] = wizard.api_url
        config["api_key"] = wizard.api_key
        config["model"] = wizard.model
        config_manager.save_config(config)
        self.save_status.setText("✅ 配置已保存到 config.json！")
        self.save_status.setStyleSheet("color: #2E7D32; font-weight: bold;")


class ApiWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 配置向导")
        self.setFixedSize(650, 650)
        self.setStyleSheet("""
            QWizard {
                background-color: #FAFAFA;
            }
            QWizardPage {
                background-color: white;
                padding: 25px;
            }
        """)

        self.api_url = "https://api.deepseek.com/v1"
        self.api_key = ""
        self.model = "deepseek-chat"

        self.intro_page = IntroPage()
        self.register_page = RegisterPage()
        self.create_key_page = CreateKeyPage()
        self.input_key_page = InputKeyPage()
        self.finish_page = FinishPage()

        self.setPage(0, self.intro_page)
        self.setPage(1, self.register_page)
        self.setPage(2, self.create_key_page)
        self.setPage(3, self.input_key_page)
        self.setPage(4, self.finish_page)

        self.setStartId(0)

        self.currentIdChanged.connect(self.on_page_changed)

    def on_page_changed(self, page_id):
        if page_id == 4:
            self.finish_page.set_config_summary(
                self.input_key_page.url_edit.text(),
                self.input_key_page.key_edit.text(),
                self.input_key_page.model_combo.currentText()
            )
            self.api_key = self.input_key_page.key_edit.text()
            self.model = self.input_key_page.model_combo.currentText()


PRESET_THEMES = {
    "萌兔粉": {
        "bg_color": "#F5F5F5",
        "button_color": "#FF8FAB",
        "card_bg_color": "#FFFFFF",
        "text_color": "#2D2D2D",
        "accent_color": "#FFB6C1",
        "hover_color": "#FF6B8A",
        "border_color": "#E8E8E8"
    },
    "简约灰": {
        "bg_color": "#2D2D2D",
        "button_color": "#4A90D9",
        "card_bg_color": "#3D3D3D",
        "text_color": "#F0F0F0",
        "accent_color": "#5CACE2",
        "hover_color": "#357ABD",
        "border_color": "#555555"
    },
    "深海蓝": {
        "bg_color": "#1A2A4A",
        "button_color": "#2E8B8B",
        "card_bg_color": "#243B5A",
        "text_color": "#F0F4F8",
        "accent_color": "#20B9B9",
        "hover_color": "#3CB371",
        "border_color": "#3D5A80"
    }
}


class TagManagerDialog(QDialog):
    """标签管理对话框"""
    
    def __init__(self, tag_manager, task_manager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.task_manager = task_manager
        self.setWindowTitle("🏷️ 标签管理")
        self.setFixedSize(600, 500)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("🏷️ 标签管理")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)
        
        # 预设标签区域
        preset_group = QGroupBox("预设标签")
        preset_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        # 使用 QWidget 容器来放置标签
        preset_container = QWidget()
        preset_container_layout = QVBoxLayout(preset_container)
        preset_container_layout.setContentsMargins(10, 15, 10, 10)
        preset_container_layout.setSpacing(8)
        
        # 当前行的布局
        current_row_layout = QHBoxLayout()
        current_row_layout.setSpacing(8)
        row_width = 0
        max_width = 550  # 每行最大宽度
        
        preset_tags = self.tag_manager.get_preset_tags()
        for tag, color in preset_tags.items():
            tag_label = QLabel(f"  #{tag}  ")
            tag_label.setStyleSheet(f"""
                background-color: {self._lighten_color(color, 0.85)};
                color: {color};
                border-radius: 12px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
            """)
            tag_label.setFixedHeight(26)
            tag_label.adjustSize()
            
            # 检查是否需要换行
            tag_width = tag_label.width()
            if row_width + tag_width > max_width and row_width > 0:
                current_row_layout.addStretch()
                preset_container_layout.addLayout(current_row_layout)
                current_row_layout = QHBoxLayout()
                current_row_layout.setSpacing(8)
                row_width = 0
            
            current_row_layout.addWidget(tag_label)
            row_width += tag_width + 8
        
        # 添加最后一行
        current_row_layout.addStretch()
        preset_container_layout.addLayout(current_row_layout)
        
        preset_group_layout = QVBoxLayout(preset_group)
        preset_group_layout.setContentsMargins(0, 0, 0, 0)
        preset_group_layout.addWidget(preset_container)
        
        layout.addWidget(preset_group)
        
        # 自定义标签区域
        custom_group = QGroupBox("自定义标签")
        custom_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        custom_layout = QVBoxLayout(custom_group)
        
        # 标签列表
        self.custom_tag_list = QListWidget()
        self.custom_tag_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                background-color: #FAFAFA;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
        """)
        self.refresh_custom_tags()
        custom_layout.addWidget(self.custom_tag_list)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加标签")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self.add_custom_tag)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ 编辑标签")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        edit_btn.clicked.connect(self.edit_custom_tag)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ 删除标签")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_btn.clicked.connect(self.delete_custom_tag)
        btn_layout.addWidget(delete_btn)
        
        custom_layout.addLayout(btn_layout)
        layout.addWidget(custom_group)
        
        # 标签统计
        stats_group = QGroupBox("标签统计")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        stats_layout = QVBoxLayout(stats_group)
        
        stats_text = QTextBrowser()
        stats_text.setMaximumHeight(100)
        stats_text.setStyleSheet("border: 1px solid #E0E0E0; border-radius: 5px; background-color: #FAFAFA;")
        self.update_stats(stats_text)
        stats_layout.addWidget(stats_text)
        
        layout.addWidget(stats_group)
    
    def create_tag_widget(self, tag, color, editable=True):
        """创建标签显示组件"""
        widget = QWidget()
        widget.setFixedHeight(28)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # 颜色指示器
        color_indicator = QLabel()
        color_indicator.setFixedSize(14, 14)
        color_indicator.setStyleSheet(f"""
            background-color: {color};
            border-radius: 7px;
        """)
        layout.addWidget(color_indicator)
        
        # 标签名称
        tag_label = QLabel(f"#{tag}")
        tag_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        layout.addWidget(tag_label)
        layout.addStretch()  # 添加弹性空间防止拉伸
        
        return widget
    
    def refresh_custom_tags(self):
        """刷新自定义标签列表"""
        self.custom_tag_list.clear()
        custom_tags = self.tag_manager.get_custom_tags()
        
        for tag, color in custom_tags.items():
            item = QListWidgetItem()
            widget = self.create_tag_widget(tag, color)
            item.setSizeHint(widget.sizeHint())
            self.custom_tag_list.addItem(item)
            self.custom_tag_list.setItemWidget(item, widget)
    
    def add_custom_tag(self):
        """添加自定义标签"""
        dialog = AddTagDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            tag_name, color = dialog.get_result()
            if tag_name:
                self.tag_manager.add_custom_tag(tag_name, color)
                self.refresh_custom_tags()
                QMessageBox.information(self, "成功", f"标签「{tag_name}」已添加！")
    
    def edit_custom_tag(self):
        """编辑自定义标签"""
        current_item = self.custom_tag_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要编辑的标签！")
            return
        
        # 获取当前标签名称（从列表中获取）
        row = self.custom_tag_list.row(current_item)
        custom_tags = list(self.tag_manager.get_custom_tags().keys())
        if row < len(custom_tags):
            old_tag = custom_tags[row]
            old_color = self.tag_manager.get_tag_color(old_tag)
            
            dialog = AddTagDialog(self, old_tag, old_color)
            if dialog.exec_() == QDialog.Accepted:
                new_tag, new_color = dialog.get_result()
                if new_tag:
                    # 删除旧标签
                    self.tag_manager.remove_custom_tag(old_tag)
                    # 添加新标签
                    self.tag_manager.add_custom_tag(new_tag, new_color)
                    self.refresh_custom_tags()
                    QMessageBox.information(self, "成功", f"标签已更新！")
    
    def delete_custom_tag(self):
        """删除自定义标签"""
        current_item = self.custom_tag_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要删除的标签！")
            return
        
        # 获取当前标签名称
        row = self.custom_tag_list.row(current_item)
        custom_tags = list(self.tag_manager.get_custom_tags().keys())
        if row < len(custom_tags):
            tag_name = custom_tags[row]
            
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除标签「{tag_name}」吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.tag_manager.remove_custom_tag(tag_name)
                self.refresh_custom_tags()
                QMessageBox.information(self, "成功", f"标签「{tag_name}」已删除！")
    
    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """将颜色变浅（用于背景色）"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#F5F5F5"
    
    def update_stats(self, stats_text):
        """更新标签统计"""
        stats = self.tag_manager.get_tag_statistics(self.task_manager)
        
        if not stats:
            stats_text.setHtml("<p style='color: #999; text-align: center;'>暂无标签统计数据</p>")
            return
        
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background-color: #F5F5F5;'><th style='padding: 8px; text-align: left;'>标签</th><th style='padding: 8px; text-align: center;'>任务数量</th></tr>"
        
        for tag, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            color = self.tag_manager.get_tag_color(tag)
            html += f"<tr><td style='padding: 8px;'><span style='color: {color}; font-weight: bold;'>#{tag}</span></td><td style='padding: 8px; text-align: center;'>{count}</td></tr>"
        
        html += "</table>"
        stats_text.setHtml(html)


class AddTagDialog(QDialog):
    """添加/编辑标签对话框"""
    
    def __init__(self, parent=None, tag_name="", color="#757575"):
        super().__init__(parent)
        self.setWindowTitle("添加标签" if not tag_name else "编辑标签")
        self.setFixedSize(350, 200)
        self.setStyleSheet("background-color: #FFFFFF;")
        
        self.tag_name = tag_name
        self.color = color
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标签名称
        name_label = QLabel("标签名称：")
        name_label.setStyleSheet("font-size: 13px; color: #333; font-weight: bold;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit(self.tag_name)
        self.name_input.setPlaceholderText("输入标签名称...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #FFB6C1;
            }
        """)
        layout.addWidget(self.name_input)
        
        # 标签颜色
        color_label = QLabel("标签颜色：")
        color_label.setStyleSheet("font-size: 13px; color: #333; font-weight: bold;")
        layout.addWidget(color_label)
        
        self.color_btn = QPushButton()
        self.color_btn.setFixedHeight(40)
        self.update_color_btn()
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def update_color_btn(self):
        """更新颜色按钮样式"""
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color};
                border: 2px solid #E0E0E0;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                border: 2px solid #999;
            }}
        """)
    
    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(self.color), self, "选择标签颜色")
        if color.isValid():
            self.color = color.name()
            self.update_color_btn()
    
    def get_result(self):
        """获取结果"""
        return self.name_input.text().strip(), self.color


class MemoryManagementDialog(QDialog):
    """记忆管理对话框"""
    
    def __init__(self, memory_manager, parent=None):
        super().__init__(parent)
        self.memory_manager = memory_manager
        self.setWindowTitle("🧠 记忆管理")
        self.resize(900, 700)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索记忆...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #E0E0E0;
                border-radius: 20px;
                font-size: 13px;
                background-color: #FAFAFA;
            }
            QLineEdit:focus {
                border-color: #FFB6C1;
                background-color: white;
            }
        """)
        self.search_input.textChanged.connect(self.filter_memories)
        toolbar_layout.addWidget(self.search_input, stretch=1)
        
        # 类型筛选
        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部记忆", "短期记忆", "长期记忆"])
        self.type_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 15px;
                border: 2px solid #E0E0E0;
                border-radius: 15px;
                background-color: #FAFAFA;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #FFB6C1;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.type_combo.currentTextChanged.connect(self.filter_memories)
        toolbar_layout.addWidget(self.type_combo)
        
        # 全选按钮
        select_all_btn = QPushButton("☑️ 全选")
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        select_all_btn.clicked.connect(self.select_all)
        toolbar_layout.addWidget(select_all_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_list)
        toolbar_layout.addWidget(refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 批量操作工具栏
        batch_toolbar = QHBoxLayout()
        
        # 批量删除按钮
        batch_delete_btn = QPushButton("🗑️ 批量删除")
        batch_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        batch_delete_btn.clicked.connect(self.show_batch_delete_menu)
        batch_toolbar.addWidget(batch_delete_btn)
        
        batch_toolbar.addStretch()
        layout.addLayout(batch_toolbar)
        
        # 统计信息
        stats = self.memory_manager.get_memory_stats()
        stats_label = QLabel(
            f"📊 总计: {stats['total_memories']} 条 | "
            f"短期: {stats['short_term_count']} 条 | "
            f"长期: {stats['long_term_count']} 条"
        )
        stats_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #F5F5F5;
                border-radius: 8px;
                font-size: 12px;
                color: #666;
            }
        """)
        layout.addWidget(stats_label)
        
        # 记忆列表
        self.memory_list = QListWidget()
        self.memory_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FAFAFA;
                padding: 5px;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 10px;
                margin: 3px;
            }
            QListWidget::item:selected {
                background-color: #FFF0F3;
                border-color: #FFB6C1;
            }
            QListWidget::item:hover {
                background-color: #F5F5F5;
            }
        """)
        self.memory_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.memory_list)
        
        # 底部操作按钮
        buttons_layout = QHBoxLayout()
        
        # 删除选中
        delete_btn = QPushButton("🗑️ 删除选中")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 25px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected)
        buttons_layout.addWidget(delete_btn)
        
        # 清空短期记忆
        clear_short_btn = QPushButton("清空短期记忆")
        clear_short_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 25px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        clear_short_btn.clicked.connect(self.clear_short_term)
        buttons_layout.addWidget(clear_short_btn)
        
        # 导出记忆
        export_btn = QPushButton("📤 导出记忆")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 25px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        export_btn.clicked.connect(self.export_memories)
        buttons_layout.addWidget(export_btn)
        
        # 导入记忆
        import_btn = QPushButton("📥 导入记忆")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 25px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        import_btn.clicked.connect(self.import_memories)
        buttons_layout.addWidget(import_btn)
        
        buttons_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 30px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # 加载记忆列表
        self.load_memories()
    
    def load_memories(self):
        """加载记忆列表"""
        self.memory_list.clear()
        
        # 获取所有记忆
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        
        # 按创建时间排序（最新的在前）
        all_memories.sort(key=lambda m: m.created_at, reverse=True)
        
        for memory in all_memories:
            item = QListWidgetItem()
            
            # 格式化显示
            type_icon = "🟠" if memory.memory_type == "short_term" else "🟢"
            time_str = memory.created_at.strftime("%Y-%m-%d %H:%M")
            importance_stars = "⭐" * int(memory.importance * 5)
            
            display_text = f"{type_icon} [{time_str}] {memory.content[:100]}{'...' if len(memory.content) > 100 else ''}"
            
            item.setText(display_text)
            item.setData(Qt.UserRole, memory.id)  # 存储记忆ID
            
            # 设置工具提示（完整内容）
            tooltip = (
                f"类型: {'短期记忆' if memory.memory_type == 'short_term' else '长期记忆'}\n"
                f"重要性: {importance_stars} ({memory.importance:.2f})\n"
                f"创建时间: {time_str}\n"
                f"访问次数: {memory.access_count}\n"
                f"标签: {', '.join(memory.tags) if memory.tags else '无'}\n\n"
                f"完整内容:\n{memory.content}"
            )
            item.setToolTip(tooltip)
            
            self.memory_list.addItem(item)
    
    def filter_memories(self):
        """筛选记忆"""
        search_text = self.search_input.text().lower()
        type_filter = self.type_combo.currentText()
        
        for i in range(self.memory_list.count()):
            item = self.memory_list.item(i)
            memory_id = item.data(Qt.UserRole)
            
            # 查找对应的记忆
            all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
            memory = next((m for m in all_memories if m.id == memory_id), None)
            
            if memory:
                # 搜索过滤
                matches_search = search_text in memory.content.lower() if search_text else True
                
                # 类型过滤
                matches_type = True
                if type_filter == "短期记忆":
                    matches_type = memory.memory_type == "short_term"
                elif type_filter == "长期记忆":
                    matches_type = memory.memory_type == "long_term"
                
                item.setHidden(not (matches_search and matches_type))
    
    def delete_selected(self):
        """删除选中的记忆"""
        selected_items = self.memory_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要删除的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_items)} 条记忆吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            for item in selected_items:
                memory_id = item.data(Qt.UserRole)
                
                # 从短期记忆中删除
                self.memory_manager.short_term_memories = [
                    m for m in self.memory_manager.short_term_memories if m.id != memory_id
                ]
                
                # 从长期记忆中删除
                self.memory_manager.long_term_memories = [
                    m for m in self.memory_manager.long_term_memories if m.id != memory_id
                ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(selected_items)} 条记忆！")
    
    def clear_short_term(self):
        """清空短期记忆"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有短期记忆吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.memory_manager.clear_memories("short_term")
            self.refresh_list()
            QMessageBox.information(self, "成功", "已清空所有短期记忆！")
    
    def select_all(self):
        """全选可见的记忆"""
        visible_count = 0
        for i in range(self.memory_list.count()):
            item = self.memory_list.item(i)
            if not item.isHidden():
                item.setSelected(True)
                visible_count += 1
        
        QMessageBox.information(self, "提示", f"已选中 {visible_count} 条可见记忆！")
    
    def show_batch_delete_menu(self):
        """显示批量删除菜单"""
        from PyQt5.QtWidgets import QMenu
        from datetime import datetime, timedelta
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #FFEBEE;
                color: #D32F2F;
            }
        """)
        
        # 按时间删除
        time_menu = menu.addMenu("📅 按时间删除")
        
        delete_7_days = time_menu.addAction("删除 7 天前的记忆")
        delete_7_days.triggered.connect(lambda: self.delete_by_time(7))
        
        delete_30_days = time_menu.addAction("删除 30 天前的记忆")
        delete_30_days.triggered.connect(lambda: self.delete_by_time(30))
        
        delete_90_days = time_menu.addAction("删除 90 天前的记忆")
        delete_90_days.triggered.connect(lambda: self.delete_by_time(90))
        
        delete_custom = time_menu.addAction("自定义天数...")
        delete_custom.triggered.connect(self.delete_by_custom_time)
        
        # 按重要性删除
        importance_menu = menu.addMenu("⭐ 按重要性删除")
        
        delete_low = importance_menu.addAction("删除低重要性记忆 (< 0.3)")
        delete_low.triggered.connect(lambda: self.delete_by_importance(0.3, "below"))
        
        delete_medium = importance_menu.addAction("删除中等重要性记忆 (< 0.6)")
        delete_medium.triggered.connect(lambda: self.delete_by_importance(0.6, "below"))
        
        keep_high = importance_menu.addAction("只保留高重要性记忆 (>= 0.7)")
        keep_high.triggered.connect(lambda: self.delete_by_importance(0.7, "keep_above"))
        
        menu.addSeparator()
        
        # 删除筛选结果
        delete_filtered = menu.addAction("🔍 删除当前筛选结果")
        delete_filtered.triggered.connect(self.delete_filtered)
        
        # 删除未访问的记忆
        delete_unused = menu.addAction("📊 删除从未访问的记忆")
        delete_unused.triggered.connect(self.delete_never_accessed)
        
        menu.addSeparator()
        
        # 清空所有
        clear_all = menu.addAction("⚠️ 清空所有记忆")
        clear_all.triggered.connect(self.clear_all_memories)
        
        # 显示菜单
        menu.exec_(self.cursor().pos())
    
    def delete_by_time(self, days: int):
        """删除指定天数前的记忆"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 统计要删除的数量
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        to_delete = [m for m in all_memories if m.created_at < cutoff_date]
        
        if not to_delete:
            QMessageBox.information(self, "提示", f"没有 {days} 天前的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {days} 天前的所有记忆吗？\n\n"
            f"将删除 {len(to_delete)} 条记忆\n"
            f"（创建时间早于 {cutoff_date.strftime('%Y-%m-%d %H:%M')}）\n\n"
            f"此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            self.memory_manager.short_term_memories = [
                m for m in self.memory_manager.short_term_memories if m.created_at >= cutoff_date
            ]
            self.memory_manager.long_term_memories = [
                m for m in self.memory_manager.long_term_memories if m.created_at >= cutoff_date
            ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(to_delete)} 条记忆！")
    
    def delete_by_custom_time(self):
        """自定义时间删除"""
        from PyQt5.QtWidgets import QInputDialog
        from datetime import datetime, timedelta
        
        days, ok = QInputDialog.getInt(
            self,
            "自定义天数",
            "请输入要删除多少天前的记忆：",
            value=30,
            min=1,
            max=365
        )
        
        if ok:
            self.delete_by_time(days)
    
    def delete_by_importance(self, threshold: float, mode: str):
        """按重要性删除记忆
        
        Args:
            threshold: 重要性阈值
            mode: "below" 删除低于阈值, "keep_above" 保留高于阈值
        """
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        
        if mode == "below":
            to_delete = [m for m in all_memories if m.importance < threshold]
            message = f"确定要删除重要性低于 {threshold:.1f} 的所有记忆吗？\n\n将删除 {len(to_delete)} 条记忆\n此操作不可恢复！"
        else:  # keep_above
            to_delete = [m for m in all_memories if m.importance < threshold]
            message = f"确定要只保留重要性 >= {threshold:.1f} 的记忆吗？\n\n将删除 {len(to_delete)} 条记忆\n此操作不可恢复！"
        
        if not to_delete:
            QMessageBox.information(self, "提示", "没有符合条件的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            self.memory_manager.short_term_memories = [
                m for m in self.memory_manager.short_term_memories if m.importance >= threshold
            ]
            self.memory_manager.long_term_memories = [
                m for m in self.memory_manager.long_term_memories if m.importance >= threshold
            ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(to_delete)} 条记忆！")
    
    def delete_filtered(self):
        """删除当前筛选结果"""
        # 获取当前可见的记忆项
        visible_items = []
        for i in range(self.memory_list.count()):
            item = self.memory_list.item(i)
            if not item.isHidden():
                visible_items.append(item)
        
        if not visible_items:
            QMessageBox.warning(self, "提示", "当前没有可见的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除当前筛选结果吗？\n\n"
            f"将删除 {len(visible_items)} 条记忆\n"
            f"此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            for item in visible_items:
                memory_id = item.data(Qt.UserRole)
                
                self.memory_manager.short_term_memories = [
                    m for m in self.memory_manager.short_term_memories if m.id != memory_id
                ]
                self.memory_manager.long_term_memories = [
                    m for m in self.memory_manager.long_term_memories if m.id != memory_id
                ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(visible_items)} 条记忆！")
    
    def delete_never_accessed(self):
        """删除从未访问的记忆"""
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        to_delete = [m for m in all_memories if m.access_count == 0]
        
        if not to_delete:
            QMessageBox.information(self, "提示", "没有从未访问的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除从未访问的记忆吗？\n\n"
            f"将删除 {len(to_delete)} 条记忆\n"
            f"此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            self.memory_manager.short_term_memories = [
                m for m in self.memory_manager.short_term_memories if m.access_count > 0
            ]
            self.memory_manager.long_term_memories = [
                m for m in self.memory_manager.long_term_memories if m.access_count > 0
            ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(to_delete)} 条记忆！")
    
    def clear_all_memories(self):
        """清空所有记忆"""
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        
        if not all_memories:
            QMessageBox.information(self, "提示", "当前没有任何记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "⚠️ 危险操作",
            f"确定要清空所有记忆吗？\n\n"
            f"将删除全部 {len(all_memories)} 条记忆\n"
            f"此操作不可恢复！\n\n"
            f"建议先导出备份！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 二次确认
            confirm = QMessageBox.warning(
                self,
                "最后确认",
                "真的要清空所有记忆吗？\n此操作无法撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                self.memory_manager.clear_memories()
                self.refresh_list()
                QMessageBox.information(self, "成功", "已清空所有记忆！")
    
    
    def export_memories(self):
        """导出记忆"""
        from PyQt5.QtWidgets import QFileDialog
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出记忆",
            f"memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                self.memory_manager.export_memories(filename)
                QMessageBox.information(self, "成功", f"记忆已导出到：\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败：\n{str(e)}")
    
    def import_memories(self):
        """导入记忆"""
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "导入记忆",
            "",
            "JSON文件 (*.json)"
        )
        
        if filename:
            reply = QMessageBox.question(
                self,
                "导入方式",
                "选择导入方式：\n\n"
                "Yes - 合并现有记忆\n"
                "No - 替换现有记忆",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Cancel:
                try:
                    merge = (reply == QMessageBox.Yes)
                    self.memory_manager.import_memories(filename, merge=merge)
                    self.refresh_list()
                    QMessageBox.information(self, "成功", "记忆导入成功！")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导入失败：\n{str(e)}")
    
    def refresh_list(self):
        """刷新列表"""
        self.load_memories()
        self.filter_memories()


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 MT任务助手")
        self.setFixedSize(420, 520)
        self.setStyleSheet("background-color: #FFFFFF;")
        # 启用双缓冲减少闪烁
        self.setAttribute(Qt.WA_PaintOnScreen, False)
        self.setAutoFillBackground(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(30, 25, 30, 25)

        img_path = resource_path(os.path.join("images", "mt520.png"))

        avatar_label = QLabel()
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setFixedSize(100, 100)

        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            circular = QPixmap(100, 100)
            circular.fill(Qt.transparent)
            from PyQt5.QtGui import QPainter, QBrush, QPen
            painter = QPainter(circular)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            brush = QBrush(scaled_pixmap)
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 100, 100)
            painter.end()
            avatar_label.setPixmap(circular)
        else:
            avatar_label.setText("🐰")
            avatar_label.setStyleSheet("font-size: 70px; color: #FFB6C1;")

        layout.addWidget(avatar_label, alignment=Qt.AlignCenter)
        
        avatar_note = QLabel("仅为作者使用头像")
        avatar_note.setAlignment(Qt.AlignCenter)
        avatar_note.setStyleSheet("font-size: 9px; color: #999; font-style: italic;")
        layout.addWidget(avatar_note)
        
        layout.addSpacing(8)

        title_label = QLabel("📋 MT任务助手")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        version_label = QLabel("版本 1.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 12px; color: #999;")
        layout.addWidget(version_label)

        layout.addSpacing(12)

        desc_label = QLabel("一个基于 AI 的任务管理助手，帮助你拆分目标、管理时间。")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 13px; color: #666; line-height: 1.6; padding: 0 20px;")
        layout.addWidget(desc_label)

        layout.addSpacing(18)

        features_label = QLabel("主要功能：")
        features_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333; padding-left: 5px;")
        layout.addWidget(features_label)

        feature_layout = QVBoxLayout()
        feature_layout.setSpacing(8)
        feature_layout.setContentsMargins(10, 5, 10, 5)

        features = [
            "🤖 AI 智能任务拆分",
            "🍅 番茄钟专注计时",
            "📊 数据统计分析",
            "🎨 个性化主题定制",
            "🧭 API 配置向导"
        ]
        for text in features:
            f_label = QLabel(text)
            f_label.setStyleSheet("font-size: 12px; color: #666; padding-left: 5px;")
            feature_layout.addWidget(f_label)

        layout.addLayout(feature_layout)

        layout.addStretch()

        layout.addSpacing(10)

        tech_label = QLabel("使用 PyQt5 开发 | DeepSeek API 驱动")
        tech_label.setAlignment(Qt.AlignCenter)
        tech_label.setStyleSheet("font-size: 10px; color: #BBB;")
        layout.addWidget(tech_label)

        author_label = QLabel("作者：zyhm，灵感来源萌兔agent")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("font-size: 10px; color: #BBB;")
        layout.addWidget(author_label)

        layout.addSpacing(12)

        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(120, 38)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF8FAB;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)


class ThemeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.setWindowTitle("个性化主题")
        self.setFixedSize(560, 560)
        self.setStyleSheet("background-color: #FAFAFA;")
        self.load_current_theme()
        self.init_ui()

    def load_current_theme(self):
        config = self.config_manager.load_config()
        theme_config = config.get("theme", {})
        self.current_preset = theme_config.get("preset", "萌兔粉")
        self.custom_colors = theme_config.get("custom", {
            "bg_color": "#F5F5F5",
            "button_color": "#FF8FAB",
            "card_bg_color": "#FFFFFF",
            "text_color": "#2D2D2D",
            "border_color": "#E0E0E0"
        })
        self.use_custom = self.current_preset not in PRESET_THEMES

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel("🎨 主题设置")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        preset_label = QLabel("预设方案")
        preset_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #555;")
        layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(PRESET_THEMES.keys()))
        self.preset_combo.addItem("自定义")
        if self.use_custom:
            self.preset_combo.setCurrentText("自定义")
        else:
            self.preset_combo.setCurrentText(self.current_preset)
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        self.preset_combo.setFixedHeight(38)
        self.preset_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #333;
            }
            QComboBox:hover {
                border-color: #FF8FAB;
            }
            QComboBox:focus {
                border-color: #FF8FAB;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #888;
            }
        """)
        layout.addWidget(self.preset_combo)

        preview_label = QLabel("主题预览")
        preview_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #555; margin-top: 5px;")
        layout.addWidget(preview_label)

        preview_container = QFrame()
        preview_container.setFixedHeight(100)
        preview_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
            }
        """)
        preview_layout = QHBoxLayout(preview_container)
        preview_layout.setContentsMargins(15, 10, 15, 10)
        preview_layout.setSpacing(12)

        self.preview_bg = QFrame()
        self.preview_bg.setFixedSize(100, 70)
        preview_layout.addWidget(self.preview_bg)

        self.preview_card = QFrame()
        self.preview_card.setFixedSize(100, 70)
        preview_layout.addWidget(self.preview_card)

        btn_container = QWidget()
        btn_container_layout = QVBoxLayout(btn_container)
        btn_container_layout.setContentsMargins(0, 5, 0, 5)
        self.preview_btn = QPushButton("按钮")
        self.preview_btn.setFixedSize(70, 28)
        btn_container_layout.addWidget(self.preview_btn)
        preview_layout.addWidget(btn_container)

        layout.addWidget(preview_container)

        custom_label = QLabel("自定义颜色（选择「自定义」后生效）")
        custom_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #555; margin-top: 5px;")
        layout.addWidget(custom_label)

        custom_container = QFrame()
        custom_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
            }
        """)
        custom_layout = QGridLayout(custom_container)
        custom_layout.setContentsMargins(15, 12, 15, 12)
        custom_layout.setHorizontalSpacing(15)
        custom_layout.setVerticalSpacing(12)

        custom_layout.addWidget(QLabel("主背景色"), 0, 0)
        self.bg_color_btn = self.create_color_button("bg_color")
        custom_layout.addWidget(self.bg_color_btn, 0, 1)

        custom_layout.addWidget(QLabel("按钮/强调色"), 0, 2)
        self.button_color_btn = self.create_color_button("button_color")
        custom_layout.addWidget(self.button_color_btn, 0, 3)

        custom_layout.addWidget(QLabel("卡片背景色"), 1, 0)
        self.card_color_btn = self.create_color_button("card_bg_color")
        custom_layout.addWidget(self.card_color_btn, 1, 1)

        custom_layout.addWidget(QLabel("文字颜色"), 1, 2)
        self.text_color_btn = self.create_color_button("text_color")
        custom_layout.addWidget(self.text_color_btn, 1, 3)

        layout.addWidget(custom_container)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(100, 42)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                color: #555;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E8E8E8;
                border-color: #CCC;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("应用主题")
        ok_btn.setFixedSize(100, 42)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
        """)
        ok_btn.clicked.connect(self.save_and_apply)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        self.update_preview()

    def create_color_button(self, color_type):
        color = self.custom_colors.get(color_type, "#FFFFFF")
        btn = QPushButton()
        btn.setFixedSize(130, 44)
        btn.setText(color.upper())
        is_dark = self.is_dark_color(color)
        text_color = "#FFF" if is_dark else "#1A1A1A"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid #B0B0B0;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                color: {text_color};
                padding-left: 12px;
            }}
            QPushButton:hover {{
                border: 3px solid #FF8FAB;
                border-radius: 12px;
            }}
            QPushButton:pressed {{
                background-color: {color};
                border: 2px solid #E0E0E0;
            }}
        """)
        btn.clicked.connect(lambda: self.select_color(color_type))
        return btn

    def on_preset_changed(self):
        self.use_custom = self.preset_combo.currentText() == "自定义"
        self.update_preview()

    def update_preview(self):
        if self.use_custom:
            preset = self.custom_colors.copy()
            preset["button_color"] = self.custom_colors.get("button_color", "#FF8FAB")
        else:
            preset_name = self.preset_combo.currentText()
            preset = PRESET_THEMES.get(preset_name, PRESET_THEMES["萌兔粉"]).copy()

        bg = preset.get("bg_color", "#F5F5F5")
        card = preset.get("card_bg_color", "#FFFFFF")
        btn = preset.get("button_color", "#FF8FAB")
        text = preset.get("text_color", "#333333")

        is_dark_bg = self.is_dark_color(bg)
        is_dark_card = self.is_dark_color(card)

        bg_border = "#555" if is_dark_bg else "#E0E0E0"
        card_border = "#555" if is_dark_card else "#E0E0E0"
        btn_text_color = "#FFF" if self.is_dark_color(btn) else "#333"

        self.preview_bg.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {bg_border};
                border-radius: 8px;
            }}
        """)

        self.preview_card.setStyleSheet(f"""
            QFrame {{
                background-color: {card};
                border: 2px solid {card_border};
                border-radius: 8px;
            }}
        """)

        self.preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn};
                color: {btn_text_color};
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
        """)

    def is_dark_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return False
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5

    def select_color(self, color_type):
        current = self.custom_colors.get(color_type, "#FFFFFF")
        color = QColorDialog.getColor(QColor(current), self, f"选择{self.get_color_name(color_type)}")
        if color.isValid():
            self.custom_colors[color_type] = color.name()
            attr_map = {
                "bg_color": "bg_color_btn",
                "button_color": "button_color_btn",
                "card_bg_color": "card_color_btn",
                "text_color": "text_color_btn"
            }
            btn = getattr(self, attr_map.get(color_type, f"{color_type}_btn"))
            is_dark = self.is_dark_color(color.name())
            text_color = "#FFF" if is_dark else "#1A1A1A"
            btn.setText(color.name().upper())
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    border: 2px solid #B0B0B0;
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 600;
                    color: {text_color};
                    padding-left: 12px;
                }}
                QPushButton:hover {{
                    border: 3px solid #FF8FAB;
                    border-radius: 12px;
                }}
                QPushButton:pressed {{
                    background-color: {color.name()};
                    border: 2px solid #E0E0E0;
                }}
            """)
            if not self.use_custom:
                self.preset_combo.setCurrentText("自定义")
                self.use_custom = True
            self.update_preview()

    def get_color_name(self, color_type):
        names = {
            "bg_color": "主背景色",
            "button_color": "按钮/强调色",
            "card_bg_color": "卡片背景色",
            "text_color": "文字颜色"
        }
        return names.get(color_type, color_type)

    def save_and_apply(self):
        preset_name = "自定义" if self.use_custom else self.preset_combo.currentText()

        theme_config = {
            "preset": preset_name,
            "custom": self.custom_colors.copy()
        }

        config = self.config_manager.load_config()
        config["theme"] = theme_config
        self.config_manager.save_config(config)

        if hasattr(self.parent(), "refresh_style"):
            self.parent().refresh_style()

        self.accept()


class AddTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加任务")
        self.setFixedSize(400, 320)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.parsed_result = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 智能模式切换
        mode_row = QHBoxLayout()
        self.smart_mode_btn = QPushButton("🤖 智能模式")
        self.smart_mode_btn.setCheckable(True)
        self.smart_mode_btn.setFixedHeight(28)
        self.smart_mode_btn.setStyleSheet("""
            QPushButton {
                background: #F0F0F0;
                color: #666;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:checked {
                background: #FF8FAB;
                color: white;
            }
        """)
        self.smart_mode_btn.clicked.connect(self.toggle_smart_mode)
        mode_row.addWidget(self.smart_mode_btn)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # 任务名称
        name_label = QLabel("任务名称")
        name_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #999;")
        layout.addWidget(name_label)

        # 任务名称输入 + 智能解析按钮
        name_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入任务名称，如：明天下午3点开会 #工作 重要")
        self.name_edit.setFixedHeight(36)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #FAFAFA;
                border: 1.5px solid #E8E8E8;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #FF6B9D;
                background: white;
            }
        """)
        name_row.addWidget(self.name_edit)

        self.parse_btn = QPushButton("解析")
        self.parse_btn.setFixedSize(50, 36)
        self.parse_btn.setCursor(Qt.PointingHandCursor)
        self.parse_btn.setStyleSheet("""
            QPushButton {
                background: #E3F2FD;
                color: #1976D2;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #BBDEFB; }
        """)
        self.parse_btn.clicked.connect(self.parse_natural_language)
        name_row.addWidget(self.parse_btn)
        layout.addLayout(name_row)

        # 解析预览
        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet("color: #4CAF50; font-size: 11px; padding: 4px;")
        self.preview_label.setWordWrap(True)
        self.preview_label.hide()
        layout.addWidget(self.preview_label)

        # 预估时间（一行布局）
        time_label = QLabel("预估时间")
        time_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #999;")
        layout.addWidget(time_label)
        spin_row = QHBoxLayout()
        spin_row.setSpacing(6)
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 24)
        self.hours_spin.setValue(0)
        self.hours_spin.setFixedSize(70, 34)
        self.hours_spin.setStyleSheet("""
            QSpinBox {
                background: #FAFAFA;
                border: 1.5px solid #E8E8E8;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 13px;
                color: #333;
            }
            QSpinBox:focus { border-color: #FF6B9D; }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px; border: none; background: transparent;
            }
        """)
        spin_row.addWidget(self.hours_spin)
        spin_row.addWidget(QLabel("小时"))
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(30)
        self.minutes_spin.setFixedSize(70, 34)
        self.minutes_spin.setStyleSheet(self.hours_spin.styleSheet())
        spin_row.addWidget(self.minutes_spin)
        spin_row.addWidget(QLabel("分钟"))
        spin_row.addStretch()
        layout.addLayout(spin_row)

        # 截止时间
        due_label = QLabel("截止时间")
        due_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #999;")
        layout.addWidget(due_label)
        due_row = QHBoxLayout()
        due_row.setSpacing(8)
        self.due_date_edit = QDateTimeEdit()
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.due_date_edit.setFixedHeight(34)
        self.due_date_edit.setStyleSheet("""
            QDateTimeEdit {
                background: #FAFAFA;
                border: 1.5px solid #E8E8E8;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 13px;
                color: #333;
            }
            QDateTimeEdit:focus { border-color: #FF6B9D; }
            QDateTimeEdit::drop-down { width: 24px; border: none; }
            QDateTimeEdit::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #999;
            }
        """)
        due_row.addWidget(self.due_date_edit)
        self.no_due_checkbox = QCheckBox("无截止")
        self.no_due_checkbox.setStyleSheet("""
            QCheckBox { color: #888; font-size: 12px; spacing: 4px; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 2px solid #D0D0D0; background: white;
            }
            QCheckBox::indicator:checked {
                background-color: #FF6B9D; border-color: #FF6B9D;
            }
        """)
        self.no_due_checkbox.stateChanged.connect(self.on_no_due_changed)
        due_row.addWidget(self.no_due_checkbox)
        due_row.addStretch()
        layout.addLayout(due_row)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 36)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F5; color: #666;
                border: none; border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background: #E8E8E8; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(80, 36)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #FF6B9D; color: white;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #EC407A; }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def on_no_due_changed(self, state):
        self.due_date_edit.setEnabled(state == 0)

    def toggle_smart_mode(self, checked):
        """切换智能模式"""
        if checked:
            self.name_edit.setPlaceholderText("输入自然语言，如：明天下午3点开会 #工作 重要")
            self.parse_btn.show()
        else:
            self.name_edit.setPlaceholderText("输入任务名称...")
            self.parse_btn.hide()
            self.preview_label.hide()

    def parse_natural_language(self):
        """解析自然语言输入"""
        text = self.name_edit.text().strip()
        if not text:
            return

        try:
            from nlp_task_parser import parse_natural_task
            result = parse_natural_task(text)
            self.parsed_result = result

            # 填充表单
            self.name_edit.setText(result["task_name"])

            # 预估时间
            hours = result["estimated_minutes"] // 60
            minutes = result["estimated_minutes"] % 60
            self.hours_spin.setValue(hours)
            self.minutes_spin.setValue(minutes)

            # 截止时间
            if result["due_date"]:
                self.no_due_checkbox.setChecked(False)
                qdt = QDateTime.fromString(
                    result["due_date"].strftime("%Y-%m-%d %H:%M"),
                    "yyyy-MM-dd HH:mm"
                )
                self.due_date_edit.setDateTime(qdt)

            # 显示解析预览
            preview_parts = []
            priority_names = {1: "低", 2: "普通", 3: "中高", 4: "高", 5: "紧急"}
            preview_parts.append(f"优先级: {priority_names.get(result['priority'], '普通')}")
            if result["due_date"]:
                preview_parts.append(f"时间: {result['due_date'].strftime('%m-%d %H:%M')}")
            if result["tags"]:
                preview_parts.append(f"标签: {', '.join(result['tags'])}")

            self.preview_label.setText("✓ " + " | ".join(preview_parts))
            self.preview_label.show()

        except Exception as e:
            self.preview_label.setText(f"解析失败: {str(e)}")
            self.preview_label.setStyleSheet("color: #F44336; font-size: 11px; padding: 4px;")
            self.preview_label.show()

    def get_result(self):
        name = self.name_edit.text().strip()
        hours = self.hours_spin.value()
        minutes = self.minutes_spin.value()
        total_minutes = hours * 60 + minutes
        if total_minutes == 0:
            total_minutes = 30
        due_date = None if self.no_due_checkbox.isChecked() else self.due_date_edit.dateTime().toString("yyyy-MM-dd HH:mm")

        # 如果有解析结果，包含优先级和标签
        priority = self.parsed_result.get("priority", 2) if self.parsed_result else 2
        tags = self.parsed_result.get("tags", []) if self.parsed_result else []

        return name, total_minutes, due_date, priority, tags


class ReminderTab(QWidget):
    """提醒管理标签页"""
    def __init__(self, reminder_manager: ReminderManager, main_window=None, parent=None):
        super().__init__(parent)
        self.reminder_manager = reminder_manager
        self.main_window = main_window  # 保存 MainWindow 引用，用于系统托盘通知
        self.init_ui()

        # 连接提醒触发信号
        self.reminder_manager.reminder_triggered.connect(self.on_reminder_triggered)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("⏰ 提醒管理")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        layout.addWidget(title_label)
        
        # 添加提醒按钮
        add_btn = QPushButton("➕ 添加提醒")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
        """)
        add_btn.clicked.connect(self.add_reminder)
        layout.addWidget(add_btn)
        
        # 提醒列表
        self.reminder_list = QWidget()
        self.reminder_layout = QVBoxLayout(self.reminder_list)
        self.reminder_layout.setContentsMargins(0, 0, 0, 0)
        self.reminder_layout.setSpacing(10)
        self.reminder_layout.addStretch()
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidget(self.reminder_list)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F5F5F5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #CCC;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #AAA;
            }
        """)
        layout.addWidget(scroll)
        
        # 刷新提醒列表
        self.refresh_reminders()
    
    def refresh_reminders(self):
        """刷新提醒列表"""
        # 清空现有列表
        while self.reminder_layout.count() > 1:
            item = self.reminder_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取所有提醒
        reminders = self.reminder_manager.get_all_reminders()
        
        if not reminders:
            # 显示空状态
            empty_label = QLabel("暂无提醒\n点击上方按钮添加新提醒")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #999;
                    font-size: 14px;
                    padding: 40px;
                }
            """)
            self.reminder_layout.insertWidget(0, empty_label)
        else:
            # 显示提醒卡片
            for reminder in reminders:
                card = self.create_reminder_card(reminder)
                self.reminder_layout.insertWidget(self.reminder_layout.count() - 1, card)
    
    def create_reminder_card(self, reminder: Reminder) -> QFrame:
        """创建提醒卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid #F0F0F0;
                border-radius: 12px;
                padding: 15px;
            }}
            QFrame:hover {{
                border-color: #FFB6C1;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # 顶部：标题和状态
        top_layout = QHBoxLayout()
        
        title_label = QLabel(reminder.title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        top_layout.addWidget(title_label)
        
        # 状态标签
        status_text = "✓ 已启用" if reminder.enabled else "✗ 已禁用"
        status_color = "#4CAF50" if reminder.enabled else "#999"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {status_color};
                color: white;
                border-radius: 10px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        top_layout.addWidget(status_label)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 提醒时间
        time_str = reminder.remind_time.strftime("%Y-%m-%d %H:%M")
        time_label = QLabel(f"🕐 {time_str}")
        time_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(time_label)
        
        # 重复类型
        if reminder.repeat_type != "none":
            repeat_text = {
                "daily": "每天重复",
                "weekly": "每周重复",
                "monthly": "每月重复"
            }.get(reminder.repeat_type, "重复")
            repeat_label = QLabel(f"🔄 {repeat_text}")
            repeat_label.setStyleSheet("color: #1976D2; font-size: 12px;")
            layout.addWidget(repeat_label)
        
        # 描述
        if reminder.description:
            desc_label = QLabel(f"📝 {reminder.description}")
            desc_label.setStyleSheet("color: #888; font-size: 12px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        # 底部：操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #E3F2FD;
                color: #1976D2;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_reminder(reminder))
        btn_layout.addWidget(edit_btn)
        
        # 切换状态按钮
        toggle_text = "禁用" if reminder.enabled else "启用"
        toggle_color = "#FFF3E0" if reminder.enabled else "#E8F5E9"
        toggle_text_color = "#F57C00" if reminder.enabled else "#4CAF50"
        toggle_btn = QPushButton(toggle_text)
        toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {toggle_color};
                color: {toggle_text_color};
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {toggle_color};
                opacity: 0.8;
            }}
        """)
        toggle_btn.clicked.connect(lambda: self.toggle_reminder(reminder.id))
        btn_layout.addWidget(toggle_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFEBEE;
                color: #F44336;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFCDD2;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_reminder(reminder.id))
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return card
    
    def add_reminder(self):
        """添加提醒"""
        dialog = ReminderDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            title, remind_time, description, repeat_type = dialog.get_reminder_data()
            self.reminder_manager.add_reminder(title, remind_time, description, repeat_type)
            self.refresh_reminders()
    
    def edit_reminder(self, reminder: Reminder):
        """编辑提醒"""
        dialog = ReminderDialog(self, reminder)
        if dialog.exec_() == QDialog.Accepted:
            title, remind_time, description, repeat_type = dialog.get_reminder_data()
            self.reminder_manager.update_reminder(
                reminder.id,
                title=title,
                remind_time=remind_time,
                description=description,
                repeat_type=repeat_type
            )
            self.refresh_reminders()
    
    def toggle_reminder(self, reminder_id: int):
        """切换提醒状态"""
        self.reminder_manager.toggle_reminder(reminder_id)
        self.refresh_reminders()
    
    def delete_reminder(self, reminder_id: int):
        """删除提醒"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个提醒吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.reminder_manager.delete_reminder(reminder_id)
            self.refresh_reminders()
    
    def on_reminder_triggered(self, reminder: Reminder):
        """提醒触发 — 到时间立即弹出系统通知"""
        title = f"⏰ 提醒：{reminder.title}"
        msg = reminder.description if reminder.description else "时间到了！"

        # 方案 1：PowerShell 原生 Toast（exe 环境可靠）
        notification_sent = show_native_toast(title, msg)
        if notification_sent:
            print(f"[提醒] 原生通知已发送: {reminder.title}")

        # 方案 2：winotify（开发环境可用）
        if not notification_sent and WINOTIFY_AVAILABLE:
            try:
                toast = Notification(
                    app_id="MT任务助手",
                    title=title,
                    msg=msg,
                    duration="short"
                )
                toast.set_audio(audio.Default, loop=False)
                toast.show()
                notification_sent = True
                print(f"[提醒] winotify 通知已发送: {reminder.title}")
            except Exception as e:
                print(f"[提醒] winotify 通知失败: {e}")

        # 方案 3：系统托盘通知（通用后备）
        if not notification_sent:
            mw = self.main_window
            if mw and hasattr(mw, 'tray_icon') and mw.tray_icon:
                try:
                    mw.tray_icon.showMessage(
                        title,
                        msg,
                        QSystemTrayIcon.Information,
                        10000
                    )
                    notification_sent = True
                    print(f"[提醒] 托盘通知已发送: {reminder.title}")
                except Exception as e:
                    print(f"[提醒] 托盘通知失败: {e}")

        # 应用内弹窗（窗口可见时才生效）
        try:
            if self.isVisible():
                QMessageBox.information(self, title, f"时间到了！\n\n{msg}")
        except Exception:
            pass


class ReminderDialog(QDialog):
    """提醒编辑对话框"""
    def __init__(self, parent=None, reminder: Reminder = None):
        super().__init__(parent)
        self.reminder = reminder
        self.setWindowTitle("添加提醒" if not reminder else "编辑提醒")
        self.setFixedSize(480, 580)
        self.init_ui()

        if reminder:
            self.load_reminder_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 设置对话框背景色
        self.setStyleSheet("""
            QDialog {
                background-color: #FAFAFA;
            }
        """)

        # 标题输入
        title_label = QLabel("提醒标题：")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title_label)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("例如：开会、吃药、运动...")
        self.title_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #FFB6C1;
            }
        """)
        layout.addWidget(self.title_edit)

        # 快捷时间选择
        quick_time_label = QLabel("快捷选择：")
        quick_time_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(quick_time_label)

        self.quick_time_combo = QComboBox()
        self.quick_time_combo.addItem("🔘 自定义时间", "custom")
        self.quick_time_combo.addItem("⏱️ 10分钟后", "10min")
        self.quick_time_combo.addItem("⏱️ 30分钟后", "30min")
        self.quick_time_combo.addItem("⏱️ 1小时后", "1hour")
        self.quick_time_combo.addItem("⏱️ 2小时后", "2hour")
        self.quick_time_combo.addItem("🌅 今天 18:00", "today18")
        self.quick_time_combo.addItem("🌙 今天 21:00", "today21")
        self.quick_time_combo.addItem("☀️ 明天 08:00", "tomorrow8")
        self.quick_time_combo.addItem("🌅 明天 09:00", "tomorrow9")
        self.quick_time_combo.addItem("🌙 明天 21:00", "tomorrow21")
        self.quick_time_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #FFB6C1;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #FFE4E9;
                selection-color: #333;
            }
        """)
        self.quick_time_combo.currentIndexChanged.connect(self._on_quick_time_changed)
        layout.addWidget(self.quick_time_combo)

        # 提醒时间
        time_label = QLabel("自定义时间：")
        time_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(time_label)

        self.time_edit = QDateTimeEdit()
        self.time_edit.setCalendarPopup(True)
        self.time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        now = QDateTime.currentDateTime()
        self.time_edit.setMinimumDateTime(now)  # 不允许选择过去的时间
        self.time_edit.setDateTime(now.addSecs(3600))  # 默认1小时后
        self.time_edit.setStyleSheet("""
            QDateTimeEdit {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QDateTimeEdit:focus {
                border-color: #FFB6C1;
            }
            QDateTimeEdit::drop-down {
                border: none;
                width: 30px;
            }
            QDateTimeEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                margin-right: 10px;
            }
        """)
        layout.addWidget(self.time_edit)

        # 当手动修改时间时，切换到"自定义时间"
        self.time_edit.dateTimeChanged.connect(self._on_time_manually_changed)
        
        # 重复类型
        repeat_label = QLabel("重复方式：")
        repeat_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(repeat_label)
        
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["不重复", "每天重复", "每周重复", "每月重复"])
        self.repeat_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #FFB6C1;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #FFE4E9;
                selection-color: #333;
            }
        """)
        layout.addWidget(self.repeat_combo)
        
        # 描述
        desc_label = QLabel("备注说明：")
        desc_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(desc_label)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("添加备注信息（可选）...")
        self.desc_edit.setMinimumHeight(80)
        self.desc_edit.setMaximumHeight(120)
        self.desc_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #FFB6C1;
            }
        """)
        layout.addWidget(self.desc_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666;
                border: none;
                border-radius: 20px;
                padding: 12px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_quick_time_changed(self, index):
        """快捷时间选择改变"""
        data = self.quick_time_combo.currentData()
        if data == "custom":
            return  # 自定义时间，不做修改

        now = QDateTime.currentDateTime()

        if data == "10min":
            self.time_edit.setDateTime(now.addSecs(10 * 60))
        elif data == "30min":
            self.time_edit.setDateTime(now.addSecs(30 * 60))
        elif data == "1hour":
            self.time_edit.setDateTime(now.addSecs(60 * 60))
        elif data == "2hour":
            self.time_edit.setDateTime(now.addSecs(2 * 60 * 60))
        elif data == "today18":
            target = QDateTime(now.date(), QTime(18, 0))
            if target < now:
                # 已经过了今天18点，设为明天18点
                target = target.addDays(1)
            self.time_edit.setDateTime(target)
        elif data == "today21":
            target = QDateTime(now.date(), QTime(21, 0))
            if target < now:
                target = target.addDays(1)
            self.time_edit.setDateTime(target)
        elif data == "tomorrow8":
            tomorrow = now.addDays(1)
            self.time_edit.setDateTime(QDateTime(tomorrow.date(), QTime(8, 0)))
        elif data == "tomorrow9":
            tomorrow = now.addDays(1)
            self.time_edit.setDateTime(QDateTime(tomorrow.date(), QTime(9, 0)))
        elif data == "tomorrow21":
            tomorrow = now.addDays(1)
            self.time_edit.setDateTime(QDateTime(tomorrow.date(), QTime(21, 0)))

    def _on_time_manually_changed(self):
        """手动修改时间时，切换到自定义"""
        # 阻止信号循环
        self.quick_time_combo.blockSignals(True)
        self.quick_time_combo.setCurrentIndex(0)  # 切换到"自定义时间"
        self.quick_time_combo.blockSignals(False)

    def load_reminder_data(self):
        """加载提醒数据"""
        if self.reminder:
            self.title_edit.setText(self.reminder.title)
            self.time_edit.setDateTime(QDateTime.fromString(
                self.reminder.remind_time.strftime("%Y-%m-%d %H:%M:%S"),
                "yyyy-MM-dd HH:mm:ss"
            ))
            self.desc_edit.setPlainText(self.reminder.description)
            
            repeat_map = {"none": 0, "daily": 1, "weekly": 2, "monthly": 3}
            self.repeat_combo.setCurrentIndex(repeat_map.get(self.reminder.repeat_type, 0))
    
    def get_reminder_data(self):
        """获取提醒数据"""
        title = self.title_edit.text().strip()
        if not title:
            title = "未命名提醒"
        
        remind_time = self.time_edit.dateTime().toPyDateTime()
        description = self.desc_edit.toPlainText().strip()
        
        repeat_map = {0: "none", 1: "daily", 2: "weekly", 3: "monthly"}
        repeat_type = repeat_map[self.repeat_combo.currentIndex()]
        
        return title, remind_time, description, repeat_type


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 核心管理器（必须立即加载）
        self.config_manager = ConfigManager()
        self.task_manager = TaskManager()
        self.stats_manager = StatsManager()
        self.tag_manager = TagManager()
        self.reminder_manager = ReminderManager(
            data_file=get_data_path("reminders.json")
        )

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        self.scale_factor = self.screen_width / 1920.0 if self.screen_width > 1920 else 1.0

        # 初始化UI和系统托盘
        self.init_system_tray()
        self.init_ui()

        # 设置窗口图标
        icon_path = resource_path(os.path.join("images", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 创建桌面快捷方式
        self.create_desktop_shortcut()

        # 启动时自动清理已完成的任务
        self._auto_clear_completed_tasks()
        
        self.refresh_tasks()
        self.start_reminder_timer()
        
        # 显示欢迎向导（首次使用）- 在主窗口显示后弹出
        if should_show_wizard():
            # 使用 QTimer 延迟显示，让主窗口先显示
            QTimer.singleShot(100, self.show_welcome_wizard)
        
        # 延迟加载非核心组件
        QTimer.singleShot(500, self._delayed_init)

    def _delayed_init(self):
        """延迟加载非核心组件"""
        # 初始化记忆管理器（较重的组件）
        self.memory_manager = MemoryManager()
        self.ethics_analyzer = AIEthicsAnalyzer()
        # 初始化成就系统
        self.achievement_manager = AchievementManager()

    def create_desktop_shortcut(self):
        """创建桌面快捷方式（仅打包后首次运行创建）"""
        if not getattr(sys, 'frozen', False):
            return  # 开发环境不创建

        shortcut_path = os.path.join(
            os.path.expanduser("~"), "Desktop", "MT任务助手.lnk"
        )
        if os.path.exists(shortcut_path):
            return  # 已存在则不重复创建

        try:
            import pythoncom
            from win32com.client import Dispatch
            pythoncom.CoInitialize()
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = sys.executable
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            icon_path = resource_path(os.path.join("images", "icon.ico"))
            if os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            shortcut.Save()
        except ImportError:
            pass  # 无 pywin32 则跳过
        except Exception:
            pass

    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        tray_icon_path = resource_path(os.path.join("images", "mt520.png"))
        if os.path.exists(tray_icon_path):
            self.tray_icon.setIcon(QIcon(tray_icon_path))
        else:
            fallback_pixmap = QPixmap(16, 16)
            fallback_pixmap.fill(QColor("#FFB6C1"))
            self.tray_icon.setIcon(QIcon(fallback_pixmap))
        self.tray_icon.setToolTip("MT任务助手")
        self.tray_icon.show()

    def start_reminder_timer(self):
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_upcoming_tasks)
        self.reminder_timer.start(60000)

    def check_upcoming_tasks(self):
        upcoming = self.task_manager.get_upcoming_tasks(minutes=5)
        for task, minutes_left in upcoming:
            self.tray_icon.showMessage(
                "⏰ 任务提醒",
                f"任务「{task.name}」将在 {int(minutes_left)} 分钟后截止，请尽快完成！",
                QSystemTrayIcon.Information,
                5000
            )
            self.task_manager.mark_task_reminded(task.id)
    
    def show_welcome_wizard(self):
        """显示欢迎向导"""
        wizard = WelcomeWizard(self)
        # 设置窗口在最上层，始终置顶
        wizard.setWindowFlags(wizard.windowFlags() | Qt.WindowStaysOnTopHint)
        wizard.setWindowModality(Qt.ApplicationModal)  # 应用模态，阻止其他窗口交互
        if wizard.exec_() == QWizard.Accepted:
            mark_wizard_shown()

    def show_memory_management(self):
        """显示记忆管理对话框"""
        if not hasattr(self, 'memory_manager'):
            QMessageBox.warning(self, "提示", "记忆管理器尚未初始化，请稍后再试！")
            return
        
        dialog = MemoryManagementDialog(self.memory_manager, self)
        dialog.exec_()
    
    def show_memory_filter(self):
        """显示智能记忆过滤面板"""
        from PyQt5.QtWidgets import QDialog
        from memory_filter_widget import MemoryFilterWidget
        
        # 创建对话框
        self.memory_filter_dialog = QDialog(self)
        self.memory_filter_dialog.setWindowTitle("🧠 智能记忆过滤系统")
        self.memory_filter_dialog.resize(600, 700)
        
        layout = QVBoxLayout(self.memory_filter_dialog)
        
        # 添加过滤组件
        self.memory_filter_widget = MemoryFilterWidget(self.memory_manager, self.memory_filter_dialog)
        layout.addWidget(self.memory_filter_widget)

        # 显示对话框
        self.memory_filter_dialog.exec_()

    def scale_font(self, base_size):
        return int(base_size * self.scale_factor)

    def scale_size(self, base_size):
        return int(base_size * self.scale_factor)

    def get_current_theme(self):
        config = self.config_manager.load_config()
        theme_config = config.get("theme", {})
        preset = theme_config.get("preset", "萌兔粉")
        custom = theme_config.get("custom", {})
        if preset == "萌兔粉":
            return PRESET_THEMES["萌兔粉"].copy()
        elif preset == "简约灰":
            return PRESET_THEMES["简约灰"].copy()
        elif preset == "深海蓝":
            return PRESET_THEMES["深海蓝"].copy()
        else:
            theme = PRESET_THEMES["萌兔粉"].copy()
            theme["bg_color"] = custom.get("bg_color", "#F5F5F5")
            theme["button_color"] = custom.get("button_color", "#FF8FAB")
            theme["card_bg_color"] = custom.get("card_bg_color", "#FFFFFF")
            theme["text_color"] = custom.get("text_color", "#2D2D2D")
            theme["border_color"] = custom.get("border_color", "#E0E0E0")
            theme["hover_color"] = custom.get("button_color", "#FF6B8A")
            return theme

    def refresh_style(self):
        theme = self.get_current_theme()
        bg = theme["bg_color"]
        btn = theme["button_color"]
        card = theme["card_bg_color"]
        text = theme.get("text_color", "#2D2D2D")
        hover = theme.get("hover_color", btn)
        border = theme.get("border_color", "#E0E0E0")

        def is_dark(c):
            c = c.lstrip('#')
            if len(c) != 6:
                return False
            r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5

        def get_contrast_color(hex_color):
            return "#FFFFFF" if is_dark(hex_color) else "#1A1A1A"

        def get_muted_color(hex_color):
            return "#E0E0E0" if not is_dark(hex_color) else "#505050"

        dark_bg = is_dark(bg)
        dark_card = is_dark(card)
        dark_btn = is_dark(btn)

        main_text = get_contrast_color(bg)
        card_text = get_contrast_color(card)
        btn_text = get_contrast_color(btn)
        muted = get_muted_color(bg)

        input_bg = "#FFFFFF"
        input_text = "#1A1A1A"
        input_border = border

        toolbar_bg = card if dark_bg else "#FFFFFF"
        toolbar_text = card_text if dark_bg else "#333333"

        qss = f"""
            QMainWindow {{
                background-color: {bg};
            }}
            QWidget {{
                background-color: {bg};
                color: {main_text};
            }}
            QFrame#task-card {{
                background-color: {card};
                border-radius: 12px;
                border: 1px solid {border};
            }}
            QFrame#task-card:hover {{
                border: 2px solid {btn};
                background-color: {card};
            }}
            QPushButton {{
                background-color: {btn};
                color: {btn_text};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {hover};
            }}
            QLineEdit, QTextEdit {{
                background-color: {input_bg};
                border: 2px solid {input_border};
                border-radius: 8px;
                padding: 8px;
                color: {input_text};
                selection-background-color: {btn};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {btn};
            }}
            QComboBox {{
                background-color: {input_bg};
                border: 2px solid {input_border};
                border-radius: 8px;
                padding: 8px;
                color: {input_text};
                selection-background-color: {btn};
            }}
            QComboBox:hover {{
                border-color: {btn};
            }}
            QComboBox:focus {{
                border: 2px solid {btn};
            }}
            QTabWidget::pane {{
                border: 1px solid {border};
                border-radius: 8px;
                background-color: {card};
            }}
            QTabBar::tab {{
                background-color: {bg};
                color: {main_text};
                padding: 8px 16px;
                border: 1px solid {border};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:hover {{
                background-color: {card};
            }}
            QTabBar::tab:selected {{
                background-color: {card};
                color: {btn};
                border-bottom: 2px solid {btn};
                font-weight: bold;
            }}
            QScrollArea {{
                background-color: {bg};
                border: none;
            }}
            QLabel {{
                color: {main_text};
            }}
            QMenuBar {{
                background-color: {toolbar_bg};
                color: {toolbar_text};
                border-bottom: 1px solid {border};
            }}
            QMenuBar::item:selected {{
                background-color: {btn};
                color: {btn_text};
            }}
            QMenu {{
                background-color: {card};
                color: {card_text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item:selected {{
                background-color: {btn};
                color: {btn_text};
            }}
            QGroupBox {{
                color: {main_text};
                border: 1px solid {border};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                color: {main_text};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QSpinBox {{
                background-color: {input_bg};
                border: 2px solid {input_border};
                border-radius: 8px;
                padding: 6px;
                color: {input_text};
            }}
            QSpinBox:focus {{
                border: 2px solid {btn};
            }}
            QListWidget {{
                background-color: {bg};
                border: none;
                color: {main_text};
            }}
            QListWidget::item {{
                background-color: {card};
                border-radius: 8px;
                padding: 8px;
                margin-bottom: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {btn};
                color: {btn_text};
            }}
            QTextBrowser {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 8px;
                color: {card_text};
            }}
            QCheckBox {{
                color: {main_text};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {border};
                background-color: {input_bg};
            }}
            QCheckBox::indicator:checked {{
                background-color: {btn};
                border-color: {btn};
            }}
            QCheckBox::indicator:hover {{
                border-color: {btn};
            }}
            QDialog {{
                background-color: {bg};
            }}
            #toolbar {{
                background-color: {toolbar_bg};
                border-bottom: 1px solid {border};
            }}
            #toolbar QLabel {{
                color: {toolbar_text};
            }}
        """
        self.setStyleSheet(qss)

        if hasattr(self, 'toolbar_widget'):
            self.toolbar_widget.setStyleSheet(f"background-color: {toolbar_bg}; border-bottom: 1px solid {border};")
        if hasattr(self, 'toolbar_title'):
            self.toolbar_title.setStyleSheet(f"color: {toolbar_text};")
        if hasattr(self, 'left_title'):
            self.left_title.setStyleSheet(f"color: {main_text};")

        try:
            import glass_style
            glass_style.THEME_COLOR = btn
            glass_style.HOVER_COLOR = hover
            glass_style.GLOBAL_BG_COLOR = bg
            glass_style.CARD_BG_COLOR = card
        except:
            pass

    def init_ui(self):
        self.setWindowTitle("MT任务助手")

        if self.screen_width >= 2560:
            self.resize(1400, 900)
        elif self.screen_width >= 1920:
            self.resize(1200, 800)
        else:
            self.resize(1000, 700)

        self.refresh_style()
        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("toolbar")
        self.toolbar_widget = toolbar_widget
        toolbar_widget.setStyleSheet("background-color: white; border-bottom: 1px solid #F0F0F0;")
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(self.scale_size(15), self.scale_size(5), self.scale_size(15), self.scale_size(5))

        title_label = QLabel("📝 MT任务助手")
        title_label.setFont(QFont("Microsoft YaHei", self.scale_font(14), QFont.Bold))
        self.toolbar_title = title_label
        title_label.setStyleSheet("color: #333333; font-size: 15px;")
        toolbar_layout.addWidget(title_label)

        toolbar_layout.addStretch()

        main_layout.addWidget(toolbar_widget)

        content_splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(12, 12, 12, 12)

        left_title = QLabel("📋 任务列表")
        left_title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.left_title = left_title
        left_title.setStyleSheet("color: #333333;")

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        # 分段控件容器
        segment_container = QFrame()
        segment_container.setObjectName("segmentContainer")
        segment_container.setStyleSheet("""
            QFrame#segmentContainer {
                background-color: #F0F2F8;
                border-radius: 10px;
                padding: 3px;
            }
        """)
        segment_layout = QHBoxLayout(segment_container)
        segment_layout.setContentsMargins(3, 3, 3, 3)
        segment_layout.setSpacing(0)

        self.filter_all_btn = QPushButton("全部")
        self.filter_all_btn.setFixedHeight(30)
        self.filter_all_btn.setFixedWidth(70)
        self.filter_all_btn.setCursor(Qt.PointingHandCursor)
        self.filter_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B9D;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #EC407A;
            }
        """)
        self.filter_all_btn.clicked.connect(lambda: self.set_task_filter("all"))
        segment_layout.addWidget(self.filter_all_btn)

        self.filter_today_btn = QPushButton("今日任务")
        self.filter_today_btn.setFixedHeight(30)
        self.filter_today_btn.setFixedWidth(80)
        self.filter_today_btn.setCursor(Qt.PointingHandCursor)
        self.filter_today_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 107, 157, 0.08);
                color: #FF6B9D;
            }
        """)
        self.filter_today_btn.clicked.connect(lambda: self.set_task_filter("today"))
        segment_layout.addWidget(self.filter_today_btn)

        filter_layout.addWidget(segment_container)

        # 搜索框
        search_container = QWidget()
        search_container.setFixedWidth(200)
        search_container.setStyleSheet("background: transparent;")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索任务...")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #F5F7FA;
                border: 1.5px solid #E8E8E8;
                border-radius: 10px;
                padding: 0 14px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1.5px solid #FF6B9D;
                background-color: white;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        filter_layout.addWidget(search_container)

        # 标签筛选下拉框
        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.addItem("所有标签")
        self.tag_filter_combo.setFixedHeight(36)
        self.tag_filter_combo.setFixedWidth(120)
        self.tag_filter_combo.setCursor(Qt.PointingHandCursor)
        self.tag_filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #F5F7FA;
                border: 1.5px solid #E8E8E8;
                border-radius: 10px;
                padding: 0 14px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1.5px solid rgba(255, 107, 157, 0.4);
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #999;
                margin-right: 10px;
            }
        """)
        self.tag_filter_combo.currentTextChanged.connect(self.on_tag_filter_changed)
        filter_layout.addWidget(self.tag_filter_combo)
        
        filter_layout.addStretch()
        left_layout.addLayout(filter_layout)
        self.current_filter = "all"
        self.current_search = ""
        self.current_tag = "所有标签"
        
        # 初始化标签筛选下拉框
        self.update_tag_filter()

        self.task_list_widget = QListWidget()
        self.task_list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.task_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.task_list_widget.setSpacing(10)
        self.task_list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.task_list_widget.model().rowsMoved.connect(self.on_tasks_reordered)
        left_layout.addWidget(self.task_list_widget, stretch=1)

        content_splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumHeight(300)
        apply_tab_style(self.tab_widget)
        # tab切换动画已移除（QGraphicsOpacityEffect导致子控件渲染异常）

        self.ai_tab = QWidget()
        self.init_ai_tab()
        self.tab_widget.addTab(self.ai_tab, "🤖 AI助手")

        self.pomodoro_tab = PomodoroTab(self.stats_manager, self.task_manager, self.refresh_tasks)
        self.tab_widget.addTab(self.pomodoro_tab, "🍅 番茄钟")

        self.stats_tab = StatsTab(self.stats_manager, self.task_manager)
        self.tab_widget.addTab(self.stats_tab, "📊 数据统计")

        self.reminder_tab = ReminderTab(self.reminder_manager, main_window=self, parent=self)
        self.tab_widget.addTab(self.reminder_tab, "⏰ 提醒管理")

        self.calendar_tab = CalendarWidget(self.task_manager, self.reminder_manager)
        self.tab_widget.addTab(self.calendar_tab, "📅 日历视图")

        right_layout.addWidget(self.tab_widget, stretch=1)

        content_splitter.addWidget(right_widget)
        content_splitter.setSizes([550, 550])

        main_layout.addWidget(content_splitter, stretch=1)

        self.init_bottom_bar(main_layout)

    def create_menu_bar(self):
        menubar = self.menuBar()

        menubar.setStyleSheet("""
            QMenuBar {
                background-color: white;
                border-bottom: 2px solid #F0F0F0;
                padding: 4px 0;
                font-size: 13px;
                font-weight: 500;
            }
            QMenuBar::item {
                padding: 8px 16px;
                background-color: transparent;
                color: #333333;
                border-radius: 6px;
                margin: 0 2px;
            }
            QMenuBar::item:selected {
                background-color: #FFF0F3;
                color: #FF6B9D;
            }
            QMenuBar::item:pressed {
                background-color: #FF8FAB;
                color: white;
            }
            QMenu {
                background-color: white;
                border: 2px solid #F0F0F0;
                border-radius: 8px;
                padding: 8px 0;
            }
            QMenu::item {
                padding: 10px 24px;
                color: #333333;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #FFF0F3;
                color: #FF8FAB;
                border-radius: 0;
            }
            QMenu::separator {
                height: 1px;
                background-color: #F0F0F0;
                margin: 6px 12px;
            }
        """)

        file_menu = menubar.addMenu("文件")
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        settings_menu = menubar.addMenu("设置")
        api_config_action = settings_menu.addAction("⚙️ 基础设置")
        api_config_action.triggered.connect(self.open_settings)
        persona_config_action = settings_menu.addAction("人设配置")
        persona_config_action.triggered.connect(self.open_persona_settings)
        theme_action = settings_menu.addAction("个性化主题")
        theme_action.triggered.connect(self.open_theme_settings)
        tag_manager_action = settings_menu.addAction("🏷️ 标签管理")
        tag_manager_action.triggered.connect(self.open_tag_manager)
        settings_menu.addSeparator()
        backup_action = settings_menu.addAction("💾 数据备份/恢复")
        backup_action.triggered.connect(self.show_backup_dialog)
        achievement_action = settings_menu.addAction("🏆 成就殿堂")
        achievement_action.triggered.connect(self.show_achievement_dialog)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        smart_sort_action = tools_menu.addAction("📊 智能排序")
        smart_sort_action.triggered.connect(self.show_smart_sort_dialog)
        weekly_report_action = tools_menu.addAction("📋 生成周报")
        weekly_report_action.triggered.connect(self.show_weekly_report)

        help_menu = menubar.addMenu("帮助")
        api_wizard_action = help_menu.addAction("API配置向导")
        api_wizard_action.triggered.connect(self.show_api_wizard)
        memory_management_action = help_menu.addAction("🧠 记忆管理")
        memory_management_action.triggered.connect(self.show_memory_management)
        memory_filter_action = help_menu.addAction("📊 智能记忆过滤")
        memory_filter_action.triggered.connect(self.show_memory_filter)
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def init_ai_tab(self):
        ai_layout = QVBoxLayout(self.ai_tab)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(0)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("border: none; background-color: #F5F7FA;")
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_container_layout = QVBoxLayout(self.chat_container)
        self.chat_container_layout.setContentsMargins(15, 15, 15, 15)
        self.chat_container_layout.setSpacing(12)
        self.chat_container_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        ai_layout.addWidget(self.chat_scroll, stretch=1)

        input_container = QWidget()
        input_container.setStyleSheet("background-color: rgba(255,255,255,0.92); border-top: 1px solid rgba(0,0,0,0.06);")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(10)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入消息与AI对话...")
        self.chat_input.setMinimumHeight(46)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E8E8E8;
                border-radius: 23px;
                padding: 10px 20px;
                font-size: 14px;
                background-color: #F5F7FA;
            }
            QLineEdit:focus {
                border-color: #FF6B9D;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #D0D0D0;
                background-color: #FAFAFA;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input, stretch=1)

        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(44, 44)
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #888;
                border: 2px solid #E8E8E8;
                border-radius: 22px;
                font-size: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #FFF5F7;
                color: #FF8FAB;
                border-color: #FFB6C1;
            }
        """)
        self.voice_btn.setToolTip("语音输入")
        self.voice_btn.clicked.connect(self.voice_input)
        input_layout.addWidget(self.voice_btn)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(80, 44)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
            QPushButton:pressed {
                background-color: #E53959;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #999;
            }
        """)
        self.send_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(self.send_btn)

        ai_layout.addWidget(input_container)

        self.conversation_history = []
        self._pending_goal = None
        self._pending_intent_check = False

        welcome_msg = "您好！我是您的 AI 助手。有什么我可以帮您的吗？您可以：\n• 告诉我您的目标，我会帮您拆解成任务\n• 询问任何问题\n• 输入「帮我出一份数学试卷」等考试相关需求"
        self._add_ai_message(welcome_msg, show_adoption=False)  # 欢迎消息不显示采纳按钮

    def init_bottom_bar(self, main_layout):
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(75)
        bottom_widget.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 0.95);
            border-top: 1px solid rgba(255, 182, 193, 0.3);
        """)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(20, 12, 20, 12)
        bottom_layout.setSpacing(12)

        add_button = QPushButton("➕ 添加任务")
        add_button.setMinimumHeight(50)
        add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF8FAB,
                    stop:1 #FF6B9D);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF6B9D,
                    stop:1 #EC407A);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #EC407A,
                    stop:1 #D81B60);
            }
        """)
        add_button.clicked.connect(self._add_task_with_ripple)
        bottom_layout.addWidget(add_button)

        # 添加导出按钮
        export_button = QPushButton("📊 导出数据")
        export_button.setMinimumHeight(50)
        export_button.setFixedWidth(120)
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #66BB6A,
                    stop:1 #4CAF50);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4CAF50,
                    stop:1 #43A047);
            }
            QPushButton:pressed {
                background: #388E3C;
            }
        """)
        export_button.clicked.connect(self.export_tasks)
        bottom_layout.addWidget(export_button)

        # 添加批量删除按钮
        delete_button = QPushButton("🗑️ 批量删除")
        delete_button.setMinimumHeight(50)
        delete_button.setFixedWidth(120)
        delete_button.setCursor(Qt.PointingHandCursor)
        delete_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #EF5350,
                    stop:1 #F44336);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F44336,
                    stop:1 #D32F2F);
            }
            QPushButton:pressed {
                background: #C62828;
            }
        """)
        delete_button.clicked.connect(self.batch_delete_tasks)
        bottom_layout.addWidget(delete_button)

        main_layout.addWidget(bottom_widget)

    def create_task_item(self, task):
        item = QListWidgetItem(self.task_list_widget)
        item.setSizeHint(QSize(0, 88))
        item.setData(Qt.UserRole, task.id)

        card_widget = TaskCardWidget(task, self.task_manager, self.stats_manager, self.tag_manager, self.task_list_widget)
        card_widget.deleteRequested.connect(self.on_task_delete)
        card_widget.completionToggled.connect(self.on_task_completion_changed)
        card_widget.focusRequested.connect(self.on_focus_task)
        card_widget.renameRequested.connect(self.on_task_renamed)
        card_widget.tagClicked.connect(self.on_tag_clicked)  # 连接标签点击信号

        self.task_list_widget.setItemWidget(item, card_widget)
        return item

    def set_task_filter(self, filter_type):
        self.current_filter = filter_type
        if filter_type == "all":
            self.filter_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B9D;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #EC407A;
                }
            """)
            self.filter_today_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #888;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(255, 107, 157, 0.08);
                    color: #FF6B9D;
                }
            """)
        else:
            self.filter_today_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B9D;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #EC407A;
                }
            """)
            self.filter_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #888;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(255, 107, 157, 0.08);
                    color: #FF6B9D;
                }
            """)
        self.refresh_tasks()

    def refresh_tasks(self):
        # 确保 task_list_widget 已创建
        if not hasattr(self, 'task_list_widget'):
            return
        self.task_list_widget.clear()

        tasks = self.task_manager.get_tasks_sorted_by_due()

        # 应用日期筛选
        if self.current_filter == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            tasks = [t for t in tasks if t.due_date and not t.completed and (
                (isinstance(t.due_date, str) and t.due_date.startswith(today)) or
                (isinstance(t.due_date, datetime) and t.due_date.strftime("%Y-%m-%d") == today)
            )]
        
        # 应用搜索筛选
        if hasattr(self, 'current_search') and self.current_search:
            tasks = [t for t in tasks if self.current_search.lower() in t.name.lower()]
        
        # 应用标签筛选
        if hasattr(self, 'current_tag') and self.current_tag and self.current_tag != "所有标签":
            # 去掉 # 前缀进行匹配
            tag_name = self.current_tag.lstrip('#')
            tasks = [t for t in tasks if hasattr(t, 'tags') and tag_name in t.tags]

        for task in tasks:
            self.create_task_item(task)
    
    def on_search_changed(self, text):
        """搜索框文本改变时"""
        self.current_search = text
        self.refresh_tasks()
    
    def on_tag_filter_changed(self, tag):
        """标签筛选改变时"""
        self.current_tag = tag
        self.refresh_tasks()
    
    def update_tag_filter(self):
        """更新标签筛选下拉框"""
        if not hasattr(self, 'tag_filter_combo'):
            return
        
        current_tag = self.tag_filter_combo.currentText()
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("所有标签")
        
        # 从 tag_manager 获取所有标签（预设+自定义）
        all_tags = self.tag_manager.get_all_tags()
        for tag in all_tags:
            self.tag_filter_combo.addItem(f"#{tag}")
        
        # 恢复之前的选择
        index = self.tag_filter_combo.findText(current_tag)
        if index >= 0:
            self.tag_filter_combo.setCurrentIndex(index)

    def on_tasks_reordered(self, parent, start, end, destination, row):
        new_order = []
        for i in range(self.task_list_widget.count()):
            item = self.task_list_widget.item(i)
            task_id = item.data(Qt.UserRole)
            task = self.task_manager.get_task_by_id(task_id)
            if task:
                new_order.append(task)

        self.task_manager.tasks = new_order
        self.task_manager.save_tasks()

    def on_task_delete(self, task):
        self.task_manager.delete_task(task.id)
        self.refresh_tasks()
        if hasattr(self, 'stats_tab'):
            self.stats_tab.refresh_stats()

    def on_task_completion_changed(self, task):
        if hasattr(self, 'stats_tab'):
            self.stats_tab.refresh_stats()

    def on_task_renamed(self, task, new_name):
        pass
    
    def on_tag_clicked(self, tag: str):
        """标签点击事件 - 更改任务标签"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout

        # 获取所有可用标签
        all_tags = self.tag_manager.get_all_tags()
        if not all_tags:
            all_tags = ["工作", "学习", "生活", "娱乐", "重要", "紧急"]

        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"更改标签「{tag}」")
        dialog.setFixedSize(300, 400)
        dialog.setStyleSheet("background-color: #FAFAFA;")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel(f"选择新标签替换「{tag}」")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # 标签列表
        tag_list = QListWidget()
        tag_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #FF8FAB;
                color: white;
            }
            QListWidget::item:hover {
                background: #FFF0F3;
            }
        """)

        for t in all_tags:
            tag_list.addItem(t)
            # 默认选中当前标签
            if t == tag:
                tag_list.setCurrentRow(tag_list.count() - 1)

        layout.addWidget(tag_list)

        # 按钮行
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F5;
                color: #666;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background: #E0E0E0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        remove_btn = QPushButton("移除标签")
        remove_btn.setFixedHeight(36)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: #FFEBEE;
                color: #D32F2F;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background: #FFCDD2; }
        """)
        remove_btn.clicked.connect(lambda: self._change_tag(tag, None, dialog))
        btn_layout.addWidget(remove_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setFixedHeight(36)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #FF8FAB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #FF6B8A; }
        """)
        ok_btn.clicked.connect(lambda: self._change_tag(tag, tag_list.currentItem().text() if tag_list.currentItem() else tag, dialog))
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)
        dialog.exec_()

    def _change_tag(self, old_tag: str, new_tag: str, dialog):
        """更改标签"""
        dialog.accept()

        if new_tag is None:
            # 移除标签 - 找到所有包含该标签的任务
            for task in self.task_manager.tasks:
                if old_tag in getattr(task, 'tags', []):
                    task.tags.remove(old_tag)
                    self.task_manager.save_tasks()
            self.refresh_tasks()
            self.statusBar().showMessage(f"已移除标签「{old_tag}」", 3000)
        elif new_tag != old_tag:
            # 更换标签
            for task in self.task_manager.tasks:
                if old_tag in getattr(task, 'tags', []):
                    task.tags.remove(old_tag)
                    task.tags.append(new_tag)
                    self.task_manager.save_tasks()
            self.refresh_tasks()
            self.statusBar().showMessage(f"已将标签「{old_tag}」更改为「{new_tag}」", 3000)

    def _analyze_urgent_task(self, new_task, due_date):
        """分析紧急任务与现有任务的冲突"""
        from datetime import datetime

        conflicts = []
        suggestions = []

        # 检查时间冲突
        if due_date:
            try:
                if isinstance(due_date, str):
                    new_due = datetime.strptime(due_date[:16], "%Y-%m-%d %H:%M")
                else:
                    new_due = due_date

                # 检查同一天的其他高优先级任务
                same_day_tasks = []
                for task in self.task_manager.tasks:
                    if task.id == new_task.id or task.completed:
                        continue
                    task_due = getattr(task, 'due_date', None)
                    if task_due:
                        try:
                            if isinstance(task_due, str):
                                td = datetime.strptime(task_due[:16], "%Y-%m-%d %H:%M")
                            else:
                                td = task_due
                            # 同一天且时间接近（2小时内）
                            if td.date() == new_due.date():
                                time_diff = abs((td - new_due).total_seconds() / 3600)
                                if time_diff < 2:
                                    same_day_tasks.append((task, time_diff))
                        except:
                            pass

                if same_day_tasks:
                    same_day_tasks.sort(key=lambda x: x[1])
                    for task, diff in same_day_tasks[:3]:
                        conflicts.append(f"• {task.name}（时间接近 {diff:.0f}小时）")

            except:
                pass

        # 检查高优先级任务数量
        high_priority_count = sum(1 for t in self.task_manager.tasks if not t.completed and getattr(t, 'priority', 2) >= 4)

        if high_priority_count > 3:
            suggestions.append(f"当前有 {high_priority_count} 个高优先级任务，建议重新评估优先级")

        # 显示分析结果
        if conflicts or suggestions:
            msg = f"📋 紧急任务分析\n\n"
            msg += f"新任务：「{new_task.name}」\n\n"

            if conflicts:
                msg += "⚠️ 时间冲突：\n" + "\n".join(conflicts) + "\n\n"

            if suggestions:
                msg += "💡 建议：\n" + "\n".join(f"• {s}" for s in suggestions) + "\n\n"

            msg += "是否打开智能排序查看详情？"

            reply = QMessageBox.question(self, "紧急任务分析", msg,
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.show_smart_sort_dialog()

    def highlight_tag_filter(self, tag: str):
        """高亮显示当前筛选的标签"""
        # 重置所有筛选按钮样式
        self.set_task_filter(self.current_filter)
        
        # 显示筛选提示
        if hasattr(self, 'tag_filter_label'):
            self.tag_filter_label.setText(f"🏷️ 筛选: {tag}")
            self.tag_filter_label.show()
        else:
            self.tag_filter_label = QLabel(f"🏷️ 筛选: {tag}")
            self.tag_filter_label.setStyleSheet("""
                QLabel {
                    background-color: #E3F2FD;
                    color: #1976D2;
                    border-radius: 15px;
                    padding: 8px 15px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
            # 插入到任务列表顶部
            self.main_layout.insertWidget(2, self.tag_filter_label)
        
        # 添加清除筛选按钮
        if not hasattr(self, 'clear_tag_filter_btn'):
            self.clear_tag_filter_btn = QPushButton("✕ 清除筛选")
            self.clear_tag_filter_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF5722;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 8px 15px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #E64A19;
                }
            """)
            self.clear_tag_filter_btn.clicked.connect(self.clear_tag_filter)
            self.main_layout.insertWidget(3, self.clear_tag_filter_btn)
        else:
            self.clear_tag_filter_btn.show()
    
    def clear_tag_filter(self):
        """清除标签筛选"""
        self.current_tag_filter = None
        self.refresh_tasks()
        
        # 隐藏筛选提示和清除按钮
        if hasattr(self, 'tag_filter_label'):
            self.tag_filter_label.hide()
        if hasattr(self, 'clear_tag_filter_btn'):
            self.clear_tag_filter_btn.hide()

    def on_focus_task(self, task):
        dialog = PomodoroDialog(task.estimated_minutes, task.name, self)
        dialog.finished.connect(lambda duration, name: self.on_pomodoro_finished(task, duration))
        dialog.exec_()

    def on_pomodoro_finished(self, task, duration):
        self.stats_manager.add_focus_time(duration, task_name=task.name)
        self.task_manager.toggle_complete(task.id)
        self.refresh_tasks()
        if hasattr(self, 'stats_tab'):
            self.stats_tab.refresh_stats()

    def _add_task_with_ripple(self):
        """添加任务按钮点击 — 带涟漪动画"""
        from animation_utils import RippleAnimation
        button = self.sender()
        if button:
            ripple = RippleAnimation(button)
            ripple.click_ripple()
        # 延迟打开对话框让动画先播放
        QTimer.singleShot(150, self.add_task)

    def add_task(self):
        dialog = AddTaskDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            task_name = result[0]
            total_minutes = result[1]
            due_date = result[2]
            priority = result[3] if len(result) > 3 else 2
            tags = result[4] if len(result) > 4 else []

            if task_name and total_minutes > 0:
                task = self.task_manager.add_task(task_name, total_minutes, due_date=due_date, tags=tags)
                if task and priority != 2:
                    task.priority = priority
                    self.task_manager.save_tasks()

                # 紧急任务分析
                if priority >= 4:  # 高优先级或紧急
                    self._analyze_urgent_task(task, due_date)

                self.refresh_tasks()
                self.update_tag_filter()  # 更新标签筛选
                if hasattr(self, 'stats_tab'):
                    self.stats_tab.refresh_stats()
    
    def export_tasks(self):
        """导出任务数据"""
        from PyQt5.QtWidgets import QFileDialog
        import csv
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出任务数据",
            "tasks_export.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                # 写入表头
                writer.writerow([
                    '任务ID', '任务名称', '预计时长(分钟)', '实际时长(分钟)', 
                    '是否完成', '创建日期', '完成日期', '截止日期', 
                    '优先级', '状态', '标签', '来源'
                ])
                
                # 写入任务数据
                for task in self.task_manager.tasks:
                    writer.writerow([
                        task.id,
                        task.name,
                        task.estimated_minutes,
                        task.actual_minutes,
                        '是' if task.completed else '否',
                        task.created_date,
                        task.completed_at or '',
                        task.due_date or '',
                        task.priority,
                        task.status,
                        ', '.join(task.tags) if hasattr(task, 'tags') else '',
                        task.source
                    ])
            
            QMessageBox.information(self, "导出成功", f"任务数据已导出到：\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出任务数据时出错：\n{str(e)}")
    
    def batch_delete_tasks(self):
        """批量删除任务"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QCheckBox
        
        # 获取所有任务
        all_tasks = self.task_manager.tasks
        if not all_tasks:
            QMessageBox.information(self, "提示", "没有可删除的任务")
            return
        
        # 创建批量删除对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("批量删除任务")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 快捷操作按钮
        quick_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_completed_btn = QPushButton("选择已完成")
        select_none_btn = QPushButton("取消全选")
        
        quick_layout.addWidget(select_all_btn)
        quick_layout.addWidget(select_completed_btn)
        quick_layout.addWidget(select_none_btn)
        layout.addLayout(quick_layout)
        
        # 任务列表
        task_list = QListWidget()
        task_list.setSelectionMode(QListWidget.MultiSelection)  # 允许多选
        task_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #DDD;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #EEE;
            }
            QListWidget::item:selected {
                background-color: #FFB6C1;
                color: black;
            }
        """)
        
        for task in all_tasks:
            status = "✅" if task.completed else "⏳"
            tags = f" [{', '.join(['#'+t for t in task.tags])}]" if hasattr(task, 'tags') and task.tags else ""
            task_list.addItem(f"{status} {task.name}{tags}")
        
        layout.addWidget(task_list)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 快捷操作连接
        select_all_btn.clicked.connect(lambda: task_list.selectAll())
        select_none_btn.clicked.connect(lambda: task_list.clearSelection())
        select_completed_btn.clicked.connect(lambda: self._select_completed_tasks(task_list, all_tasks))
        
        if dialog.exec_() == QDialog.Accepted:
            selected_items = task_list.selectedItems()
            if selected_items:
                # 获取选中的任务索引
                selected_indices = [task_list.row(item) for item in selected_items]
                selected_task_ids = [all_tasks[i].id for i in selected_indices]
                
                # 确认删除
                reply = QMessageBox.question(
                    self, '确认删除',
                    f'确定要删除选中的 {len(selected_task_ids)} 个任务吗？',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    deleted_count = self.task_manager.delete_multiple_tasks(selected_task_ids)
                    self.refresh_tasks()
                    if hasattr(self, 'stats_tab'):
                        self.stats_tab.refresh_stats()
                    QMessageBox.information(self, "删除成功", f"已删除 {deleted_count} 个任务")
    
    def _select_completed_tasks(self, task_list, all_tasks):
        """选择所有已完成的任务"""
        task_list.clearSelection()
        for i, task in enumerate(all_tasks):
            if task.completed:
                task_list.item(i).setSelected(True)
    
    def _auto_clear_completed_tasks(self):
        """启动时自动清理已完成的任务"""
        completed_count = self.task_manager.clear_completed_tasks()
        if completed_count > 0:
            print(f"自动清理了 {completed_count} 个已完成的任务")

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def open_persona_settings(self):
        from persona_dialog import PersonaDialog
        dialog = PersonaDialog(self)
        dialog.exec_()

    def open_theme_settings(self):
        dialog = ThemeDialog(self)
        dialog.exec_()

    def show_api_wizard(self):
        wizard = ApiWizard(self)
        wizard.exec_()

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()

    def show_backup_dialog(self):
        """显示备份/恢复对话框"""
        from PyQt5.QtWidgets import QFileDialog, QListWidget, QListWidgetItem

        dialog = QDialog(self)
        dialog.setWindowTitle("💾 数据备份与恢复")
        dialog.setFixedSize(500, 450)
        dialog.setStyleSheet("background-color: #FAFAFA;")

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("💾 数据备份与恢复")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #FF8FAB;")
        layout.addWidget(title)

        # 备份区域
        backup_group = QGroupBox("创建备份")
        backup_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        backup_layout = QVBoxLayout(backup_group)

        backup_btn = QPushButton("📤 创建备份")
        backup_btn.setFixedHeight(40)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FF6B8A; }
        """)
        backup_btn.clicked.connect(lambda: self._create_backup(dialog))
        backup_layout.addWidget(backup_btn)
        layout.addWidget(backup_group)

        # 恢复区域
        restore_group = QGroupBox("恢复数据")
        restore_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        restore_layout = QVBoxLayout(restore_group)

        # 备份列表
        self.backup_list = QListWidget()
        self.backup_list.setFixedHeight(120)
        self.backup_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
        """)
        self._refresh_backup_list()
        restore_layout.addWidget(self.backup_list)

        # 恢复按钮行
        btn_row = QHBoxLayout()
        restore_btn = QPushButton("📥 恢复选中")
        restore_btn.setFixedHeight(36)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        restore_btn.clicked.connect(lambda: self._restore_backup(dialog))
        btn_row.addWidget(restore_btn)

        import_btn = QPushButton("📁 导入备份文件")
        import_btn.setFixedHeight(36)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        import_btn.clicked.connect(lambda: self._import_backup(dialog))
        btn_row.addWidget(import_btn)
        btn_row.addStretch()
        restore_layout.addLayout(btn_row)
        layout.addWidget(restore_group)

        dialog.exec_()

    def _create_backup(self, parent_dialog):
        """创建备份"""
        backup_manager = BackupManager(
            task_manager=self.task_manager,
            reminder_manager=self.reminder_manager,
            stats_manager=self.stats_manager,
            tag_manager=self.tag_manager,
            config_manager=self.config_manager,
            memory_manager=self.memory_manager
        )
        success, message, path = backup_manager.create_backup()
        if success:
            QMessageBox.information(parent_dialog, "成功", f"{message}\n\n备份位置：{path}")
            self._refresh_backup_list()
        else:
            QMessageBox.warning(parent_dialog, "失败", message)

    def _refresh_backup_list(self):
        """刷新备份列表"""
        self.backup_list.clear()
        backup_manager = BackupManager()
        backups = backup_manager.get_backup_list()
        for backup in backups:
            size_kb = backup["size"] / 1024
            item = QListWidgetItem(f"📅 {backup['time']} ({size_kb:.1f} KB)")
            item.setData(Qt.UserRole, backup["path"])
            self.backup_list.addItem(item)
        if not backups:
            item = QListWidgetItem("暂无备份文件")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.backup_list.addItem(item)

    def _restore_backup(self, parent_dialog):
        """恢复选中的备份"""
        current_item = self.backup_list.currentItem()
        if not current_item:
            QMessageBox.warning(parent_dialog, "提示", "请先选择一个备份文件")
            return

        backup_path = current_item.data(Qt.UserRole)
        if not backup_path:
            return

        reply = QMessageBox.question(
            parent_dialog, "确认恢复",
            "恢复将覆盖当前所有数据，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            backup_manager = BackupManager(
                task_manager=self.task_manager,
                reminder_manager=self.reminder_manager,
                stats_manager=self.stats_manager,
                tag_manager=self.tag_manager,
                config_manager=self.config_manager,
                memory_manager=self.memory_manager
            )
            success, message = backup_manager.restore_backup(backup_path)
            if success:
                QMessageBox.information(parent_dialog, "成功", message)
                # 刷新界面
                self.refresh_tasks()
                if hasattr(self, 'reminder_tab'):
                    self.reminder_tab.refresh_reminders()
            else:
                QMessageBox.warning(parent_dialog, "失败", message)

    def _import_backup(self, parent_dialog):
        """导入外部备份文件"""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            parent_dialog, "选择备份文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            reply = QMessageBox.question(
                parent_dialog, "确认恢复",
                "恢复将覆盖当前所有数据，是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                backup_manager = BackupManager(
                    task_manager=self.task_manager,
                    reminder_manager=self.reminder_manager,
                    stats_manager=self.stats_manager,
                    tag_manager=self.tag_manager,
                    config_manager=self.config_manager,
                    memory_manager=self.memory_manager
                )
                success, message = backup_manager.restore_backup(file_path)
                if success:
                    QMessageBox.information(parent_dialog, "成功", message)
                    self.refresh_tasks()
                    if hasattr(self, 'reminder_tab'):
                        self.reminder_tab.refresh_reminders()
                else:
                    QMessageBox.warning(parent_dialog, "失败", message)

    def show_achievement_dialog(self):
        """显示成就对话框"""
        dialog = AchievementDialog(self.achievement_manager, self)
        dialog.exec_()

    def show_smart_sort_dialog(self):
        """显示智能排序对话框"""
        try:
            from smart_priority import SmartPriorityEngine
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton

            dialog = QDialog(self)
            dialog.setWindowTitle("📊 智能任务排序")
            dialog.setFixedSize(500, 600)
            dialog.setStyleSheet("background-color: #FAFAFA;")

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            # 标题
            title = QLabel("智能优先级排序")
            title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
            title.setStyleSheet("color: #FF8FAB;")
            layout.addWidget(title)

            # 说明
            desc = QLabel("基于截止时间、优先级、标签重要性等多维度智能排序")
            desc.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(desc)

            # 任务列表
            list_widget = QListWidget()
            list_widget.setStyleSheet("""
                QListWidget {
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 5px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #F0F0F0;
                }
                QListWidget::item:selected {
                    background: #FFF0F3;
                    color: #333;
                }
            """)

            engine = SmartPriorityEngine(self.task_manager, self.stats_manager)
            sorted_tasks = engine.sort_tasks_by_priority()

            for task in sorted_tasks:
                score = engine.calculate_smart_priority(task)

                # 显示格式：分数 | 任务名
                item_text = f"[{score:.0f}分] {task.name}"
                if task.due_date:
                    due_str = task.due_date if isinstance(task.due_date, str) else task.due_date.strftime("%Y-%m-%d %H:%M")
                    item_text += f" 📅 {due_str[:10] if len(due_str) >= 10 else due_str}"
                list_widget.addItem(item_text)

            layout.addWidget(list_widget)

            # 详情显示
            detail_label = QLabel("点击任务查看排序详情")
            detail_label.setStyleSheet("color: #888; font-size: 11px; padding: 10px; background: white; border-radius: 6px;")
            layout.addWidget(detail_label)

            def on_item_clicked(item):
                idx = list_widget.row(item)
                if idx < len(sorted_tasks):
                    task = sorted_tasks[idx]
                    breakdown = engine.get_priority_breakdown(task)
                    detail_text = f"""
任务：{task.name}
总分：{breakdown['total_score']:.1f}
├─ 用户优先级：{breakdown['user_priority']:.1f}分
├─ 时间紧迫度：{breakdown['urgency']:.1f}分
├─ 标签重要性：{breakdown['tag_importance']:.1f}分
├─ 任务年龄：{breakdown['age']:.1f}分
└─ 历史完成率调整：{breakdown['completion_rate']:+.1f}分

💡 {breakdown['suggestion']}
"""
                    detail_label.setText(detail_text)
                    detail_label.setStyleSheet("color: #333; font-size: 11px; padding: 10px; background: white; border-radius: 6px;")

            list_widget.itemClicked.connect(on_item_clicked)

            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.setFixedHeight(40)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF8FAB;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #FF6B8A; }
            """)
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec_()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"智能排序失败: {str(e)}")

    def show_weekly_report(self):
        """显示周报"""
        try:
            from weekly_report import WeeklyReportGenerator
            from PyQt5.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QPushButton, QLabel

            generator = WeeklyReportGenerator(self.task_manager, self.stats_manager)
            report = generator.generate_report(week_offset=0)

            dialog = QDialog(self)
            dialog.setWindowTitle("📋 本周工作周报")
            dialog.setFixedSize(600, 700)
            dialog.setStyleSheet("background-color: #FAFAFA;")

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            # 标题
            title = QLabel("📊 本周工作周报")
            title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
            title.setStyleSheet("color: #FF8FAB;")
            layout.addWidget(title)

            # 效率评分
            score_label = QLabel(f"效率评分：{report['score']:.0f}/100")
            score_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            if report['score'] >= 80:
                score_label.setStyleSheet("color: #4CAF50;")
            elif report['score'] >= 60:
                score_label.setStyleSheet("color: #FF9800;")
            else:
                score_label.setStyleSheet("color: #F44336;")
            layout.addWidget(score_label)

            # 报告内容
            report_text = QTextEdit()
            report_text.setReadOnly(True)
            report_text.setStyleSheet("""
                QTextEdit {
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 13px;
                }
            """)
            report_text.setPlainText(generator.format_report_text(report))
            layout.addWidget(report_text)

            # 按钮
            btn_layout = QHBoxLayout()

            copy_btn = QPushButton("📋 复制报告")
            copy_btn.setFixedHeight(36)
            copy_btn.setStyleSheet("""
                QPushButton {
                    background: #E3F2FD;
                    color: #1976D2;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                }
                QPushButton:hover { background: #BBDEFB; }
            """)
            copy_btn.clicked.connect(lambda: self._copy_report(generator.format_report_text(report)))
            btn_layout.addWidget(copy_btn)

            close_btn = QPushButton("关闭")
            close_btn.setFixedHeight(36)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF8FAB;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #FF6B8A; }
            """)
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)
            dialog.exec_()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"生成周报失败: {str(e)}")

    def _copy_report(self, text: str):
        """复制报告到剪贴板"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "成功", "周报已复制到剪贴板！")

    def open_tag_manager(self):
        """打开标签管理对话框"""
        dialog = TagManagerDialog(self.tag_manager, self.task_manager, self)
        dialog.exec_()
        # 刷新标签筛选下拉框
        self.update_tag_filter()

    def _add_user_message(self, message):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        bubble = QFrame(container)
        bubble.setStyleSheet("""
            QFrame {
                background-color: #FF8FAB;
                border-radius: 15px;
                padding: 10px 15px;
            }
        """)
        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("color: white; font-size: 14px;")
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)

        container_layout.addWidget(bubble)
        container_layout.addStretch()

        self.chat_container_layout.insertWidget(
            self.chat_container_layout.count() - 1,
            container
        )
        self._scroll_to_bottom()

    def _add_ai_message(self, message, with_action_button=None, show_adoption=False):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()

        bubble = QFrame(container)
        bubble.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                padding: 10px 15px;
                border: 1px solid #E8E8E8;
            }
        """)

        content_layout = QVBoxLayout(bubble)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("color: #333; font-size: 14px;")
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_layout.addWidget(label)

        if with_action_button:
            content_layout.addWidget(with_action_button)
        
        # 📊 建议采纳按钮（只在AI给出建议时显示，且明确启用）
        # 只有当 show_adoption=True 时才显示采纳按钮
        has_suggestion = False
        if show_adoption:
            suggestion_keywords = ['建议', '推荐', '应该', '可以', '需要', '最好', '记得', '提醒']
            has_suggestion = any(keyword in message for keyword in suggestion_keywords)
        
        if has_suggestion:
            adoption_layout = QHBoxLayout()
            adoption_layout.setSpacing(10)
            
            adopt_btn = QPushButton("✅ 采纳")
            adopt_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8F5E9;
                    color: #4CAF50;
                    border: 1px solid #81C784;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #C8E6C9;
                }
                QPushButton:disabled {
                    background-color: #F5F5F5;
                    color: #BDBDBD;
                    border: 1px solid #E0E0E0;
                }
            """)
            adopt_btn.setCursor(Qt.PointingHandCursor)
            adopt_btn.clicked.connect(lambda: self._on_suggestion_adopted(True, adopt_btn, reject_btn))
            adoption_layout.addWidget(adopt_btn)
            
            reject_btn = QPushButton("❌ 忽略")
            reject_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFEBEE;
                    color: #F44336;
                    border: 1px solid #E57373;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #FFCDD2;
                }
                QPushButton:disabled {
                    background-color: #F5F5F5;
                    color: #BDBDBD;
                    border: 1px solid #E0E0E0;
                }
            """)
            reject_btn.setCursor(Qt.PointingHandCursor)
            reject_btn.clicked.connect(lambda: self._on_suggestion_adopted(False, adopt_btn, reject_btn))
            adoption_layout.addWidget(reject_btn)
            
            adoption_layout.addStretch()
            content_layout.addLayout(adoption_layout)
        
        # 🔒 AI 伦理：添加局限性说明按钮
        ethics_btn = QPushButton("⚠️ AI 局限性说明")
        ethics_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFF3E0;
                color: #F57C00;
                border: 1px solid #FFB74D;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFE0B2;
            }
        """)
        ethics_btn.setCursor(Qt.PointingHandCursor)
        ethics_btn.clicked.connect(lambda: self._show_ai_limitations(message))
        content_layout.addWidget(ethics_btn)

        container_layout.addWidget(bubble)

        self.chat_container_layout.insertWidget(
            self.chat_container_layout.count() - 1,
            container
        )
        self._scroll_to_bottom()
        return container

    def _show_ai_limitations(self, ai_message: str):
        """显示 AI 局限性说明"""
        # 分析 AI 消息类型
        decision_type = self._detect_decision_type(ai_message)
        
        # 生成局限性说明（确保 ethics_analyzer 已初始化）
        if hasattr(self, 'ethics_analyzer') and self.ethics_analyzer:
            explanation = self.ethics_analyzer.explain_decision(
                decision_type,
                {
                    "message": ai_message,
                    "has_due_date": "截止" in ai_message or "明天" in ai_message,
                    "has_importance": "重要" in ai_message or "紧急" in ai_message
                }
            )
            
            # 格式化显示
            warning_text = AIEthicsWidget.format_limitation_warning(explanation)
            
            # 显示对话框
            QMessageBox.information(self, "⚠️ AI 局限性说明", warning_text)
    
    def _on_suggestion_adopted(self, adopted: bool, adopt_btn=None, reject_btn=None):
        """
        处理建议采纳/忽略
        
        Args:
            adopted: True 表示采纳，False 表示忽略
            adopt_btn: 采纳按钮（用于禁用）
            reject_btn: 忽略按钮（用于禁用）
        """
        # 禁用按钮，防止重复点击
        if adopt_btn:
            adopt_btn.setEnabled(False)
        if reject_btn:
            reject_btn.setEnabled(False)

        # 显示简短提示（不弹窗，只在状态栏显示）
        if adopted:
            self.statusBar().showMessage("✅ 已记录采纳建议", 3000)
        else:
            self.statusBar().showMessage("❌ 已记录忽略建议", 3000)
    
    def _detect_decision_type(self, message: str) -> str:
        """检测 AI 决策类型"""
        if "优先级" in message or "先做" in message or "优先" in message:
            return "priority_adjustment"
        elif "分解" in message or "步骤" in message:
            return "task_decomposition"
        elif "分钟" in message or "小时" in message or "时间" in message:
            return "time_estimation"
        elif "计划" in message or "安排" in message:
            return "study_plan"
        else:
            return "priority_adjustment"  # 默认

    def _add_ai_streaming_message(self):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()

        bubble = QFrame(container)
        bubble.setObjectName("streamingBubble")
        bubble.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                padding: 10px 15px;
                border: 1px solid #E8E8E8;
            }
        """)

        self._ai_streaming_label = QLabel("")
        self._ai_streaming_label.setWordWrap(True)
        self._ai_streaming_label.setStyleSheet("color: #333; font-size: 14px;")
        self._ai_streaming_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ai_streaming_label)

        container_layout.addWidget(bubble)

        self.chat_container_layout.insertWidget(
            self.chat_container_layout.count() - 1,
            container
        )
        self._ai_streaming_container = container
        self._scroll_to_bottom()
        return container

    def _update_streaming_message(self, text):
        if hasattr(self, '_ai_streaming_label') and self._ai_streaming_label:
            self._ai_streaming_label.setText(text)
            self._scroll_to_bottom()

    def _finish_streaming_message(self):
        if hasattr(self, '_ai_streaming_container') and self._ai_streaming_container:
            self._ai_streaming_container.hide()
            self._ai_streaming_container.deleteLater()
            self._ai_streaming_container = None
        if hasattr(self, '_ai_streaming_label'):
            self._ai_streaming_label = None

    def _scroll_to_bottom(self):
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _get_context_prompt(self, include_memory=True):
        config = self.config_manager.load_config()
        base_prompt = config.get("system_prompt", "你是一个友好的 AI 助手。")

        # 获取当前日期和时间
        from datetime import datetime
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_names[now.weekday()]

        pending_tasks = [t for t in self.task_manager.tasks if not t.completed]
        completed_today = self.task_manager.get_today_completed()

        context_parts = []
        # 添加当前时间信息
        context_parts.append(f"【当前时间】{current_date} {weekday} {current_time}")

        # 添加历史记忆 — 仅在 include_memory=True 时注入
        if include_memory and hasattr(self, 'memory_manager') and self.memory_manager:
            recent_message = self.conversation_history[-1]["content"] if self.conversation_history else ""
            memory_context = self.memory_manager.get_context_for_chat(recent_message, max_memories=3)
            if memory_context:
                # 明确告诉AI这是它的记忆
                context_parts.append(f"你有长期记忆功能，以下是相关的历史记忆，请根据这些记忆来回答用户问题：\n{memory_context}")

        if pending_tasks:
            tasks_text = "\n".join([f"- {t.name} (预计{t.estimated_minutes}分钟)" for t in pending_tasks[:5]])
            context_parts.append(f"【未完成任务】\n{tasks_text}")
        if completed_today:
            completed_text = "\n".join([f"- {t.name}" for t in completed_today])
            context_parts.append(f"【今日已完成】\n{completed_text}")

        if context_parts:
            context_text = "\n\n" + "\n\n".join(context_parts)
            return base_prompt + context_text
        return base_prompt

    def send_chat_message(self):
        message = self.chat_input.text().strip()
        if not message:
            return

        if hasattr(self, '_api_call_thread') and self._api_call_thread and self._api_call_thread.isRunning():
            return

        self._set_ai_inputs_enabled(False)
        self._add_user_message(message)
        self.chat_input.clear()

        self._add_ai_streaming_message()

        self._add_to_history("user", message)
        
        # 添加用户消息到记忆（确保 memory_manager 已初始化）
        if hasattr(self, 'memory_manager') and self.memory_manager:
            self.memory_manager.add_memory(
                content=message,
                memory_type="auto",
                context={"source": "user_message"}
            )
        
        # 意图判断使用简洁的系统提示，不包含记忆和上下文
        system_prompt = "你是一个意图识别助手。请根据用户的输入判断意图类型，只返回JSON格式的结果。"

        self._pending_goal = message
        self._send_intent_check(message, system_prompt)
        return
    
    def _send_intent_check(self, goal, system_prompt):
        """意图判断（恢复原有逻辑）"""
        # 获取当前日期和时间
        from datetime import datetime
        import json
        
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_names[now.weekday()]
        
        # 获取当前任务列表
        pending_tasks = [t for t in self.task_manager.tasks if not t.completed]
        tasks_info = "\n".join([
            f"{i+1}. {t.name} (预计{t.estimated_minutes}分钟{f', 截止:{t.due_date}' if t.due_date else ''})"
            for i, t in enumerate(pending_tasks[:10])
        ])
        
        # 获取最近的对话历史（用于上下文判断）
        recent_history = ""
        if self.conversation_history:
            recent_messages = self.conversation_history[-4:]  # 最近4条消息
            for msg in recent_messages:
                role = "用户" if msg["role"] == "user" else "AI"
                content = msg["content"][:200]  # 截取前200字符
                recent_history += f"{role}: {content}\n"
        
        check_prompt = f"""用户说：「{goal}」

当前时间：{current_date} {weekday} {current_time}

当前任务列表：
{tasks_info if tasks_info else "暂无任务"}

最近对话历史：
{recent_history if recent_history else "无历史对话"}

请判断用户的意图，并严格按照以下JSON格式回复（不要添加任何解释）：

{{
  "intent": "意图类型"
}}

意图类型（intent）必须是以下之一：
1. "可以拆解" - 用户描述了一个**目标/任务/计划**，希望拆解成多个具体子任务。关键词：规划、安排、分解、拆解、准备、完成。通常句式是"我要/我想/帮我...".
2. "普通对话" - 用户在提问、聊天、咨询建议、询问时间、打招呼、表达感受等。注意：用户如果只是说"好的"、"可以"、"行"等简单确认词而没有明确任务方向，也归为此类。
3. "创建单个任务" - 用户想添加一个**简单的待办事项**，通常句式是"添加/记下/记录...任务"或直接说一个具体事项（如"买牛奶"、"给妈妈打电话"）。
4. "设定计时提醒" - 用户想要设定计时器、番茄钟、倒计时提醒、定时任务。
5. "创建提醒" - 用户想要创建一个定时提醒，关键词：提醒、闹钟、定时、几点。例如"提醒我明天8点开会"、"设置一个下午3点的提醒"。

**重要判断规则：**
- **上下文关联**：结合"最近对话历史"判断。如果AI刚刚问"是否需要设定计时"，用户回复"好的"，应判断为"设定计时提醒"
- **简洁回复处理**：当用户只回复"是的"、"好的"、"可以"、"行"、"需要"等简短确认词时，优先参考最近一条AI消息的内容来判断意图
- **否定回复**：用户说"不用"、"不需要"、"算了"等否定词，应判断为"普通对话"
- **模糊输入**：如果用户只说一个名词（如"跑步"、"学习"），优先判断为"创建单个任务"
- 如果用户说"设定计时"、"开始番茄钟"、"帮我计时"、"开始计时"等，应判断为"设定计时提醒"
- 如果用户只是确认时间规划但没有明确要求计时，判断为"普通对话"
- 如果用户明确说要"提醒"某事，判断为"创建提醒"
- **"我要..."表达**：用户说"我要考试"、"我要准备面试"、"我要复习"等，表示有一个目标，应判断为"可以拆解"
- **事件陈述**：用户说"我明天要考试"、"下周有面试"等，表示有一个重要事件，应判断为"可以拆解"（可以帮用户准备）

场景示例：
- 用户说"我要期中考试了" → "可以拆解"（用户有一个考试目标，需要准备）
- 用户说"准备明天的面试" → "可以拆解"（目标是准备面试，需要拆解）
- 用户说"我要复习英语" → "可以拆解"（用户有一个学习目标）
- 用户说"下周要交报告" → "可以拆解"（有一个任务目标，可以拆解步骤）
- 用户说"帮我查一下天气" → "普通对话"（只是查询信息）
- 用户说"记一下明天买牛奶" → "创建单个任务"（简单待办）
- 用户说"提醒我明天8点开会" → "创建提醒"（明确要提醒）
- 用户说"好的" + AI最近问"需要设定番茄钟吗" → "设定计时提醒"（上下文确认）
- 用户说"不用了谢谢" → "普通对话"（否定）

请严格按照JSON格式回复，不要添加任何其他内容。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": check_prompt}
        ]

        self._streaming_text = ""

        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message(self._streaming_text)
            except Exception as e:
                print(f"[_send_intent_check on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    # 注意：意图判断结果不保存到历史，避免上下文混乱

                    # 尝试解析JSON格式的响应
                    try:
                        import json
                        # 移除可能的markdown代码块标记
                        json_str = final_content.strip()
                        if json_str.startswith("```"):
                            json_str = json_str.split("\n", 1)[1] if "\n" in json_str else json_str
                        if json_str.endswith("```"):
                            json_str = json_str.rsplit("\n", 1)[0] if "\n" in json_str else json_str
                        json_str = json_str.strip()

                        response_data = json.loads(json_str)
                        intent = response_data.get("intent", "普通对话")

                        if intent == "可以拆解":
                            # 先询问用户是否要拆解
                            self._ask_to_create_tasks(goal, "拆解")
                        elif intent == "创建单个任务":
                            # 先询问用户是否要创建单个任务
                            self._ask_to_create_tasks(goal, "单个")
                        elif intent == "设定计时提醒":
                            # 设定计时提醒，自动启动番茄钟
                            self._handle_timer_intent(goal)
                        elif intent == "创建提醒":
                            # 创建提醒
                            self._create_reminder_from_intent(goal)
                        else:
                            # 普通对话，需要再次调用AI获取真正回复
                            self._do_normal_chat(goal)
                            return  # 不在这里设置enabled，让_do_normal_chat处理

                    except (json.JSONDecodeError, KeyError) as e:
                        # JSON解析失败，使用旧的字符串匹配方式
                        print(f"JSON解析失败: {e}, 使用字符串匹配")
                        if "可以拆解" in final_content:
                            # 先询问用户是否要拆解
                            self._ask_to_create_tasks(goal, "拆解")
                        elif "创建单个任务" in final_content:
                            # 先询问用户是否要创建单个任务
                            self._ask_to_create_tasks(goal, "单个")
                        elif "设定计时提醒" in final_content:
                            # 设定计时提醒
                            self._handle_timer_intent(goal)
                        elif "创建提醒" in final_content:
                            # 创建提醒
                            self._create_reminder_from_intent(goal)
                        else:
                            # 普通对话，需要再次调用AI获取真正回复
                            self._do_normal_chat(goal)
                            return  # 不在这里设置enabled，让_do_normal_chat处理
                else:
                    self._add_ai_message("抱歉，我没理解你的意思，请再说一次。")
            except Exception as e:
                print(f"[_send_intent_check on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_send_intent_check on_error] {e}")
            self._set_ai_inputs_enabled(True)

        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _create_single_task_from_intent(self, user_input):
        """从用户输入中提取单个任务信息并创建（使用AI智能提取）"""
        from datetime import datetime
        import json
        
        self._add_user_message(f"好的，帮我把「{user_input}」加入任务")
        self._set_ai_inputs_enabled(False)
        self._add_ai_streaming_message()

        # 使用简洁的系统提示，不包含任何历史记忆
        system_prompt = "你是一个专业的效率助手。请专注于用户当前的任务，不要参考之前的历史对话。"
        
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        # 获取所有可用标签
        all_tags = self.tag_manager.get_all_tags()
        preset_tags = self.tag_manager.get_preset_tags()
        
        # 构建标签说明
        tag_descriptions = """
可用标签分类：
- 任务类型：学习、工作、生活、娱乐、运动、阅读、编程
- 优先级：紧急、重要、日常、可选
- 时间：今日、本周、长期
- 状态：进行中、待开始、暂停
"""
        
        user_prompt = f"""请从用户的输入中提取任务信息。

当前日期：{current_date}，当前时间：{current_time}

用户输入：{user_input}

{tag_descriptions}

请严格按照以下JSON格式返回（不要添加任何解释）：
{{
  "task_name": "任务名称",
  "estimated_minutes": 预估分钟数,
  "due_date": "截止时间（YYYY-MM-DD HH:MM格式）或null",
  "tags": ["标签1", "标签2"]
}}

要求：
1. task_name: 提取核心任务名称，去掉"帮我"、"将"、"加入任务"等无关词汇
2. estimated_minutes: 根据任务性质合理预估时间（15-120分钟）
3. due_date: 
   - 如果用户指定了日期/时间，转换为YYYY-MM-DD HH:MM格式
   - 如果用户只说了日期没说时间，默认设为当天18:00
   - 如果没有指定截止时间，设为null
4. tags: 根据任务内容智能选择1-3个合适的标签，从可用标签中选择
   - 例如"写代码"可选"编程"、"工作"
   - 例如"跑步"可选"运动"、"生活"
   - 例如"复习考试"可选"学习"、"重要"
   - 如果任务很紧急，添加"紧急"标签
   - 如果是今天要做的，添加"今日"标签

示例：
用户输入："将拉屎在2026/4/27加入任务"
返回：{{"task_name": "拉屎", "estimated_minutes": 15, "due_date": "2026-04-27 18:00", "tags": ["生活", "日常"]}}

用户输入："明天下午3点开会"
返回：{{"task_name": "开会", "estimated_minutes": 60, "due_date": "明天日期 15:00", "tags": ["工作", "重要"]}}

只输出JSON，不要其他内容。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        self._streaming_text = ""
        
        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message("正在提取任务信息...\n" + self._streaming_text)
            except Exception as e:
                print(f"[_create_single_task_from_intent on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    try:
                        # 解析JSON
                        json_str = final_content.strip()
                        if json_str.startswith("```"):
                            lines = json_str.split("\n")
                            json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

                        task_data = json.loads(json_str)
                        task_name = task_data.get("task_name", "").strip()
                        estimated_minutes = max(5, min(180, int(task_data.get("estimated_minutes", 30))))
                        due_date = task_data.get("due_date")
                        tags = task_data.get("tags", [])

                        # 过滤有效标签
                        valid_tags = [t for t in tags if t in all_tags]

                        if due_date and due_date != "null":
                            due_str = due_date
                        else:
                            due_str = None

                        if task_name:
                            # 创建任务（带标签）
                            self.task_manager.add_task(task_name, estimated_minutes, source="ai", due_date=due_str, tags=valid_tags)
                            self.refresh_tasks()

                            due_info = f"，截止时间：{due_str}" if due_str else ""
                            tags_info = f"，标签：{', '.join(['#'+t for t in valid_tags])}" if valid_tags else ""
                            self._add_ai_message(f"✅ 已创建任务：「{task_name}」({estimated_minutes}分钟{due_info}{tags_info})")

                            # 添加任务创建记忆（确保 memory_manager 已初始化）
                            if hasattr(self, 'memory_manager') and self.memory_manager:
                                self.memory_manager.add_memory(
                                    content=f"创建任务：「{task_name}」{due_info}",
                                    memory_type="short_term",
                                    tags=["task_creation"],
                                    context={"source": "single_task", "task_name": task_name}
                                )
                        else:
                            self._add_ai_message("<font color='red'>未能识别任务名称，请重新描述</font>")

                    except json.JSONDecodeError as e:
                        self._add_ai_message(f"<font color='red'>JSON解析失败: {e}</font>\n原始响应：{final_content[:200]}")
                    except Exception as e:
                        self._add_ai_message(f"<font color='red'>创建任务失败: {e}</font>")
                else:
                    self._add_ai_message("<font color='red'>抱歉，未能提取任务信息</font>")
            except Exception as e:
                print(f"[_create_single_task_from_intent on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_create_single_task_from_intent on_error] {e}")
            self._set_ai_inputs_enabled(True)
        
        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _create_reminder_from_intent(self, user_input):
        """从用户输入中提取提醒信息并创建（使用AI智能提取）"""
        from datetime import datetime, timedelta
        import json

        self._add_user_message(f"好的，帮我创建提醒「{user_input}」")
        self._set_ai_inputs_enabled(False)
        self._add_ai_streaming_message()

        # 使用简洁的系统提示，不包含任何历史记忆
        system_prompt = "你是一个专业的效率助手。请专注于用户当前的提醒请求，不要参考之前的历史对话。"

        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_names[now.weekday()]

        user_prompt = f"""请从用户的输入中提取提醒信息。

当前日期：{current_date}，{weekday}，当前时间：{current_time}

用户输入：{user_input}

请严格按照以下JSON格式返回（不要添加任何解释）：
{{
  "title": "提醒标题",
  "remind_time": "提醒时间（YYYY-MM-DD HH:MM格式）",
  "description": "提醒描述（可选，没有则为空字符串）",
  "repeat_type": "重复类型"
}}

要求：
1. title: 提取提醒的核心标题，简洁明了（如"开会"、"吃药"、"运动"）
2. remind_time: 提醒时间
   - 如果用户指定了具体日期和时间，直接转换为 YYYY-MM-DD HH:MM 格式
   - 如果用户说"明天"，则设为明天的日期
   - 如果用户说"后天"，则设为后天的日期
   - 如果用户只说了时间没说日期（如"8点"），默认设为今天
   - 如果用户说的时间已经过了今天，自动设为明天
   - 如果没有指定具体时间，默认设为上午9:00
3. description: 提醒的详细描述（如果有额外信息）
4. repeat_type: 重复类型，必须是以下之一：
   - "none" - 不重复（默认）
   - "daily" - 每天重复
   - "weekly" - 每周重复
   - "monthly" - 每月重复

示例：
用户输入："提醒我明天8点开会"
返回：{{"title": "开会", "remind_time": "2026-04-30 08:00", "description": "", "repeat_type": "none"}}

用户输入："每天早上7点提醒我吃药"
返回：{{"title": "吃药", "remind_time": "2026-04-29 07:00", "description": "每天按时吃药", "repeat_type": "daily"}}

用户输入："后天下午3点提醒我参加面试"
返回：{{"title": "参加面试", "remind_time": "2026-05-01 15:00", "description": "面试", "repeat_type": "none"}}

只输出JSON，不要其他解释。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        self._streaming_text = ""

        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message(self._streaming_text)
            except Exception as e:
                print(f"[_create_reminder_from_intent on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    try:
                        # 移除可能的markdown代码块标记
                        json_str = final_content.strip()
                        if json_str.startswith("```"):
                            lines = json_str.split("\n")
                            json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
                        json_str = json_str.strip()

                        data = json.loads(json_str)
                        title = data.get("title", "提醒")
                        remind_time_str = data.get("remind_time", "")
                        description = data.get("description", "")
                        repeat_type = data.get("repeat_type", "none")

                        # 解析提醒时间
                        try:
                            remind_time = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M")
                        except:
                            # 解析失败，默认1小时后
                            remind_time = now + timedelta(hours=1)

                        # 创建提醒
                        self.reminder_manager.add_reminder(title, remind_time, description, repeat_type)

                        # 刷新提醒列表
                        if hasattr(self, 'reminder_tab'):
                            self.reminder_tab.refresh_reminders()

                        # 格式化时间显示
                        time_str = remind_time.strftime("%Y-%m-%d %H:%M")
                        repeat_text = {
                            "none": "",
                            "daily": "（每天重复）",
                            "weekly": "（每周重复）",
                            "monthly": "（每月重复）"
                        }.get(repeat_type, "")

                        self._add_to_history("assistant", f"已创建提醒「{title}」")
                        self._add_ai_message(
                            f"<font color='green'><b>✅ 提醒创建成功！</b></font>\n\n"
                            f"⏰ <b>{title}</b>\n"
                            f"📅 {time_str} {repeat_text}\n"
                            f"{f'📝 {description}' if description else ''}"
                        )

                    except json.JSONDecodeError as e:
                        self._add_ai_message(f"<font color='red'>JSON解析失败: {e}</font>\n原始响应：{final_content[:200]}")
                    except Exception as e:
                        self._add_ai_message(f"<font color='red'>创建提醒失败: {e}</font>")
                else:
                    self._add_ai_message("<font color='red'>抱歉，未能提取提醒信息</font>")
            except Exception as e:
                print(f"[_create_reminder_from_intent on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_create_reminder_from_intent on_error] {e}")
            self._set_ai_inputs_enabled(True)

        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _handle_timer_intent(self, user_input):
        """处理设定计时提醒的意图"""
        import re
        from datetime import datetime
        
        # 获取未完成任务
        pending_tasks = [t for t in self.task_manager.tasks if not t.completed]
        
        # 尝试从用户输入中提取时间（分钟）
        time_match = re.search(r'(\d+)\s*(分钟|小时|h|hour)', user_input)
        if time_match:
            time_value = int(time_match.group(1))
            unit = time_match.group(2)
            if unit in ['小时', 'h', 'hour']:
                time_value *= 60
        else:
            # 默认25分钟（番茄钟标准时长）
            time_value = 25
        
        # 尝试匹配任务名称
        matched_task = None
        for task in pending_tasks:
            # 简单匹配：检查任务名是否在用户输入中
            if task.name in user_input:
                matched_task = task
                break
        
        # 如果用户只是确认（如"好的"、"可以"、"行"），自动选择第一个任务
        confirmation_words = ["好的", "可以", "行", "是的", "需要", "嗯", "好", "ok", "OK", "Ok"]
        is_confirmation = any(word in user_input for word in confirmation_words) and len(user_input.strip()) <= 10
        
        if matched_task:
            # 找到匹配的任务，使用任务的时间
            task_name = matched_task.name
            task_minutes = matched_task.estimated_minutes
            self._add_ai_message(f"好的，我来帮你启动「{task_name}」的番茄钟计时（{task_minutes}分钟）⏰\n\n专注模式已开启，加油！💪")
            # 启动番茄钟
            dialog = PomodoroDialog(task_minutes, task_name, self)
            dialog.finished.connect(lambda duration, name: self.on_pomodoro_finished(matched_task, duration))
            dialog.exec_()
        elif is_confirmation and pending_tasks:
            # 用户确认，自动选择第一个任务
            first_task = pending_tasks[0]
            self._add_ai_message(f"好的，我来帮你启动「{first_task.name}」的番茄钟计时（{first_task.estimated_minutes}分钟）⏰\n\n专注模式已开启，加油！💪")
            dialog = PomodoroDialog(first_task.estimated_minutes, first_task.name, self)
            dialog.finished.connect(lambda duration, name: self.on_pomodoro_finished(first_task, duration))
            dialog.exec_()
        elif pending_tasks:
            # 没有匹配到任务，自动选择第一个任务
            first_task = pending_tasks[0]
            self._add_ai_message(f"好的，我来帮你启动「{first_task.name}」的番茄钟计时（{first_task.estimated_minutes}分钟）⏰\n\n专注模式已开启，加油！💪")
            dialog = PomodoroDialog(first_task.estimated_minutes, first_task.name, self)
            dialog.finished.connect(lambda duration, name: self.on_pomodoro_finished(first_task, duration))
            dialog.exec_()
        else:
            # 没有任务，启动默认计时器
            self._add_ai_message(f"好的，我来帮你启动一个 {time_value} 分钟的计时器 ⏰\n\n专注模式已开启，加油！💪")
            dialog = PomodoroDialog(time_value, "专注时间", self)
            dialog.exec_()
        
        self._set_ai_inputs_enabled(True)

    def _do_normal_chat(self, message):
        self._add_ai_streaming_message()

        system_prompt = self._get_context_prompt()

        messages = [{"role": "system", "content": system_prompt}]
        # 使用最近的历史（不包括当前消息，因为当前消息已经在历史中了）
        for h in self.conversation_history[-8:]:
            messages.append({"role": h["role"], "content": h["content"]})

        self._streaming_text = ""

        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message(self._streaming_text)
            except Exception as e:
                print(f"[_do_normal_chat on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    self._add_to_history("assistant", final_content)
                    rendered = render_latex(final_content)
                    self._add_ai_message(rendered)

                    # 添加AI回复到记忆（确保 memory_manager 已初始化）
                    if hasattr(self, 'memory_manager') and self.memory_manager:
                        self.memory_manager.add_memory(
                            content=final_content,
                            memory_type="auto",
                            tags=["ai_response"],
                            context={"source": "ai_message"}
                        )
            except Exception as e:
                print(f"[_do_normal_chat on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_do_normal_chat on_error] {e}")
            self._set_ai_inputs_enabled(True)

        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _ask_to_create_tasks(self, goal, task_type="拆解"):
        """
        询问用户是否要创建任务
        
        Args:
            goal: 目标内容
            task_type: 任务类型（"拆解" 或 "单个"）
        """
        # 创建确认按钮
        btn = QPushButton("✅ 确认创建")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        if task_type == "拆解":
            btn.clicked.connect(lambda: self._create_tasks_from_goal(goal))
            label_text = f"🤖 AI 建议将「{goal}」拆解成多个任务，是否创建？"
        else:
            btn.clicked.connect(lambda: self._create_single_task_from_intent(goal))
            label_text = f"🤖 AI 建议创建任务「{goal}」，是否创建？"
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #666; font-size: 13px;")
        label.setWordWrap(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(label)
        layout.addWidget(btn)
        
        self._add_ai_message("", with_action_button=container)
    
    def _show_create_tasks_button(self, goal):
        btn = QPushButton("🤖 创建任务")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn.clicked.connect(lambda: self._create_tasks_from_goal(goal))

        label = QLabel("这是一个目标，要拆解成任务吗？")
        label.setStyleSheet("color: #666; font-size: 13px;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(label)
        layout.addWidget(btn)

        self._add_ai_message("", with_action_button=container)

    def _create_tasks_from_goal(self, goal):
        self._add_user_message(f"好的，帮我把「{goal}」拆解成任务")
        self._set_ai_inputs_enabled(False)

        self._add_ai_streaming_message()

        # 使用简洁的系统提示，不包含任何历史记忆
        system_prompt = "你是一个专业的效率助手。请专注于用户当前的目标，不要参考之前的历史对话。"

        # 获取当前日期和时间
        from datetime import datetime
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        # 获取所有可用标签
        all_tags = self.tag_manager.get_all_tags()
        
        # 构建标签说明
        tag_descriptions = """
可用标签分类：
- 任务类型：学习、工作、生活、娱乐、运动、阅读、编程
- 优先级：紧急、重要、日常、可选
- 时间：今日、本周、长期
- 状态：进行中、待开始、暂停
"""

        user_prompt = f"""请将以下目标拆解成 3~6 个具体的子任务。

当前日期：{current_date}，当前时间：{current_time}

{tag_descriptions}

返回格式必须是严格的 JSON 数组：
[{{"name": "任务名称", "estimated_minutes": 预估分钟数, "due_date": "截止时间或null", "tags": ["标签1", "标签2"]}}]

要求：
1. name: 任务名称要具体可执行，不要笼统
2. estimated_minutes: 根据任务难度合理预估时间（15-120分钟）
   - 简单任务（如整理笔记）：15-30分钟
   - 中等任务（如做题、阅读）：30-60分钟
   - 复杂任务（如写报告、复习章节）：60-120分钟
3. due_date: 截止时间（格式：YYYY-MM-DD HH:MM）
   - 如果用户指定了截止时间，按用户要求设置
   - 否则，合理分配到未来几天，从今天开始安排
   - 每个任务的截止时间要错开，避免堆积
4. tags: 根据任务内容智能选择1-2个合适的标签，从可用标签中选择
   - 例如"写代码"可选"编程"、"工作"
   - 例如"跑步"可选"运动"、"生活"
   - 例如"复习考试"可选"学习"、"重要"

目标：{goal}

只输出 JSON 数组，不要其他解释。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        self._streaming_text = ""
        self._goal_for_tasks = goal

        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message("正在分析目标...\n" + self._streaming_text)
            except Exception as e:
                print(f"[_create_tasks_from_goal on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    self._parse_and_create_tasks(final_content, goal)
                else:
                    self._add_ai_message("<font color='red'>抱歉，未能解析任务列表</font>")
            except Exception as e:
                print(f"[_create_tasks_from_goal on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_create_tasks_from_goal on_error] {e}")
            self._set_ai_inputs_enabled(True)

        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _parse_and_create_tasks(self, json_str, goal):
        try:
            json_str = json_str.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            tasks = json.loads(json_str)
            if not isinstance(tasks, list):
                raise ValueError("返回格式不是数组")

            # 获取所有有效标签（预设+自定义）
            all_tags = self.tag_manager.get_all_tags()
            preset_tags = self.tag_manager.get_preset_tags()

            added_count = 0
            task_info_list = []
            total_minutes = 0
            has_due_date = False
            first_due_date = None
            first_task_name = ""
            for task_data in tasks:
                name = task_data.get("name", "").strip()
                minutes = max(5, min(180, int(task_data.get("estimated_minutes", 30))))
                total_minutes += minutes
                due_date = task_data.get("due_date")
                if due_date and (due_date == "null" or due_date is None):
                    due_date = None

                # 记录第一个有截止时间的任务信息
                if due_date and not has_due_date:
                    has_due_date = True
                    first_due_date = due_date
                    first_task_name = name

                # 获取标签并过滤有效标签
                tags = task_data.get("tags", [])
                valid_tags = []
                for t in tags:
                    # 精确匹配
                    if t in all_tags:
                        valid_tags.append(t)
                    # 尝试去除空格后匹配
                    elif t.strip() in all_tags:
                        valid_tags.append(t.strip())
                    # 如果不在预设标签中，自动添加为自定义标签
                    elif t.strip():
                        self.tag_manager.add_custom_tag(t.strip())
                        valid_tags.append(t.strip())

                if name:
                    self.task_manager.add_task(name, minutes, source="ai", due_date=due_date, tags=valid_tags)
                    added_count += 1
                    due_info = f" 📅 {due_date}" if due_date else ""
                    tags_info = f" 🏷️ {', '.join(['#'+t for t in valid_tags])}" if valid_tags else ""
                    task_info_list.append(f"• {name} ⏱ {minutes}分钟{due_info}{tags_info}")

            self.refresh_tasks()
            if hasattr(self, 'stats_tab'):
                self.stats_tab.refresh_stats()

            total_hours = total_minutes // 60
            remain_mins = total_minutes % 60
            time_str = f"{total_hours}小时{remain_mins}分钟" if total_hours > 0 else f"{total_minutes}分钟"

            self._add_to_history("assistant", f"已将「{goal}」拆解为 {added_count} 个任务")

            # 如果有截止时间，显示创建提醒按钮
            if has_due_date and first_due_date:
                self._show_tasks_with_reminder_option(goal, added_count, time_str, task_info_list, first_task_name, first_due_date)
            else:
                self._add_ai_message(
                    f"<font color='green'><b>✅ 成功!</b></font> 已创建 {added_count} 个任务，预计总时长 {time_str}：\n\n" +
                    "\n".join(task_info_list)
                )

            # 添加任务创建记忆（确保 memory_manager 已初始化）
            if hasattr(self, 'memory_manager') and self.memory_manager:
                self.memory_manager.add_memory(
                    content=f"目标「{goal}」已拆解为{added_count}个任务，预计总时长{time_str}",
                    memory_type="long_term",
                    tags=["task_creation", "goal_decomposition"],
                    context={"source": "task_creation", "task_count": added_count}
                )

        except json.JSONDecodeError as e:
            self._add_ai_message(f"<font color='red'><b>❌ JSON解析失败:</b> {e}</font>\n原始响应：{json_str[:200]}")
        except Exception as e:
            self._add_ai_message(f"<font color='red'><b>❌ 处理失败:</b> {e}</font>")

    def _show_tasks_with_reminder_option(self, goal, task_count, time_str, task_info_list, task_name, due_date):
        """显示任务创建结果，并提供创建提醒的选项"""
        # 创建容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(10)

        # 任务信息
        info_label = QLabel(
            f"<font color='green'><b>✅ 成功!</b></font> 已创建 {task_count} 个任务，预计总时长 {time_str}：\n\n" +
            "\n".join(task_info_list)
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.PlainText)
        layout.addWidget(info_label)

        # 提醒询问
        ask_label = QLabel(f"\n💡 任务「{task_name}」有截止时间，需要创建提醒吗？")
        ask_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(ask_label)

        # 按钮行
        btn_layout = QHBoxLayout()

        # 创建提醒按钮
        create_btn = QPushButton("⏰ 创建提醒")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
        """)
        create_btn.clicked.connect(lambda: self._quick_create_reminder(task_name, due_date))
        btn_layout.addWidget(create_btn)

        # 稍后按钮
        later_btn = QPushButton("暂不需要")
        later_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #666;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #BDBDBD;
            }
        """)
        btn_layout.addWidget(later_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._add_ai_message("", with_action_button=container)

    def _quick_create_reminder(self, task_name, due_date):
        """快速创建提醒（从任务截止时间）"""
        from datetime import datetime

        try:
            # 解析截止时间
            if isinstance(due_date, str):
                remind_time = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            else:
                remind_time = due_date

            # 创建提醒
            self.reminder_manager.add_reminder(
                title=f"任务提醒：{task_name}",
                remind_time=remind_time,
                description=f"任务「{task_name}」即将到期，请及时完成！"
            )

            # 刷新提醒列表
            if hasattr(self, 'reminder_tab'):
                self.reminder_tab.refresh_reminders()

            time_str = remind_time.strftime("%Y-%m-%d %H:%M")
            self._add_ai_message(
                f"<font color='green'><b>✅ 提醒已创建！</b></font>\n\n"
                f"⏰ 任务「{task_name}」\n"
                f"📅 提醒时间：{time_str}"
            )
        except Exception as e:
            self._add_ai_message(f"<font color='red'>创建提醒失败: {e}</font>")

    def _add_to_history(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        # 保留最近 10 条对话历史，确保上下文连贯
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def _on_ai_result(self, result, chat_output):
        if chat_output:
            rendered = render_latex(result)
            chat_output.append(f"<b>AI:</b> {rendered}")

    def _on_ai_error(self, error_msg, chat_output):
        if chat_output:
            chat_output.append(f"<font color='red'><b>AI:</b> 错误: {error_msg}</font>")

    def _set_ai_inputs_enabled(self, enabled):
        if hasattr(self, 'send_btn'):
            self.send_btn.setEnabled(enabled)
        if hasattr(self, 'chat_input'):
            self.chat_input.setEnabled(enabled)
        if hasattr(self, 'voice_btn'):
            self.voice_btn.setEnabled(enabled)

    def ai_breakdown(self):
        self.tab_widget.setCurrentIndex(0)
        self._add_ai_message("💡 请在下方输入您的目标，例如：「准备数学考试」或「完成项目报告」，我会帮您拆解成具体任务。")

    def generate_summary(self):
        self.tab_widget.setCurrentIndex(0)
        today_tasks = self.task_manager.get_today_tasks()
        completed_tasks = self.task_manager.get_today_completed()

        if not today_tasks:
            self._add_ai_message("📭 今天还没有任务记录，添加一些任务后再来生成总结吧！")
            return

        message = f"📊 今日进度：已完成 {len(completed_tasks)}/{len(today_tasks)} 个任务\n\n"
        message += "✅ 已完成任务：\n"
        for t in completed_tasks:
            message += f"  • {t.name}\n"

        pending = [t for t in today_tasks if not t.completed]
        if pending:
            message += "\n⏳ 未完成任务：\n"
            for t in pending:
                message += f"  • {t.name}\n"

        self._add_ai_message(message)

    def voice_input(self):
        if hasattr(self, '_voice_thread') and self._voice_thread.isRunning():
            self._voice_thread.stop()
            self._restore_voice_btn()
            return

        try:
            from voice_input import VoiceRecognitionThread, VoiceInputDialog, get_default_model_path
        except ImportError as e:
            self._add_ai_message(f"🎤 导入语音模块失败: {e}")
            return

        model_path = get_default_model_path()
        if not model_path or not os.path.exists(model_path):
            self._add_ai_message("🎤 未找到语音模型文件\n请下载 vosk-model-small-cn-0.22 到 models 目录")
            return

        self.voice_btn.setText("🔴")
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 77, 77, 0.9);
                color: white;
                border: none;
                border-radius: 21px;
                font-size: 20px;
                padding: 0px;
            }
        """)

        self._voice_dialog = VoiceInputDialog(self)
        self._voice_thread = VoiceRecognitionThread(model_path)

        def on_result(text):
            self._restore_voice_btn()
            self._voice_dialog.set_result(text)
            self._voice_dialog.accept()

        def on_error(msg):
            self._restore_voice_btn()
            self._voice_dialog.set_status("错误: " + msg)
            self._add_ai_message(f"<font color='red'>🎤 识别错误: {msg}</font>")

        self._voice_thread.result_ready.connect(on_result)
        self._voice_thread.error_occurred.connect(on_error)

        def on_dialog_accepted():
            self._restore_voice_btn()
            if hasattr(self, '_voice_thread') and self._voice_thread.isRunning():
                self._voice_thread.stop()
            text = self._voice_dialog.recognized_text
            if text:
                self.chat_input.setText(text)

        def on_dialog_rejected():
            self._restore_voice_btn()
            if hasattr(self, '_voice_thread') and self._voice_thread.isRunning():
                self._voice_thread.stop()

        self._voice_dialog.accepted.connect(on_dialog_accepted)
        self._voice_dialog.rejected.connect(on_dialog_rejected)

        from PyQt5.QtCore import QTimer
        self._voice_timeout_timer = QTimer()
        self._voice_timeout_timer.setSingleShot(True)
        self._voice_timeout_timer.timeout.connect(lambda: (self._voice_thread.stop(), self._voice_dialog.reject(), self._restore_voice_btn(), self._add_ai_message("🎤 识别超时")))
        self._voice_timeout_timer.start(30000)

        self._voice_thread.start()
        self._voice_dialog.show()

    def _restore_voice_btn(self):
        if hasattr(self, '_voice_timeout_timer'):
            self._voice_timeout_timer.stop()
        if hasattr(self, 'voice_btn'):
            self.voice_btn.setText("🎤")
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #888;
                    border: none;
                    border-radius: 21px;
                    font-size: 20px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #F0F0F0;
                    color: #FF8FAB;
                }
            """)


def _exception_hook(exc_type, exc_value, exc_tb):
    """全局异常钩子 — 防止 Qt 信号槽中未捕获的异常导致闪退"""
    import traceback
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[FATAL] 未捕获的异常:\n{msg}", file=sys.stderr)
    # 写入日志文件以便事后分析
    log_path = os.path.join(os.getcwd(), "crash.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n===== {datetime.now()} =====\n{msg}\n")
    except Exception:
        pass
    # 尝试弹出错误对话框（GUI 环境）
    try:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "😵 程序遇到错误",
            f"发生了未预期的错误，请将以下信息反馈给开发者：\n\n{exc_value}")
    except Exception:
        pass


if __name__ == "__main__":
    # 记录启动路径信息（调试用）
    try:
        with open("crash.log", "a", encoding="utf-8") as lf:
            lf.write(f"\n===== {datetime.now()} STARTUP =====\n")
            lf.write(f"frozen={getattr(sys, 'frozen', False)}, exec={sys.executable if getattr(sys, 'frozen', False) else 'N/A'}\n")
            from utils import get_data_path
            lf.write(f"tasks.json path: {get_data_path('tasks.json')}\n")
            lf.write(f"tasks.json exists: {os.path.exists(get_data_path('tasks.json'))}\n")
    except Exception:
        pass

    sys.excepthook = _exception_hook
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
