"""任务卡片"""
from ui_common import *  # noqa: F401,F403


class TaskCardWidget(QFrame):
    deleteRequested = pyqtSignal(object)
    completionToggled = pyqtSignal(object)
    focusRequested = pyqtSignal(object)
    renameRequested = pyqtSignal(object, str)
    tagClicked = pyqtSignal(str)  # 标签点击信号

    def __init__(self, task, task_manager, stats_manager, tag_manager, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(False)  # 半透明玻璃卡片，不能先铺不透明底色
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

        self.focus_btn = LiquidGlassButton("🎯", tint="#FF6B9D", font_px=18, refract=False,
                                           hover_tint="#EC407A")
        self.focus_btn.setFixedSize(46, 46)
        self.focus_btn.setToolTip("开始专注")
        self.focus_btn.clicked.connect(self.on_focus_clicked)
        if self.task.completed:
            self.focus_btn.hide()
        layout.addWidget(self.focus_btn)

        self.delete_btn = LiquidGlassButton("✕", tint="#FFFFFF", text_color="#A0A0A8", font_px=15,
                                            refract=False, hover_tint="#FFCDD2", hover_text_color="#E53935")
        self.delete_btn.setFixedSize(38, 38)
        self.delete_btn.setToolTip("删除任务")
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
                QFrame#taskCardWidget {
                    background-color: rgba(240, 253, 244, 0.62);
                    border: 1.5px solid rgba(134, 239, 172, 0.85);
                    border-radius: 14px;
                }
            """)
            self.name_label.setStyleSheet("color: #166534; text-decoration: line-through; background-color: transparent;")
            self.time_label.setStyleSheet("color: #22C55E; font-size: 12px; background-color: transparent;")
            self.focus_btn.hide()
        else:
            self.setStyleSheet("""
                QFrame#taskCardWidget {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 0.86), stop:1 rgba(255, 255, 255, 0.62));
                    border: 1px solid rgba(255, 255, 255, 0.95);
                    border-radius: 14px;
                }
                QFrame#taskCardWidget:hover {
                    border: 1.5px solid rgba(255, 143, 171, 0.85);
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 0.96), stop:1 rgba(255, 250, 251, 0.80));
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
        # 完成任务时：删除线从左到右划过 + 弹跳庆祝，动画结束后再切换为完成样式
        if state == Qt.Checked and not self.task.completed:
            self._play_complete_bounce()
            self._strike_anim = play_strike_through(self.name_label, on_finished=self._do_checkbox_change)
        else:
            QTimer.singleShot(100, self._do_checkbox_change)

    def play_enter(self):
        """新任务入场：从左侧滑入并淡入"""
        layout = self.layout()
        margins = layout.contentsMargins()
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        anim = QVariantAnimation(self)
        anim.setDuration(420)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def step(v):
            effect.setOpacity(v)
            layout.setContentsMargins(int(margins.left() + 40 * (1 - v)), margins.top(),
                                      margins.right(), margins.bottom())

        anim.valueChanged.connect(step)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start(QVariantAnimation.DeleteWhenStopped)
        self._enter_anim = anim

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
            if isinstance(widget, QMainWindow):  # 主窗口在 main.py，避免循环导入
                return widget
            widget = widget.parent()
        return None
