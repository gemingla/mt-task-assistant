"""关于对话框"""
from ui_common import *  # noqa: F401,F403
from version import __version__


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 MT任务助手")
        self.setFixedSize(420, 520)
        self.setStyleSheet("background-color: #FFFFFF;")
        # 启用双缓冲减少闪烁
        self.setAttribute(Qt.WA_PaintOnScreen, False)
        self.setAutoFillBackground(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(30, 25, 30, 25)

        img_path = resource_path(os.path.join("images", "mt520.png"))

        avatar_label = QLabel()
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setFixedSize(100, 100)

        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            circular = QPixmap(100, 100)
            circular.fill(Qt.transparent)
            from PyQt5.QtGui import QPainter, QBrush, QPen
            painter = QPainter(circular)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            brush = QBrush(scaled_pixmap)
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 100, 100)
            painter.end()
            avatar_label.setPixmap(circular)
        else:
            avatar_label.setText("🐰")
            avatar_label.setStyleSheet("font-size: 70px; color: #FFB6C1;")

        layout.addWidget(avatar_label, alignment=Qt.AlignCenter)
        
        avatar_note = QLabel("仅为作者使用头像")
        avatar_note.setAlignment(Qt.AlignCenter)
        avatar_note.setStyleSheet("font-size: 9px; color: #999; font-style: italic;")
        layout.addWidget(avatar_note)
        
        layout.addSpacing(8)

        title_label = QLabel("📋 MT任务助手")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        version_label = QLabel(f"版本 {__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 12px; color: #999;")
        layout.addWidget(version_label)

        layout.addSpacing(12)

        desc_label = QLabel("一个基于 AI 的任务管理助手，帮助你拆分目标、管理时间。")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 13px; color: #666; line-height: 1.6; padding: 0 20px;")
        layout.addWidget(desc_label)

        layout.addSpacing(18)

        features_label = QLabel("主要功能：")
        features_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333; padding-left: 5px;")
        layout.addWidget(features_label)

        feature_layout = QVBoxLayout()
        feature_layout.setSpacing(8)
        feature_layout.setContentsMargins(10, 5, 10, 5)

        features = [
            "🤖 AI 智能任务拆分",
            "🍅 番茄钟专注计时",
            "📊 数据统计分析",
            "🎨 个性化主题定制",
            "🧭 API 配置向导"
        ]
        for text in features:
            f_label = QLabel(text)
            f_label.setStyleSheet("font-size: 12px; color: #666; padding-left: 5px;")
            feature_layout.addWidget(f_label)

        layout.addLayout(feature_layout)

        layout.addStretch()

        layout.addSpacing(10)

        tech_label = QLabel("使用 PyQt5 开发 | DeepSeek API 驱动")
        tech_label.setAlignment(Qt.AlignCenter)
        tech_label.setStyleSheet("font-size: 10px; color: #BBB;")
        layout.addWidget(tech_label)

        author_label = QLabel("作者：zyhm，灵感来源萌兔agent")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("font-size: 10px; color: #BBB;")
        layout.addWidget(author_label)

        layout.addSpacing(12)

        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(120, 38)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFB6C1;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF8FAB;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
