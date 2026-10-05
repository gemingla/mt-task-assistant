"""添加任务对话框"""
from ui_common import *  # noqa: F401,F403


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
