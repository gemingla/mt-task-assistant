"""提醒管理标签页"""
from ui_common import *  # noqa: F401,F403
from dialogs.reminder_dialog import ReminderDialog


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
