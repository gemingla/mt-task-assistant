"""添加/编辑提醒对话框"""
from ui_common import *  # noqa: F401,F403


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
