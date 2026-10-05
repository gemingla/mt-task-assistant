"""个性化主题对话框"""
from ui_common import *  # noqa: F401,F403


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
