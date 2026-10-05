"""基础设置对话框"""
from ui_common import *  # noqa: F401,F403
from dialogs.api_wizard import ApiWizard


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

        def fetch():
            # 后台线程里不能弹窗，先把错误信息收集起来
            errors = []
            models = get_models(api_url, api_key, callback=errors.append)
            return models, errors

        self._fetch_worker = BackgroundTask(fetch, parent=self)
        self._fetch_worker.succeeded.connect(self._on_models_fetched)
        self._fetch_worker.failed.connect(lambda msg: self._on_models_fetched((None, [msg])))
        self._fetch_worker.start()

    def _on_models_fetched(self, result):
        models, errors = result
        self.fetch_models_btn.setText("获取")
        self.fetch_models_btn.setEnabled(True)
        if errors:
            QMessageBox.warning(self, "错误", "\n".join(errors))
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
