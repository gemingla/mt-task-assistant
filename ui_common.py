"""
主界面各模块共享的导入、常量与工具（由 main.py 拆分而来）
各 UI 模块通过 `from ui_common import *` 获得与原 main.py 相同的命名空间。
"""
import sys
import os
import json
import ctypes
from datetime import datetime, timedelta

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
    QSizePolicy, QMenuBar
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QVariantAnimation, pyqtSignal, QPoint, QMimeData, QTimer, QSize, QThread, QDateTime, QTime
from PyQt5.QtGui import QFont, QColor, QDrag, QPixmap, QIcon
import webbrowser

from config import ConfigManager
from task_manager import TaskManager
from stats_manager import StatsManager
from reminder_manager import ReminderManager, Reminder
from tag_manager import TagManager
from ai_client import get_models, render_latex
# 优化版 AI 客户端
from ai_client_optimized import call_ai_stream_optimized
from pomodoro_widget import PomodoroWidget
from pomodoro_dialog import PomodoroDialog
from stats_chart_widget import BarChartWidget, PieChartWidget
from stats_widget import StatisticsWidget
from utils import get_data_path, log_error, parse_datetime
from version import __version__
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


# 已完成任务在主列表中保留显示的天数
COMPLETED_VISIBLE_DAYS = 3


class BackgroundTask(QThread):
    """在后台线程执行任意函数，避免网络请求卡住界面；结果通过信号回到 UI 线程"""
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, func, *args, parent=None, **kwargs):
        super().__init__(parent)
        self._func, self._args, self._kwargs = func, args, kwargs

    def run(self):
        try:
            self.succeeded.emit(self._func(*self._args, **self._kwargs))
        except Exception as e:
            self.failed.emit(str(e))


class AsyncAPICallStream(QThread):
    chunk_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)
    stream_finished = pyqtSignal(str)

    def __init__(self, messages, parent=None):
        super().__init__(parent)
        self.messages = messages

    def run(self):
        try:
            call_ai_stream_optimized(
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
    apply_combobox_style, apply_textedit_style, set_completed_style,
    GLOBAL_BG_COLOR, THEME_COLOR, HOVER_COLOR, CARD_BG_COLOR, TEXT_COLOR, SUBTEXT_COLOR, COMPLETED_BG_COLOR
)
from theme_adapter import ThemeAdapter
from glass_effects import (
    AuroraBackground, GlassPanel, GlassTabWidget, SlidingPill, LiquidGlassButton, play_strike_through,
    glass_palette, fade_in_window, make_scroll_areas_transparent,
)


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
