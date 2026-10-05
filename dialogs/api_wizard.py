"""API 配置向导"""
from ui_common import *  # noqa: F401,F403


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

        def request_status():
            import requests
            response = requests.get(
                f"{self.api_url}/models",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            return response.status_code

        self._test_worker = BackgroundTask(request_status, parent=self)
        self._test_worker.succeeded.connect(self._on_test_finished)
        self._test_worker.failed.connect(lambda msg: self._on_test_finished(msg))
        self._test_worker.start()

    def _on_test_finished(self, result):
        """result 为 HTTP 状态码，或请求异常时的错误信息"""
        if result == 200:
            self.status_label.setText("✅ 连接成功！API Key 有效")
            self.status_label.setStyleSheet("background-color: #E8F5E9; color: #2E7D32; padding: 10px; border-radius: 5px;")
        else:
            detail = f"HTTP {result}" if isinstance(result, int) else result
            self.status_label.setText(f"❌ 连接失败：{detail}")
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
