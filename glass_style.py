from PyQt5.QtWidgets import QPushButton, QCheckBox, QLineEdit, QWidget, QLabel, QFrame, QDialog, QSpinBox, QComboBox
from PyQt5.QtCore import QTimer, QEasingCurve, QPropertyAnimation, QVariantAnimation, Qt
from PyQt5.QtGui import QColor, QPalette, QFont, QPainter, QLinearGradient, QBrush


# ========================
# 配色系统 — 现代高级版
# ========================
GLOBAL_BG_COLOR = "#F8F9FC"
THEME_COLOR = "#FF6B9D"
THEME_GRADIENT_START = "#FF6B9D"
THEME_GRADIENT_END = "#EC407A"
HOVER_COLOR = "#EC407A"
PRESSED_COLOR = "#D81B60"
CARD_BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#1A1A2E"
SUBTEXT_COLOR = "#6B7280"
COMPLETED_BG_COLOR = "#F1F8E9"
COMPLETED_BORDER_COLOR = "#A5D6A7"

# 新增现代配色
ACCENT_COLOR = "#6366F1"  # 紫罗兰强调色
SUCCESS_COLOR = "#10B981"  # 成功绿
WARNING_COLOR = "#F59E0B"  # 警告橙
DANGER_COLOR = "#EF4444"  # 危险红
INFO_COLOR = "#3B82F6"  # 信息蓝
SURFACE_COLOR = "#FFFFFF"  # 表面色
ELEVATION_COLOR = "rgba(0, 0, 0, 0.04)"  # 阴影色


def _gradient_stylesheet(bg_start, bg_end, hover_end, pressed_end, border_radius, padding, font_size, color, border_alpha=0.3):
    """生成渐变按钮样式"""
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {bg_start},
                stop:1 {bg_end});
            color: {color};
            border: 1px solid rgba(255, 255, 255, {border_alpha});
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {bg_end},
                stop:1 {hover_end});
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {hover_end},
                stop:1 {pressed_end});
        }}
        QPushButton:disabled {{
            background: rgba(200, 200, 200, 0.5);
            color: #BDBDBD;
            border: 1px solid rgba(200, 200, 200, 0.3);
        }}
    """


def apply_glass_style(button: QPushButton,
                      bg_color: str = "rgba(255, 107, 157, 0.85)",
                      hover_color: str = "rgba(236, 64, 122, 0.9)",
                      pressed_color: str = "rgba(216, 27, 96, 0.95)",
                      border_radius: int = 10,
                      padding: str = "8px 18px",
                      font_size: int = 13,
                      color: str = "white"):
    """高级毛玻璃效果 — 主按钮"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: {color};
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
            border: 1px solid rgba(255, 255, 255, 0.4);
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        QPushButton:disabled {{
            background-color: rgba(200, 200, 200, 0.5);
            color: #BDBDBD;
            border: 1px solid rgba(200, 200, 200, 0.3);
        }}
    """)


def apply_glass_style_secondary(button: QPushButton,
                                bg_color: str = "rgba(120, 144, 156, 0.85)",
                                hover_color: str = "rgba(96, 125, 139, 0.9)",
                                pressed_color: str = "rgba(84, 110, 122, 0.95)",
                                border_radius: int = 10,
                                padding: str = "8px 18px",
                                font_size: int = 13,
                                color: str = "white"):
    """高级毛玻璃效果 — 次要按钮"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: {color};
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        QPushButton:disabled {{
            background-color: rgba(200, 200, 200, 0.5);
            color: #BDBDBD;
        }}
    """)


def apply_glass_style_danger(button: QPushButton,
                             bg_color: str = "rgba(239, 83, 80, 0.85)",
                             hover_color: str = "rgba(211, 47, 47, 0.9)",
                             pressed_color: str = "rgba(180, 50, 50, 0.95)",
                             border_radius: int = 10,
                             padding: str = "8px 18px",
                             font_size: int = 13,
                             color: str = "white"):
    """高级毛玻璃效果 — 危险按钮"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: {color};
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
    """)


def apply_glass_style_light(button: QPushButton,
                           bg_color: str = "rgba(255, 107, 157, 0.7)",
                           hover_color: str = "rgba(236, 64, 122, 0.8)",
                           pressed_color: str = "rgba(216, 27, 96, 0.85)",
                           border_radius: int = 10,
                           padding: str = "8px 18px",
                           font_size: int = 13,
                           color: str = "white"):
    """高级毛玻璃效果 — 浅色按钮"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: {color};
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        QPushButton:disabled {{
            background-color: rgba(200, 200, 200, 0.5);
            color: #BDBDBD;
        }}
    """)


def apply_glass_style_icon(button: QPushButton,
                           border_radius: int = 22,
                           size: int = 44,
                           bg_color: str = "rgba(255, 107, 157, 0.85)",
                           hover_color: str = "rgba(236, 64, 122, 0.9)"):
    """高级毛玻璃效果 — 圆形图标按钮"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: {border_radius}px;
            font-size: 18px;
            min-width: {size}px;
            max-width: {size}px;
            min-height: {size}px;
            max-height: {size}px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        QPushButton:pressed {{
            background-color: rgba(216, 27, 96, 0.85);
        }}
    """)


def apply_input_style(line_edit: QLineEdit,
                      border_radius: int = 8,
                      border_color: str = "#E8E8E8",
                      focus_color: str = "#FF6B9D"):
    """高级输入框样式"""
    line_edit.setStyleSheet(f"""
        QLineEdit {{
            background: #FAFAFA;
            border: 1.5px solid {border_color};
            border-radius: {border_radius}px;
            padding: 8px 12px;
            font-size: 13px;
            color: {TEXT_COLOR};
        }}
        QLineEdit:hover {{
            border: 1.5px solid #D0D0D0;
            background: white;
        }}
        QLineEdit:focus {{
            border: 2px solid {focus_color};
            padding: 7px 11px;
            background: white;
        }}
        QLineEdit:disabled {{
            background: #F5F5F5;
            color: {SUBTEXT_COLOR};
            border: 1.5px solid #E8E8E8;
        }}
    """)


def apply_textedit_style(text_edit,
                         border_radius: int = 10,
                         border_color: str = "#E8E8E8",
                         bg_color: str = "#FAFAFA",
                         focus_color: str = "#FF6B9D"):
    """高级文本编辑框样式"""
    text_edit.setStyleSheet(f"""
        QTextEdit {{
            background-color: {bg_color};
            border: 1.5px solid {border_color};
            border-radius: {border_radius}px;
            padding: 10px;
            font-size: 13px;
            color: {TEXT_COLOR};
        }}
        QTextEdit:hover {{
            border: 1.5px solid #D0D0D0;
            background: white;
        }}
        QTextEdit:focus {{
            border: 2px solid {focus_color};
            padding: 9px;
            background: white;
        }}
    """)


def apply_checkbox_style(checkbox: QCheckBox,
                         checked_color: str = "#FF6B9D",
                         unchecked_color: str = "#D0D0D0"):
    """高级复选框样式 — 大号圆角"""
    checkbox.setStyleSheet(f"""
        QCheckBox {{
            spacing: 10px;
            color: {TEXT_COLOR};
            font-size: 13px;
        }}
        QCheckBox::indicator {{
            width: 24px;
            height: 24px;
            border-radius: 7px;
            border: 2px solid {unchecked_color};
            background: white;
        }}
        QCheckBox::indicator:hover {{
            border-color: {checked_color};
            background: #FFF0F5;
        }}
        QCheckBox::indicator:checked {{
            background-color: {checked_color};
            border-color: {checked_color};
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: #EC407A;
            border-color: #EC407A;
        }}
    """)


def apply_card_style(widget: QWidget,
                    bg_color: str = CARD_BG_COLOR,
                    border_color: str = "rgba(0, 0, 0, 0.06)",
                    border_radius: int = 12):
    """高级卡片样式"""
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
        }}
        QWidget:hover {{
            border: 1px solid rgba(255, 107, 157, 0.2);
        }}
    """)


def apply_scrollbar_style():
    """返回优雅滚动条样式字符串"""
    return """
        QScrollBar:vertical {
            width: 8px;
            background: transparent;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background: rgba(180, 180, 200, 0.4);
            border-radius: 4px;
            min-height: 30px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(180, 180, 200, 0.7);
        }
        QScrollBar::handle:vertical:pressed {
            background: #FF6B9D;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar:horizontal {
            height: 8px;
            background: transparent;
            margin: 0;
        }
        QScrollBar::handle:horizontal {
            background: rgba(180, 180, 200, 0.4);
            border-radius: 4px;
            min-width: 30px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal:hover {
            background: rgba(180, 180, 200, 0.7);
        }
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            width: 0;
        }
    """


def apply_tab_style(tab_widget,
                   selected_color: str = THEME_COLOR,
                   bg_color: str = "transparent"):
    """高级标签页样式 — 下划线式"""
    tab_widget.setStyleSheet(f"""
        QTabWidget::pane {{
            border: none;
            background: transparent;
        }}
        QTabBar::tab {{
            background: transparent;
            color: #888;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 500;
            border: none;
            border-bottom: 2px solid transparent;
            margin-right: 4px;
        }}
        QTabBar::tab:hover {{
            color: {selected_color};
            background: rgba(255, 107, 157, 0.06);
            border-radius: 8px 8px 0 0;
        }}
        QTabBar::tab:selected {{
            color: {selected_color};
            border-bottom: 2px solid {selected_color};
            font-weight: 600;
        }}
    """)


def apply_spinbox_style(spinbox,
                       border_color: str = "#E8E8E8",
                       focus_color: str = "#FF6B9D"):
    """高级数字选择框样式"""
    spinbox.setStyleSheet(f"""
        QSpinBox {{
            background: white;
            border: 1.5px solid {border_color};
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 13px;
            color: {TEXT_COLOR};
        }}
        QSpinBox:hover {{
            border: 1.5px solid #D0D0D0;
        }}
        QSpinBox:focus {{
            border: 2px solid {focus_color};
            padding: 5px 9px;
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background: #F5F5F5;
            border-radius: 4px;
            width: 18px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background: rgba(255, 107, 157, 0.12);
        }}
    """)


def apply_combobox_style(combo,
                        border_color: str = "#E8E8E8",
                        focus_color: str = "#FF6B9D"):
    """高级下拉框样式"""
    combo.setStyleSheet(f"""
        QComboBox {{
            background: white;
            border: 1.5px solid {border_color};
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 13px;
            color: {TEXT_COLOR};
            min-width: 120px;
        }}
        QComboBox:hover {{
            border: 1.5px solid rgba(255, 107, 157, 0.4);
        }}
        QComboBox:focus {{
            border: 2px solid {focus_color};
            padding: 7px 13px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 28px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #999;
            margin-right: 8px;
        }}
        QComboBox::down-arrow:hover {{
            border-top: 6px solid {focus_color};
        }}
        QComboBox QAbstractItemView {{
            background: white;
            border: 1px solid #E8E8E8;
            border-radius: 10px;
            padding: 6px;
            selection-background-color: rgba(255, 107, 157, 0.12);
            selection-color: {TEXT_COLOR};
            outline: none;
            font-size: 13px;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            border-radius: 6px;
            min-height: 24px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background: rgba(255, 107, 157, 0.06);
        }}
    """)


# ========================
# 动画系统
# ========================

class FadeAnimation:
    """高级淡入淡出动画"""
    def __init__(self, widget, duration: int = 300):
        self.widget = widget
        self.duration = duration
        self.opacity_effect = None
        self.animation = None

    def fade_in(self, on_finished=None):
        """淡入动画 — OutCubic 缓出"""
        from PyQt5.QtWidgets import QGraphicsOpacityEffect
        self.opacity_effect = QGraphicsOpacityEffect(self.widget)
        self.widget.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(self.duration)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        if on_finished:
            self.animation.finished.connect(on_finished)

        self.animation.start()
        return self.animation

    def fade_out(self, on_finished=None):
        """淡出动画 — InCubic 缓入"""
        if not self.opacity_effect:
            self.opacity_effect = QGraphicsOpacityEffect(self.widget)
            self.widget.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(self.duration)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.InCubic)

        if on_finished:
            self.animation.finished.connect(on_finished)

        self.animation.start()
        return self.animation


def set_completed_style(widget: QWidget, completed: bool):
    """设置任务卡片的完成状态样式 — 绿色高亮"""
    if completed:
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COMPLETED_BG_COLOR};
                border: 1.5px solid {COMPLETED_BORDER_COLOR};
                border-radius: 12px;
            }}
            QWidget:hover {{
                border: 1.5px solid #81C784;
            }}
        """)
    else:
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {CARD_BG_COLOR};
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 12px;
            }}
            QWidget:hover {{
                border: 1px solid rgba(255, 107, 157, 0.25);
            }}
        """)


# ========================
# 新增高级样式函数
# ========================

def apply_shadow_card_style(widget: QWidget,
                            bg_color: str = CARD_BG_COLOR,
                            border_radius: int = 14,
                            shadow_intensity: float = 0.08):
    """高级阴影卡片样式"""
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect
    from PyQt5.QtGui import QColor

    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {bg_color};
            border: 1px solid rgba(0, 0, 0, 0.04);
            border-radius: {border_radius}px;
        }}
        QWidget:hover {{
            border: 1px solid rgba(255, 107, 157, 0.15);
        }}
    """)

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(24)
    shadow.setColor(QColor(0, 0, 0, int(255 * shadow_intensity)))
    shadow.setOffset(0, 4)
    widget.setGraphicsEffect(shadow)
    return shadow


def apply_glow_button_style(button,
                            glow_color: str = "#FF6B9D",
                            bg_color: str = "rgba(255, 107, 157, 0.9)",
                            hover_color: str = "rgba(236, 64, 122, 0.95)",
                            border_radius: int = 12,
                            padding: str = "10px 24px",
                            font_size: int = 14,
                            color: str = "white"):
    """发光按钮样式 — 带光晕悬停效果"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: {color};
            border: none;
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        QPushButton:pressed {{
            background-color: rgba(216, 27, 96, 0.95);
        }}
        QPushButton:disabled {{
            background-color: rgba(200, 200, 200, 0.5);
            color: #BDBDBD;
        }}
    """)


def apply_segmented_button_style(buttons: list, active_index: int = 0,
                                 active_color: str = "#FF6B9D",
                                 inactive_color: str = "transparent",
                                 border_radius: int = 10):
    """分段控件样式 — 按钮组仿 iOS 分段"""
    for i, btn in enumerate(buttons):
        if i == active_index:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {active_color};
                    color: white;
                    border: none;
                    border-radius: {border_radius}px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 600;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {inactive_color};
                    color: #888;
                    border: 1.5px solid #E0E0E0;
                    border-radius: {border_radius}px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 107, 157, 0.06);
                    color: #FF6B9D;
                    border-color: rgba(255, 107, 157, 0.3);
                }}
            """)


def apply_badge_style(label,
                      bg_color: str = "#FF5252",
                      color: str = "white",
                      border_radius: int = 10):
    """徽标/Badge 样式 — 用于未读计数等"""
    label.setStyleSheet(f"""
        QLabel {{
            background-color: {bg_color};
            color: {color};
            border-radius: {border_radius}px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: bold;
        }}
    """)


def apply_empty_state_style(widget, icon_text: str = "📋",
                            message: str = "暂无数据",
                            sub_message: str = ""):
    """空状态占位样式"""
    from PyQt5.QtWidgets import QVBoxLayout, QLabel
    from PyQt5.QtGui import QFont

    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignCenter)
    layout.setSpacing(12)

    icon_label = QLabel(icon_text)
    icon_label.setFont(QFont("Segoe UI Emoji", 48))
    icon_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(icon_label)

    msg_label = QLabel(message)
    msg_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
    msg_label.setAlignment(Qt.AlignCenter)
    msg_label.setStyleSheet(f"color: {SUBTEXT_COLOR};")
    layout.addWidget(msg_label)

    if sub_message:
        sub_label = QLabel(sub_message)
        sub_label.setAlignment(Qt.AlignCenter)
        sub_label.setStyleSheet(f"color: #BDBDBD; font-size: 13px;")
        layout.addWidget(sub_label)

    widget.setLayout(layout)


def apply_loading_spinner_style(label, size: int = 32,
                                 color: str = "#FF6B9D"):
    """加载旋转动画样式（配合动画使用）"""
    label.setStyleSheet(f"""
        QLabel {{
            color: {color};
            font-size: {size}px;
        }}
    """)


def apply_notification_banner_style(widget, bg_color: str = "#FFF3E0",
                                     text_color: str = "#E65100",
                                     border_color: str = "#FFB74D"):
    """通知横幅样式"""
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 10px;
            padding: 12px 16px;
        }}
        QWidget QLabel {{
            color: {text_color};
            background: transparent;
            font-size: 13px;
        }}
    """)


# ========================
# 现代高级样式函数
# ========================

def apply_modern_card_style(widget: QWidget,
                             bg_color: str = "#FFFFFF",
                             border_radius: int = 16,
                             shadow: bool = True):
    """现代卡片样式 — 柔和阴影、圆角"""
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {bg_color};
            border: 1px solid rgba(0, 0, 0, 0.04);
            border-radius: {border_radius}px;
        }}
        QWidget:hover {{
            border: 1px solid rgba(255, 107, 157, 0.12);
            background-color: {bg_color};
        }}
    """)

    if shadow:
        try:
            shadow_effect = QGraphicsDropShadowEffect(widget)
            shadow_effect.setBlurRadius(20)
            shadow_effect.setColor(QColor(0, 0, 0, 15))
            shadow_effect.setOffset(0, 4)
            widget.setGraphicsEffect(shadow_effect)
        except:
            pass


def apply_modern_button_style(button: QPushButton,
                               bg_color: str = "#FF6B9D",
                               hover_color: str = "#EC407A",
                               text_color: str = "white",
                               border_radius: int = 12,
                               padding: str = "10px 24px",
                               font_size: int = 14,
                               font_weight: str = "600"):
    """现代按钮样式 — 渐变背景、平滑过渡"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: {text_color};
            border: none;
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: {font_weight};
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {PRESSED_COLOR};
        }}
        QPushButton:disabled {{
            background-color: #E5E7EB;
            color: #9CA3AF;
        }}
    """)


def apply_modern_input_style(line_edit: QLineEdit,
                              border_radius: int = 12,
                              bg_color: str = "#F9FAFB",
                              focus_border: str = "#FF6B9D"):
    """现代输入框样式 — 柔和背景、动态边框"""
    line_edit.setStyleSheet(f"""
        QLineEdit {{
            background-color: {bg_color};
            border: 1.5px solid rgba(0, 0, 0, 0.06);
            border-radius: {border_radius}px;
            padding: 10px 14px;
            font-size: 14px;
            color: {TEXT_COLOR};
            selection-background-color: rgba(255, 107, 157, 0.2);
        }}
        QLineEdit:hover {{
            border: 1.5px solid rgba(0, 0, 0, 0.1);
            background-color: #FFFFFF;
        }}
        QLineEdit:focus {{
            border: 2px solid {focus_border};
            background-color: #FFFFFF;
            padding: 9px 13px;
        }}
    """)


def apply_modern_dialog_style(dialog: QDialog,
                               bg_color: str = "#FFFFFF",
                               border_radius: int = 20,
                               border_color: str = "rgba(255, 107, 157, 0.3)"):
    """现代对话框样式 — 圆角、边框"""
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {bg_color};
            border: 2px solid {border_color};
            border-radius: {border_radius}px;
        }}
        QDialog QLabel {{
            background: transparent;
        }}
    """)


def apply_modern_tag_style(label: QLabel,
                            bg_color: str = "#FFF0F5",
                            text_color: str = "#FF6B9D",
                            border_radius: int = 8,
                            padding: str = "4px 10px"):
    """现代标签样式 — 柔和背景"""
    label.setStyleSheet(f"""
        QLabel {{
            background-color: {bg_color};
            color: {text_color};
            border: none;
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: 12px;
            font-weight: 500;
        }}
    """)


def apply_gradient_button(button: QPushButton,
                           start_color: str = "#FF6B9D",
                           end_color: str = "#EC407A",
                           hover_start: str = "#EC407A",
                           hover_end: str = "#D81B60",
                           border_radius: int = 12,
                           padding: str = "10px 24px",
                           font_size: int = 14):
    """渐变按钮样式 — 动态渐变效果"""
    button.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {start_color},
                stop:1 {end_color});
            color: white;
            border: none;
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {hover_start},
                stop:1 {hover_end});
        }}
        QPushButton:pressed {{
            background: {PRESSED_COLOR};
        }}
    """)


def apply_outlined_button(button: QPushButton,
                           text_color: str = "#FF6B9D",
                           border_color: str = "#FF6B9D",
                           hover_bg: str = "rgba(255, 107, 157, 0.08)",
                           border_radius: int = 12,
                           padding: str = "10px 24px",
                           font_size: int = 14):
    """描边按钮样式 — 透明背景、彩色边框"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {text_color};
            border: 2px solid {border_color};
            border-radius: {border_radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            border: 2px solid {text_color};
        }}
        QPushButton:pressed {{
            background-color: rgba(255, 107, 157, 0.15);
        }}
    """)


def apply_icon_button(button: QPushButton,
                      size: int = 44,
                      bg_color: str = "rgba(255, 107, 157, 0.1)",
                      hover_color: str = "rgba(255, 107, 157, 0.2)",
                      icon_color: str = "#FF6B9D",
                      border_radius: int = 22):
    """图标按钮样式 — 圆形、柔和背景"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: {icon_color};
            border: none;
            border-radius: {border_radius}px;
            font-size: 18px;
            min-width: {size}px;
            max-width: {size}px;
            min-height: {size}px;
            max-height: {size}px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: rgba(255, 107, 157, 0.3);
        }}
    """)


def apply_floating_action_button(button: QPushButton,
                                  bg_color: str = "#FF6B9D",
                                  hover_color: str = "#EC407A",
                                  size: int = 56,
                                  icon_size: int = 24):
    """浮动操作按钮 (FAB) 样式 — Material Design 风格"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg_color};
            color: white;
            border: none;
            border-radius: {size // 2}px;
            font-size: {icon_size}px;
            min-width: {size}px;
            max-width: {size}px;
            min-height: {size}px;
            max-height: {size}px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {PRESSED_COLOR};
        }}
    """)


def apply_modern_checkbox(checkbox: QCheckBox,
                          checked_color: str = "#FF6B9D",
                          unchecked_border: str = "#D1D5DB",
                          border_radius: int = 6,
                          indicator_size: int = 22):
    """现代复选框样式 — 圆角、动画感"""
    checkbox.setStyleSheet(f"""
        QCheckBox {{
            spacing: 10px;
            color: {TEXT_COLOR};
            font-size: 14px;
        }}
        QCheckBox::indicator {{
            width: {indicator_size}px;
            height: {indicator_size}px;
            border-radius: {border_radius}px;
            border: 2px solid {unchecked_border};
            background: white;
        }}
        QCheckBox::indicator:hover {{
            border-color: {checked_color};
            background: #FFF0F5;
        }}
        QCheckBox::indicator:checked {{
            background-color: {checked_color};
            border-color: {checked_color};
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: {HOVER_COLOR};
        }}
    """)


def apply_modern_scrollbar(area: QWidget = None):
    """现代滚动条样式 — 细长、半透明"""
    style = """
        QScrollBar:vertical {
            width: 6px;
            background: transparent;
            margin: 4px 2px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 0.15);
            border-radius: 3px;
            min-height: 40px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(0, 0, 0, 0.25);
        }
        QScrollBar::handle:vertical:pressed {
            background: #FF6B9D;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: transparent;
        }
        QScrollBar:horizontal {
            height: 6px;
            background: transparent;
            margin: 2px 4px;
        }
        QScrollBar::handle:horizontal {
            background: rgba(0, 0, 0, 0.15);
            border-radius: 3px;
            min-width: 40px;
        }
        QScrollBar::handle:horizontal:hover {
            background: rgba(0, 0, 0, 0.25);
        }
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            width: 0;
        }
    """
    if area:
        area.setStyleSheet(style)
    return style


def apply_modern_combobox(combo: QComboBox,
                          border_radius: int = 12,
                          border_color: str = "rgba(0, 0, 0, 0.06)",
                          focus_color: str = "#FF6B9D"):
    """现代下拉框样式 — 圆角、柔和边框"""
    combo.setStyleSheet(f"""
        QComboBox {{
            background-color: #F9FAFB;
            border: 1.5px solid {border_color};
            border-radius: {border_radius}px;
            padding: 10px 14px;
            font-size: 14px;
            color: {TEXT_COLOR};
            min-width: 100px;
        }}
        QComboBox:hover {{
            border: 1.5px solid rgba(255, 107, 157, 0.3);
            background-color: white;
        }}
        QComboBox:focus {{
            border: 2px solid {focus_color};
            background-color: white;
            padding: 9px 13px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 28px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #9CA3AF;
            margin-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: white;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 12px;
            padding: 8px;
            selection-background-color: rgba(255, 107, 157, 0.1);
            selection-color: {TEXT_COLOR};
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 10px 14px;
            border-radius: 8px;
            min-height: 28px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: rgba(255, 107, 157, 0.08);
        }}
    """)


def apply_modern_spinbox(spinbox: QSpinBox,
                         border_radius: int = 10,
                         bg_color: str = "#F9FAFB",
                         focus_color: str = "#FF6B9D"):
    """现代数字框样式"""
    spinbox.setStyleSheet(f"""
        QSpinBox {{
            background-color: {bg_color};
            border: 1.5px solid rgba(0, 0, 0, 0.06);
            border-radius: {border_radius}px;
            padding: 8px 12px;
            font-size: 14px;
            color: {TEXT_COLOR};
        }}
        QSpinBox:hover {{
            border: 1.5px solid rgba(255, 107, 157, 0.3);
            background-color: white;
        }}
        QSpinBox:focus {{
            border: 2px solid {focus_color};
            background-color: white;
            padding: 7px 11px;
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background: transparent;
            border-radius: 4px;
            width: 20px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background: rgba(255, 107, 157, 0.1);
        }}
        QSpinBox::up-arrow {{
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid #9CA3AF;
        }}
        QSpinBox::down-arrow {{
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #9CA3AF;
        }}
    """)


def apply_status_badge(label: QLabel,
                        status: str = "info",
                        border_radius: int = 8):
    """状态徽章样式 — success/warning/danger/info"""
    colors = {
        "success": ("#D1FAE5", "#059669"),
        "warning": ("#FEF3C7", "#D97706"),
        "danger": ("#FEE2E2", "#DC2626"),
        "info": ("#DBEAFE", "#2563EB"),
    }
    bg, text = colors.get(status, colors["info"])
    label.setStyleSheet(f"""
        QLabel {{
            background-color: {bg};
            color: {text};
            border: none;
            border-radius: {border_radius}px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 600;
        }}
    """)


def get_global_stylesheet():
    """获取全局样式表 — 现代主题"""
    return f"""
        QMainWindow {{
            background-color: {GLOBAL_BG_COLOR};
        }}
        QWidget {{
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        }}
        QToolTip {{
            background-color: #1F2937;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        QMenuBar {{
            background-color: white;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            padding: 6px 0;
        }}
        QMenuBar::item {{
            padding: 8px 14px;
            background: transparent;
            border-radius: 6px;
            color: {TEXT_COLOR};
        }}
        QMenuBar::item:selected {{
            background-color: rgba(255, 107, 157, 0.1);
            color: {THEME_COLOR};
        }}
        QMenu {{
            background-color: white;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 12px;
            padding: 8px 0;
        }}
        QMenu::item {{
            padding: 10px 20px;
            color: {TEXT_COLOR};
            border-radius: 0;
        }}
        QMenu::item:selected {{
            background-color: rgba(255, 107, 157, 0.1);
            color: {THEME_COLOR};
        }}
        QMenu::separator {{
            height: 1px;
            background: rgba(0, 0, 0, 0.06);
            margin: 6px 12px;
        }}
    """
