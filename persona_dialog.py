from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
from PyQt5.QtCore import Qt
from config import ConfigManager, DEFAULT_CONFIG


class PersonaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.setWindowTitle("自定义人设")
        self.setFixedSize(500, 300)
        self.setStyleSheet("background-color: #FAFAFA;")
        self.init_ui()
        self.load_prompt()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title_label = QLabel("设置 AI 助手的人设和性格")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("输入 AI 助手的人设提示词...")
        self.prompt_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                color: #333;
            }
            QTextEdit:focus {
                border: 2px solid #FF8FAB;
            }
        """)
        layout.addWidget(self.prompt_edit)

        hint_label = QLabel("💡 提示：人设决定了 AI 助手回复的风格和语气")
        hint_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(hint_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setFixedSize(100, 38)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                color: #555;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E8E8E8;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_default)
        btn_layout.addWidget(self.reset_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedSize(80, 38)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
        """)
        self.save_btn.clicked.connect(self.save_prompt)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def load_prompt(self):
        config = self.config_manager.load_config()
        prompt = config.get("system_prompt", DEFAULT_CONFIG["system_prompt"])
        self.prompt_edit.setPlainText(prompt)

    def reset_to_default(self):
        self.prompt_edit.setPlainText(DEFAULT_CONFIG["system_prompt"])

    def save_prompt(self):
        from PyQt5.QtWidgets import QMessageBox
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            prompt = DEFAULT_CONFIG["system_prompt"]
        config = self.config_manager.load_config()
        config["system_prompt"] = prompt
        self.config_manager.save_config(config)
        QMessageBox.information(self, "提示", "人设已更新")
        self.accept()
