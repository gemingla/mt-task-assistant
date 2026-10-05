from ui_common import *  # noqa: F401,F403
from widgets.task_card import TaskCardWidget
from dialogs.settings_dialog import SettingsDialog
from dialogs.api_wizard import IntroPage, RegisterPage, CreateKeyPage, InputKeyPage, FinishPage, ApiWizard
from dialogs.tag_dialogs import TagManagerDialog, AddTagDialog
from dialogs.memory_dialog import MemoryManagementDialog
from dialogs.about_dialog import AboutDialog
from dialogs.theme_dialog import ThemeDialog
from dialogs.add_task_dialog import AddTaskDialog
from dialogs.reminder_dialog import ReminderDialog
from tabs.reminder_tab import ReminderTab
from tabs.pomodoro_tab import PomodoroTab
from tabs.stats_tab import StatsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 核心管理器（必须立即加载）
        self.config_manager = ConfigManager()
        self.task_manager = TaskManager()
        self.stats_manager = StatsManager()
        self.tag_manager = TagManager()
        self.reminder_manager = ReminderManager(
            data_file=get_data_path("reminders.json")
        )

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        self.scale_factor = self.screen_width / 1920.0 if self.screen_width > 1920 else 1.0

        # 主题适配器：让对话框和各页面中写死的浅色样式跟随玻璃主题
        self.theme_adapter = ThemeAdapter(QApplication.instance(), self)

        # 初始化UI和系统托盘
        self.init_system_tray()
        self.init_ui()

        # 设置窗口图标
        icon_path = resource_path(os.path.join("images", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 创建桌面快捷方式
        self.create_desktop_shortcut()

        self.refresh_tasks()
        self.start_reminder_timer()
        
        # 显示欢迎向导（首次使用）- 在主窗口显示后弹出
        if should_show_wizard():
            # 使用 QTimer 延迟显示，让主窗口先显示
            QTimer.singleShot(100, self.show_welcome_wizard)
        
        # 延迟加载非核心组件
        QTimer.singleShot(500, self._delayed_init)

    def _delayed_init(self):
        """延迟加载非核心组件"""
        # 初始化记忆管理器（较重的组件）
        self.memory_manager = MemoryManager()
        self.ethics_analyzer = AIEthicsAnalyzer()
        # 初始化成就系统
        self.achievement_manager = AchievementManager()
        # 每日自动备份（当天已备份则跳过，只保留最近 7 份）
        QTimer.singleShot(2000, self._run_auto_backup)

    def _run_auto_backup(self):
        try:
            self._make_backup_manager().auto_backup()
        except Exception:
            import traceback
            log_error("自动备份失败:\n" + traceback.format_exc())

    def _make_backup_manager(self):
        return BackupManager(
            task_manager=self.task_manager,
            reminder_manager=self.reminder_manager,
            stats_manager=self.stats_manager,
            tag_manager=self.tag_manager,
            config_manager=self.config_manager,
            memory_manager=getattr(self, 'memory_manager', None)
        )

    def create_desktop_shortcut(self):
        """创建桌面快捷方式（仅打包后首次运行创建）"""
        if not getattr(sys, 'frozen', False):
            return  # 开发环境不创建

        shortcut_path = os.path.join(
            os.path.expanduser("~"), "Desktop", "MT任务助手.lnk"
        )
        if os.path.exists(shortcut_path):
            return  # 已存在则不重复创建

        try:
            import pythoncom
            from win32com.client import Dispatch
            pythoncom.CoInitialize()
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = sys.executable
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            icon_path = resource_path(os.path.join("images", "icon.ico"))
            if os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            shortcut.Save()
        except ImportError:
            pass  # 无 pywin32 则跳过
        except Exception:
            pass

    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        tray_icon_path = resource_path(os.path.join("images", "mt520.png"))
        if os.path.exists(tray_icon_path):
            self.tray_icon.setIcon(QIcon(tray_icon_path))
        else:
            fallback_pixmap = QPixmap(16, 16)
            fallback_pixmap.fill(QColor("#FFB6C1"))
            self.tray_icon.setIcon(QIcon(fallback_pixmap))
        self.tray_icon.setToolTip("MT任务助手")
        self.tray_icon.show()

    def start_reminder_timer(self):
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_upcoming_tasks)
        self.reminder_timer.start(60000)

    def check_upcoming_tasks(self):
        upcoming = self.task_manager.get_upcoming_tasks(minutes=5)
        for task, minutes_left in upcoming:
            self.tray_icon.showMessage(
                "⏰ 任务提醒",
                f"任务「{task.name}」将在 {int(minutes_left)} 分钟后截止，请尽快完成！",
                QSystemTrayIcon.Information,
                5000
            )
            self.task_manager.mark_task_reminded(task.id)
    
    def show_welcome_wizard(self):
        """显示欢迎向导"""
        wizard = WelcomeWizard(self)
        # 设置窗口在最上层，始终置顶
        wizard.setWindowFlags(wizard.windowFlags() | Qt.WindowStaysOnTopHint)
        wizard.setWindowModality(Qt.ApplicationModal)  # 应用模态，阻止其他窗口交互
        if wizard.exec_() == QWizard.Accepted:
            mark_wizard_shown()

    def show_memory_management(self):
        """显示记忆管理对话框"""
        if not hasattr(self, 'memory_manager'):
            QMessageBox.warning(self, "提示", "记忆管理器尚未初始化，请稍后再试！")
            return
        
        dialog = MemoryManagementDialog(self.memory_manager, self)
        dialog.exec_()
    
    def show_memory_filter(self):
        """显示智能记忆过滤面板"""
        from PyQt5.QtWidgets import QDialog
        from memory_filter_widget import MemoryFilterWidget
        
        # 创建对话框
        self.memory_filter_dialog = QDialog(self)
        self.memory_filter_dialog.setWindowTitle("🧠 智能记忆过滤系统")
        self.memory_filter_dialog.resize(600, 700)
        
        layout = QVBoxLayout(self.memory_filter_dialog)
        
        # 添加过滤组件
        self.memory_filter_widget = MemoryFilterWidget(self.memory_manager, self.memory_filter_dialog)
        layout.addWidget(self.memory_filter_widget)

        # 显示对话框
        self.memory_filter_dialog.exec_()

    def scale_font(self, base_size):
        return int(base_size * self.scale_factor)

    def scale_size(self, base_size):
        return int(base_size * self.scale_factor)

    def get_current_theme(self):
        config = self.config_manager.load_config()
        theme_config = config.get("theme", {})
        preset = theme_config.get("preset", "萌兔粉")
        custom = theme_config.get("custom", {})
        if preset == "萌兔粉":
            return PRESET_THEMES["萌兔粉"].copy()
        elif preset == "简约灰":
            return PRESET_THEMES["简约灰"].copy()
        elif preset == "深海蓝":
            return PRESET_THEMES["深海蓝"].copy()
        else:
            theme = PRESET_THEMES["萌兔粉"].copy()
            theme["bg_color"] = custom.get("bg_color", "#F5F5F5")
            theme["button_color"] = custom.get("button_color", "#FF8FAB")
            theme["card_bg_color"] = custom.get("card_bg_color", "#FFFFFF")
            theme["text_color"] = custom.get("text_color", "#2D2D2D")
            theme["border_color"] = custom.get("border_color", "#E0E0E0")
            theme["hover_color"] = custom.get("button_color", "#FF6B8A")
            return theme

    def refresh_style(self):
        theme = self.get_current_theme()
        bg = theme["bg_color"]
        btn = theme["button_color"]
        card = theme["card_bg_color"]
        text = theme.get("text_color", "#2D2D2D")
        hover = theme.get("hover_color", btn)
        border = theme.get("border_color", "#E0E0E0")

        def is_dark(c):
            c = c.lstrip('#')
            if len(c) != 6:
                return False
            r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5

        def get_contrast_color(hex_color):
            return "#FFFFFF" if is_dark(hex_color) else "#1A1A1A"

        def get_muted_color(hex_color):
            return "#E0E0E0" if not is_dark(hex_color) else "#505050"

        dark_bg = is_dark(bg)
        dark_card = is_dark(card)
        dark_btn = is_dark(btn)

        main_text = get_contrast_color(bg)
        card_text = get_contrast_color(card)
        btn_text = get_contrast_color(btn)
        muted = get_muted_color(bg)

        input_bg = "#FFFFFF"
        input_text = "#1A1A1A"
        input_border = border

        toolbar_bg = card if dark_bg else "#FFFFFF"
        toolbar_text = card_text if dark_bg else "#333333"

        # 主窗口内部的控件铺在动态玻璃背景上，因此这里不再给 QWidget 统一刷底色
        glass = glass_palette(theme)
        panel_text = "#FFFFFF" if glass["dark"] else "#1F1F2B"
        muted_text = "rgba(255,255,255,0.65)" if glass["dark"] else "rgba(40,40,60,0.55)"
        glass_fill = "rgba(255,255,255,0.10)" if glass["dark"] else "rgba(255,255,255,0.55)"
        glass_fill_hover = "rgba(255,255,255,0.16)" if glass["dark"] else "rgba(255,255,255,0.78)"
        glass_border = "rgba(255,255,255,0.22)" if glass["dark"] else "rgba(255,255,255,0.85)"

        qss = f"""
            QMainWindow {{
                background-color: {bg};
            }}
            QWidget {{
                color: {main_text};
            }}
            QWidget#glassRoot QLabel {{
                color: {panel_text};
            }}
            QFrame#task-card {{
                background-color: {card};
                border-radius: 12px;
                border: 1px solid {border};
            }}
            QFrame#task-card:hover {{
                border: 2px solid {btn};
                background-color: {card};
            }}
            QPushButton {{
                background-color: {btn};
                color: {btn_text};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {hover};
            }}
            QLineEdit, QTextEdit {{
                background-color: {input_bg};
                border: 2px solid {input_border};
                border-radius: 8px;
                padding: 8px;
                color: {input_text};
                selection-background-color: {btn};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {btn};
            }}
            QComboBox {{
                background-color: {input_bg};
                border: 2px solid {input_border};
                border-radius: 8px;
                padding: 8px;
                color: {input_text};
                selection-background-color: {btn};
            }}
            QComboBox:hover {{
                border-color: {btn};
            }}
            QComboBox:focus {{
                border: 2px solid {btn};
            }}
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QScrollArea, QListWidget {{
                background: transparent;
                border: none;
            }}
            QSplitter::handle {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 4px 2px 4px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {muted_text};
                border-radius: 4px;
                min-height: 36px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {btn};
            }}
            QScrollBar:horizontal {{
                background: transparent;
                height: 10px;
                margin: 0 4px 2px 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {muted_text};
                border-radius: 4px;
                min-width: 36px;
            }}
            QScrollBar::add-line, QScrollBar::sub-line {{
                width: 0; height: 0;
            }}
            QScrollBar::add-page, QScrollBar::sub-page {{
                background: transparent;
            }}
            QMenu {{
                background-color: {card};
                color: {card_text};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 22px;
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background-color: {btn};
                color: {btn_text};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {border};
                margin: 5px 10px;
            }}
            QGroupBox {{
                color: {main_text};
                border: 1px solid {border};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                color: {main_text};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QSpinBox {{
                background-color: {input_bg};
                border: 2px solid {input_border};
                border-radius: 8px;
                padding: 6px;
                color: {input_text};
            }}
            QSpinBox:focus {{
                border: 2px solid {btn};
            }}
            QListWidget::item {{
                background-color: transparent;
                border-radius: 8px;
            }}
            QTextBrowser {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 8px;
                color: {card_text};
            }}
            QCheckBox {{
                color: {main_text};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {border};
                background-color: {input_bg};
            }}
            QCheckBox::indicator:checked {{
                background-color: {btn};
                border-color: {btn};
            }}
            QCheckBox::indicator:hover {{
                border-color: {btn};
            }}
            QDialog {{
                background-color: {bg};
            }}
        """
        self.setStyleSheet(qss)

        if hasattr(self, 'toolbar_title'):
            self.toolbar_title.setStyleSheet(f"color: {panel_text}; background: transparent; font-size: 17px; font-weight: bold;")
        if hasattr(self, 'left_title'):
            self.left_title.setStyleSheet(f"color: {panel_text};")
        self._apply_glass_theme(theme, glass, panel_text, muted_text, glass_fill, glass_fill_hover, glass_border)
        if hasattr(self, 'theme_adapter'):
            self.theme_adapter.set_theme(theme)

        try:
            import glass_style
            glass_style.THEME_COLOR = btn
            glass_style.HOVER_COLOR = hover
            glass_style.GLOBAL_BG_COLOR = bg
            glass_style.CARD_BG_COLOR = card
        except:
            pass

    def _apply_glass_theme(self, theme, glass, panel_text, muted_text, glass_fill, glass_fill_hover, glass_border):
        """把当前主题同步到动态背景、玻璃面板和各个玻璃化控件"""
        if not hasattr(self, 'aurora'):
            return
        btn = theme["button_color"]
        self._glass_colors = {"text": panel_text, "muted": muted_text, "fill": glass_fill,
                              "fill_hover": glass_fill_hover, "border": glass_border, "accent": btn}
        self.aurora.set_theme(theme)
        for panel in self.glass_panels:
            panel.set_theme(glass)

        # 深色主题下主题色文字对比度不足，选中态改用提亮后的主题色
        tab_accent = QColor(btn).lighter(170).name() if glass["dark"] else btn
        self.tab_widget.glass_tab_bar().set_colors(tab_accent, glass["dark"])
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar {{ background: transparent; }}
            QTabBar::tab {{
                background: transparent;
                color: {muted_text};
                padding: 9px 13px;
                margin: 4px 1px;
                font-size: 13px;
                font-weight: 500;
                border: none;
            }}
            QTabBar::tab:hover {{ color: {tab_accent}; }}
            QTabBar::tab:selected {{ color: {tab_accent}; font-weight: 600; }}
            QTabBar QToolButton {{
                background: {glass_fill_hover};
                border: 1px solid {glass_border};
                border-radius: 8px;
                margin: 6px 1px;
            }}
        """)

        self.menu_bar.setStyleSheet(f"""
            QMenuBar {{
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: 500;
            }}
            QMenuBar::item {{
                padding: 6px 14px;
                background: transparent;
                color: {panel_text};
                border-radius: 8px;
                margin: 0 1px;
            }}
            QMenuBar::item:selected {{
                background: {glass_fill_hover};
                color: {btn};
            }}
            QMenuBar::item:pressed {{
                background: {btn};
                color: white;
            }}
        """)

        input_style = f"""
            background-color: {glass_fill};
            border: 1.5px solid {glass_border};
            border-radius: 10px;
            padding: 0 14px;
            font-size: 13px;
            color: {panel_text};
        """
        self.search_input.setStyleSheet(f"""
            QLineEdit {{ {input_style} }}
            QLineEdit:hover {{ background-color: {glass_fill_hover}; }}
            QLineEdit:focus {{ border: 1.5px solid {btn}; background-color: {glass_fill_hover}; }}
        """)
        self.tag_filter_combo.setStyleSheet(f"""
            QComboBox {{ {input_style} }}
            QComboBox:hover {{ background-color: {glass_fill_hover}; border: 1.5px solid {btn}; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {muted_text};
                margin-right: 10px;
            }}
        """)
        self.segment_container.setStyleSheet(f"""
            QFrame#segmentContainer {{
                background-color: {glass_fill};
                border: 1px solid {glass_border};
                border-radius: 11px;
            }}
        """)
        self.filter_pill.set_color(btn)
        self._update_filter_buttons()

        self.chat_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {glass_border};
                border-radius: 23px;
                padding: 10px 20px;
                font-size: 14px;
                background-color: {glass_fill};
                color: {panel_text};
            }}
            QLineEdit:hover {{ background-color: {glass_fill_hover}; }}
            QLineEdit:focus {{ border-color: {btn}; background-color: {glass_fill_hover}; }}
        """)
        self._voice_btn_tint = ("#FFFFFF", "#FFFFFF" if glass["dark"] else "#555555")
        self.voice_btn.set_tint(*self._voice_btn_tint)
        self.send_btn.set_tint(btn)
        # 深色主题的 hover 色可能与“导出”的绿色撞色，改用主色
        self.add_button.set_tint(btn if glass["dark"] else theme.get("hover_color", btn))

    def init_ui(self):
        self.setWindowTitle("MT任务助手")

        if self.screen_width >= 2560:
            self.resize(1400, 900)
        elif self.screen_width >= 1920:
            self.resize(1200, 800)
        else:
            self.resize(1000, 700)

        # 动态玻璃背景作为 central widget，所有面板都浮在它上面
        self.aurora = AuroraBackground()
        self.glass_panels = []
        self.setCentralWidget(self.aurora)
        main_layout = QVBoxLayout(self.aurora)
        main_layout.setContentsMargins(14, 10, 14, 14)
        main_layout.setSpacing(10)

        # 顶部玻璃标题栏（标题 + 菜单）
        toolbar_widget = self._new_glass_panel(radius=16)
        toolbar_widget.setObjectName("toolbar")
        self.toolbar_widget = toolbar_widget
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(self.scale_size(16), self.scale_size(6), self.scale_size(12), self.scale_size(6))
        toolbar_layout.setSpacing(12)

        title_label = QLabel("📝 MT任务助手")
        title_label.setFont(QFont("Microsoft YaHei", self.scale_font(14), QFont.Bold))
        self.toolbar_title = title_label
        toolbar_layout.addWidget(title_label)

        self.menu_bar = QMenuBar(toolbar_widget)
        self.create_menu_bar()
        toolbar_layout.addWidget(self.menu_bar, 0, Qt.AlignVCenter)
        toolbar_layout.addStretch()

        main_layout.addWidget(toolbar_widget)

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setHandleWidth(10)
        content_splitter.setChildrenCollapsible(False)

        left_widget = self._new_glass_panel()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(14, 14, 14, 10)

        left_title = QLabel("📋 任务列表")
        left_title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.left_title = left_title

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        # 分段控件容器（选中项下方有滑动的高亮块）
        segment_container = QFrame()
        segment_container.setObjectName("segmentContainer")
        self.segment_container = segment_container
        segment_layout = QHBoxLayout(segment_container)
        segment_layout.setContentsMargins(3, 3, 3, 3)
        segment_layout.setSpacing(0)
        self.filter_pill = SlidingPill(segment_container)

        self.filter_all_btn = QPushButton("全部")
        self.filter_all_btn.setFixedHeight(30)
        self.filter_all_btn.setFixedWidth(70)
        self.filter_all_btn.setCursor(Qt.PointingHandCursor)
        self.filter_all_btn.clicked.connect(lambda: self.set_task_filter("all"))
        segment_layout.addWidget(self.filter_all_btn)

        self.filter_today_btn = QPushButton("今日任务")
        self.filter_today_btn.setFixedHeight(30)
        self.filter_today_btn.setFixedWidth(80)
        self.filter_today_btn.setCursor(Qt.PointingHandCursor)
        self.filter_today_btn.clicked.connect(lambda: self.set_task_filter("today"))
        segment_layout.addWidget(self.filter_today_btn)

        filter_layout.addWidget(segment_container)

        # 搜索框
        search_container = QWidget()
        search_container.setFixedWidth(200)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索任务...")
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        filter_layout.addWidget(search_container)

        # 标签筛选下拉框
        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.addItem("所有标签")
        self.tag_filter_combo.setFixedHeight(36)
        self.tag_filter_combo.setFixedWidth(120)
        self.tag_filter_combo.setCursor(Qt.PointingHandCursor)
        self.tag_filter_combo.currentTextChanged.connect(self.on_tag_filter_changed)
        filter_layout.addWidget(self.tag_filter_combo)

        filter_layout.addStretch()
        left_layout.addLayout(filter_layout)
        self.current_filter = "all"
        self.current_search = ""
        self.current_tag = "所有标签"

        # 初始化标签筛选下拉框
        self.update_tag_filter()

        self.task_list_widget = QListWidget()
        self.task_list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.task_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.task_list_widget.setSpacing(6)
        self.task_list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.task_list_widget.verticalScrollBar().setSingleStep(12)
        self.task_list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.task_list_widget.model().rowsMoved.connect(self.on_tasks_reordered)
        left_layout.addWidget(self.task_list_widget, stretch=1)

        content_splitter.addWidget(left_widget)

        right_widget = self._new_glass_panel()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 6, 8, 8)

        self.tab_widget = GlassTabWidget()
        self.tab_widget.setMinimumHeight(300)

        self.ai_tab = QWidget()
        self.init_ai_tab()
        self.tab_widget.addTab(self.ai_tab, "🤖 AI助手")

        self.pomodoro_tab = PomodoroTab(self.stats_manager, self.task_manager, self.refresh_tasks)
        self.tab_widget.addTab(self.pomodoro_tab, "🍅 番茄钟")

        self.stats_tab = StatsTab(self.stats_manager, self.task_manager)
        self.tab_widget.addTab(self.stats_tab, "📊 数据统计")

        self.reminder_tab = ReminderTab(self.reminder_manager, main_window=self, parent=self)
        self.tab_widget.addTab(self.reminder_tab, "⏰ 提醒管理")

        self.calendar_tab = CalendarWidget(self.task_manager, self.reminder_manager)
        self.tab_widget.addTab(self.calendar_tab, "📅 日历视图")

        right_layout.addWidget(self.tab_widget, stretch=1)

        content_splitter.addWidget(right_widget)
        content_splitter.setSizes([550, 550])

        main_layout.addWidget(content_splitter, stretch=1)

        self.init_bottom_bar(main_layout)

        make_scroll_areas_transparent(self.aurora)
        self.refresh_style()
        self.aurora.set_animated(self.config_manager.load_config().get("glass_animation", True))
        self.filter_pill.move_to(self.filter_all_btn, animate=False)

    def _new_glass_panel(self, radius=18):
        panel = GlassPanel(radius=radius)
        self.glass_panels.append(panel)
        return panel

    def toggle_glass_animation(self, enabled):
        """菜单：开关动态玻璃背景（关闭后保留玻璃外观，只停止动画）"""
        self.aurora.set_animated(enabled)
        for panel in self.glass_panels:
            panel.set_sheen_enabled(enabled)
        config = self.config_manager.load_config()
        config["glass_animation"] = bool(enabled)
        self.config_manager.save_config(config)

    def create_menu_bar(self):
        menubar = self.menu_bar

        file_menu = menubar.addMenu("文件")
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        settings_menu = menubar.addMenu("设置")
        api_config_action = settings_menu.addAction("⚙️ 基础设置")
        api_config_action.triggered.connect(self.open_settings)
        persona_config_action = settings_menu.addAction("人设配置")
        persona_config_action.triggered.connect(self.open_persona_settings)
        theme_action = settings_menu.addAction("个性化主题")
        theme_action.triggered.connect(self.open_theme_settings)
        tag_manager_action = settings_menu.addAction("🏷️ 标签管理")
        tag_manager_action.triggered.connect(self.open_tag_manager)
        glass_action = settings_menu.addAction("✨ 动态玻璃背景")
        glass_action.setCheckable(True)
        glass_action.setChecked(self.config_manager.load_config().get("glass_animation", True))
        glass_action.toggled.connect(self.toggle_glass_animation)
        settings_menu.addSeparator()
        backup_action = settings_menu.addAction("💾 数据备份/恢复")
        backup_action.triggered.connect(self.show_backup_dialog)
        achievement_action = settings_menu.addAction("🏆 成就殿堂")
        achievement_action.triggered.connect(self.show_achievement_dialog)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        smart_sort_action = tools_menu.addAction("📊 智能排序")
        smart_sort_action.triggered.connect(self.show_smart_sort_dialog)
        weekly_report_action = tools_menu.addAction("📋 生成周报")
        weekly_report_action.triggered.connect(self.show_weekly_report)
        tools_menu.addSeparator()
        show_completed_action = tools_menu.addAction(f"👁 显示全部已完成任务（默认只显示 {COMPLETED_VISIBLE_DAYS} 天内）")
        show_completed_action.setCheckable(True)
        show_completed_action.toggled.connect(self.toggle_show_all_completed)
        clear_completed_action = tools_menu.addAction("🧹 清理已完成任务…")
        clear_completed_action.triggered.connect(self.clear_completed_tasks_manually)

        help_menu = menubar.addMenu("帮助")
        api_wizard_action = help_menu.addAction("API配置向导")
        api_wizard_action.triggered.connect(self.show_api_wizard)
        memory_management_action = help_menu.addAction("🧠 记忆管理")
        memory_management_action.triggered.connect(self.show_memory_management)
        memory_filter_action = help_menu.addAction("📊 智能记忆过滤")
        memory_filter_action.triggered.connect(self.show_memory_filter)
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def init_ai_tab(self):
        ai_layout = QVBoxLayout(self.ai_tab)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        ai_layout.setSpacing(0)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.verticalScrollBar().setSingleStep(14)

        self.chat_container = QWidget()
        self.chat_container_layout = QVBoxLayout(self.chat_container)
        self.chat_container_layout.setContentsMargins(15, 15, 15, 15)
        self.chat_container_layout.setSpacing(12)
        self.chat_container_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        ai_layout.addWidget(self.chat_scroll, stretch=1)

        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(10)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入消息与AI对话...")
        self.chat_input.setMinimumHeight(46)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E8E8E8;
                border-radius: 23px;
                padding: 10px 20px;
                font-size: 14px;
                background-color: #F5F7FA;
            }
            QLineEdit:focus {
                border-color: #FF6B9D;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #D0D0D0;
                background-color: #FAFAFA;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input, stretch=1)

        self.voice_btn = LiquidGlassButton("🎤", tint="#FFFFFF", text_color="#555555", font_px=20)
        self.voice_btn.setFixedSize(50, 50)
        self.voice_btn.setToolTip("语音输入")
        self.voice_btn.clicked.connect(self.voice_input)
        input_layout.addWidget(self.voice_btn)

        self.send_btn = LiquidGlassButton("发送", tint="#FF8FAB", font_px=14)
        self.send_btn.setFixedSize(86, 50)
        self.send_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(self.send_btn)

        ai_layout.addWidget(input_container)

        self.conversation_history = []
        self._pending_goal = None
        self._pending_intent_check = False

        welcome_msg = "您好！我是您的 AI 助手。有什么我可以帮您的吗？您可以：\n• 告诉我您的目标，我会帮您拆解成任务\n• 询问任何问题\n• 输入「帮我出一份数学试卷」等考试相关需求"
        self._add_ai_message(welcome_msg, show_adoption=False)  # 欢迎消息不显示采纳按钮

    def init_bottom_bar(self, main_layout):
        bottom_widget = self._new_glass_panel(radius=18)
        bottom_widget.setFixedHeight(78)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(12, 10, 12, 10)
        bottom_layout.setSpacing(10)

        # 液态玻璃按钮：主色随主题变化，导出/删除保留语义色
        self.add_button = LiquidGlassButton("➕ 添加任务", tint="#FF6B9D", font_px=15, radius=18)
        self.add_button.setMinimumHeight(56)
        self.add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_button.clicked.connect(self._add_task_with_ripple)
        bottom_layout.addWidget(self.add_button)

        # 添加导出按钮
        export_button = LiquidGlassButton("📊 导出数据", tint="#43A047", radius=18)
        export_button.setMinimumHeight(56)
        export_button.setFixedWidth(128)
        export_button.clicked.connect(self.export_tasks)
        bottom_layout.addWidget(export_button)

        # 添加批量删除按钮
        delete_button = LiquidGlassButton("🗑️ 批量删除", tint="#E53935", radius=18)
        delete_button.setMinimumHeight(56)
        delete_button.setFixedWidth(128)
        delete_button.clicked.connect(self.batch_delete_tasks)
        bottom_layout.addWidget(delete_button)

        main_layout.addWidget(bottom_widget)

    def create_task_item(self, task):
        item = QListWidgetItem(self.task_list_widget)
        item.setSizeHint(QSize(0, 88))
        item.setData(Qt.UserRole, task.id)

        card_widget = TaskCardWidget(task, self.task_manager, self.stats_manager, self.tag_manager, self.task_list_widget)
        card_widget.deleteRequested.connect(self.on_task_delete)
        card_widget.completionToggled.connect(self.on_task_completion_changed)
        card_widget.focusRequested.connect(self.on_focus_task)
        card_widget.renameRequested.connect(self.on_task_renamed)
        card_widget.tagClicked.connect(self.on_tag_clicked)  # 连接标签点击信号

        self.task_list_widget.setItemWidget(item, card_widget)
        return item

    def _play_task_enter(self, task_id):
        """找到新任务的卡片，滚动到可见位置并播放入场动画"""
        for i in range(self.task_list_widget.count()):
            item = self.task_list_widget.item(i)
            if item.data(Qt.UserRole) == task_id:
                self.task_list_widget.scrollToItem(item)
                card = self.task_list_widget.itemWidget(item)
                if card is not None:
                    card.play_enter()
                return

    def set_task_filter(self, filter_type):
        self.current_filter = filter_type
        active = self.filter_all_btn if filter_type == "all" else self.filter_today_btn
        self.filter_pill.move_to(active)
        self._update_filter_buttons()
        self.refresh_tasks()

    def _update_filter_buttons(self):
        """分段按钮本身保持透明，选中态由下方滑动的高亮块表现"""
        colors = getattr(self, "_glass_colors", {"muted": "#888888", "accent": "#FF6B9D"})
        for btn, key in ((self.filter_all_btn, "all"), (self.filter_today_btn, "today")):
            selected = self.current_filter == key
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {"white" if selected else colors["muted"]};
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: {600 if selected else 500};
                    padding: 0;
                }}
                QPushButton:hover {{
                    color: {"white" if selected else colors["accent"]};
                }}
            """)

    def refresh_tasks(self):
        # 确保 task_list_widget 已创建
        if not hasattr(self, 'task_list_widget'):
            return
        self.task_list_widget.clear()

        tasks = self.task_manager.get_tasks_sorted_by_due()

        # 已完成任务保留在数据中（统计/日历/周报需要），主列表只显示最近完成的
        if not getattr(self, 'show_all_completed', False):
            tasks = [t for t in tasks if self._is_recently_completed(t)]

        # 应用日期筛选
        if self.current_filter == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            tasks = [t for t in tasks if t.due_date and not t.completed and (
                (isinstance(t.due_date, str) and t.due_date.startswith(today)) or
                (isinstance(t.due_date, datetime) and t.due_date.strftime("%Y-%m-%d") == today)
            )]
        
        # 应用搜索筛选
        if hasattr(self, 'current_search') and self.current_search:
            tasks = [t for t in tasks if self.current_search.lower() in t.name.lower()]
        
        # 应用标签筛选
        if hasattr(self, 'current_tag') and self.current_tag and self.current_tag != "所有标签":
            # 去掉 # 前缀进行匹配
            tag_name = self.current_tag.lstrip('#')
            tasks = [t for t in tasks if hasattr(t, 'tags') and tag_name in t.tags]

        for task in tasks:
            self.create_task_item(task)
    
    def on_search_changed(self, text):
        """搜索框文本改变时"""
        self.current_search = text
        self.refresh_tasks()
    
    def on_tag_filter_changed(self, tag):
        """标签筛选改变时"""
        self.current_tag = tag
        self.refresh_tasks()
    
    def update_tag_filter(self):
        """更新标签筛选下拉框"""
        if not hasattr(self, 'tag_filter_combo'):
            return
        
        current_tag = self.tag_filter_combo.currentText()
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("所有标签")
        
        # 从 tag_manager 获取所有标签（预设+自定义）
        all_tags = self.tag_manager.get_all_tags()
        for tag in all_tags:
            self.tag_filter_combo.addItem(f"#{tag}")
        
        # 恢复之前的选择
        index = self.tag_filter_combo.findText(current_tag)
        if index >= 0:
            self.tag_filter_combo.setCurrentIndex(index)

    def on_tasks_reordered(self, parent, start, end, destination, row):
        new_order = []
        for i in range(self.task_list_widget.count()):
            item = self.task_list_widget.item(i)
            task_id = item.data(Qt.UserRole)
            task = self.task_manager.get_task_by_id(task_id)
            if task:
                new_order.append(task)

        self.task_manager.tasks = new_order
        self.task_manager.save_tasks()

    def on_task_delete(self, task):
        self.task_manager.delete_task(task.id)
        self.refresh_tasks()
        if hasattr(self, 'stats_tab'):
            self.stats_tab.refresh_stats()

    def on_task_completion_changed(self, task):
        if hasattr(self, 'stats_tab'):
            self.stats_tab.refresh_stats()

    def on_task_renamed(self, task, new_name):
        pass
    
    def on_tag_clicked(self, tag: str):
        """标签点击事件 - 更改任务标签"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout

        # 获取所有可用标签
        all_tags = self.tag_manager.get_all_tags()
        if not all_tags:
            all_tags = ["工作", "学习", "生活", "娱乐", "重要", "紧急"]

        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"更改标签「{tag}」")
        dialog.setFixedSize(300, 400)
        dialog.setStyleSheet("background-color: #FAFAFA;")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel(f"选择新标签替换「{tag}」")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)

        # 标签列表
        tag_list = QListWidget()
        tag_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #FF8FAB;
                color: white;
            }
            QListWidget::item:hover {
                background: #FFF0F3;
            }
        """)

        for t in all_tags:
            tag_list.addItem(t)
            # 默认选中当前标签
            if t == tag:
                tag_list.setCurrentRow(tag_list.count() - 1)

        layout.addWidget(tag_list)

        # 按钮行
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F5;
                color: #666;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background: #E0E0E0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        remove_btn = QPushButton("移除标签")
        remove_btn.setFixedHeight(36)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: #FFEBEE;
                color: #D32F2F;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background: #FFCDD2; }
        """)
        remove_btn.clicked.connect(lambda: self._change_tag(tag, None, dialog))
        btn_layout.addWidget(remove_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setFixedHeight(36)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #FF8FAB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #FF6B8A; }
        """)
        ok_btn.clicked.connect(lambda: self._change_tag(tag, tag_list.currentItem().text() if tag_list.currentItem() else tag, dialog))
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)
        dialog.exec_()

    def _change_tag(self, old_tag: str, new_tag: str, dialog):
        """更改标签"""
        dialog.accept()

        if new_tag is None:
            # 移除标签 - 找到所有包含该标签的任务
            for task in self.task_manager.tasks:
                if old_tag in getattr(task, 'tags', []):
                    task.tags.remove(old_tag)
                    self.task_manager.save_tasks()
            self.refresh_tasks()
            self.statusBar().showMessage(f"已移除标签「{old_tag}」", 3000)
        elif new_tag != old_tag:
            # 更换标签
            for task in self.task_manager.tasks:
                if old_tag in getattr(task, 'tags', []):
                    task.tags.remove(old_tag)
                    task.tags.append(new_tag)
                    self.task_manager.save_tasks()
            self.refresh_tasks()
            self.statusBar().showMessage(f"已将标签「{old_tag}」更改为「{new_tag}」", 3000)

    def _analyze_urgent_task(self, new_task, due_date):
        """分析紧急任务与现有任务的冲突"""
        from datetime import datetime

        conflicts = []
        suggestions = []

        # 检查时间冲突
        if due_date:
            try:
                if isinstance(due_date, str):
                    new_due = datetime.strptime(due_date[:16], "%Y-%m-%d %H:%M")
                else:
                    new_due = due_date

                # 检查同一天的其他高优先级任务
                same_day_tasks = []
                for task in self.task_manager.tasks:
                    if task.id == new_task.id or task.completed:
                        continue
                    task_due = getattr(task, 'due_date', None)
                    if task_due:
                        try:
                            if isinstance(task_due, str):
                                td = datetime.strptime(task_due[:16], "%Y-%m-%d %H:%M")
                            else:
                                td = task_due
                            # 同一天且时间接近（2小时内）
                            if td.date() == new_due.date():
                                time_diff = abs((td - new_due).total_seconds() / 3600)
                                if time_diff < 2:
                                    same_day_tasks.append((task, time_diff))
                        except:
                            pass

                if same_day_tasks:
                    same_day_tasks.sort(key=lambda x: x[1])
                    for task, diff in same_day_tasks[:3]:
                        conflicts.append(f"• {task.name}（时间接近 {diff:.0f}小时）")

            except:
                pass

        # 检查高优先级任务数量
        high_priority_count = sum(1 for t in self.task_manager.tasks if not t.completed and getattr(t, 'priority', 2) >= 4)

        if high_priority_count > 3:
            suggestions.append(f"当前有 {high_priority_count} 个高优先级任务，建议重新评估优先级")

        # 显示分析结果
        if conflicts or suggestions:
            msg = f"📋 紧急任务分析\n\n"
            msg += f"新任务：「{new_task.name}」\n\n"

            if conflicts:
                msg += "⚠️ 时间冲突：\n" + "\n".join(conflicts) + "\n\n"

            if suggestions:
                msg += "💡 建议：\n" + "\n".join(f"• {s}" for s in suggestions) + "\n\n"

            msg += "是否打开智能排序查看详情？"

            reply = QMessageBox.question(self, "紧急任务分析", msg,
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.show_smart_sort_dialog()

    def highlight_tag_filter(self, tag: str):
        """高亮显示当前筛选的标签"""
        # 重置所有筛选按钮样式
        self.set_task_filter(self.current_filter)
        
        # 显示筛选提示
        if hasattr(self, 'tag_filter_label'):
            self.tag_filter_label.setText(f"🏷️ 筛选: {tag}")
            self.tag_filter_label.show()
        else:
            self.tag_filter_label = QLabel(f"🏷️ 筛选: {tag}")
            self.tag_filter_label.setStyleSheet("""
                QLabel {
                    background-color: #E3F2FD;
                    color: #1976D2;
                    border-radius: 15px;
                    padding: 8px 15px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
            # 插入到任务列表顶部
            self.main_layout.insertWidget(2, self.tag_filter_label)
        
        # 添加清除筛选按钮
        if not hasattr(self, 'clear_tag_filter_btn'):
            self.clear_tag_filter_btn = QPushButton("✕ 清除筛选")
            self.clear_tag_filter_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF5722;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 8px 15px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #E64A19;
                }
            """)
            self.clear_tag_filter_btn.clicked.connect(self.clear_tag_filter)
            self.main_layout.insertWidget(3, self.clear_tag_filter_btn)
        else:
            self.clear_tag_filter_btn.show()
    
    def clear_tag_filter(self):
        """清除标签筛选"""
        self.current_tag_filter = None
        self.refresh_tasks()
        
        # 隐藏筛选提示和清除按钮
        if hasattr(self, 'tag_filter_label'):
            self.tag_filter_label.hide()
        if hasattr(self, 'clear_tag_filter_btn'):
            self.clear_tag_filter_btn.hide()

    def on_focus_task(self, task):
        dialog = PomodoroDialog(task.estimated_minutes, task.name, self)
        dialog.finished.connect(lambda duration, name: self.on_pomodoro_finished(task, duration))
        dialog.exec_()

    def on_pomodoro_finished(self, task, duration):
        self.stats_manager.add_focus_time(duration, task_name=task.name)
        self.task_manager.toggle_complete(task.id)
        self.refresh_tasks()
        if hasattr(self, 'stats_tab'):
            self.stats_tab.refresh_stats()

    def _add_task_with_ripple(self):
        """添加任务按钮点击 — 液态玻璃按钮自带水波与回弹动画"""
        # 延迟打开对话框，让按压回弹先播放一部分
        QTimer.singleShot(220, self.add_task)

    def add_task(self):
        dialog = AddTaskDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            task_name = result[0]
            total_minutes = result[1]
            due_date = result[2]
            priority = result[3] if len(result) > 3 else 2
            tags = result[4] if len(result) > 4 else []

            if task_name and total_minutes > 0:
                task = self.task_manager.add_task(task_name, total_minutes, due_date=due_date, tags=tags)
                if task and priority != 2:
                    task.priority = priority
                    self.task_manager.save_tasks()

                # 紧急任务分析
                if priority >= 4:  # 高优先级或紧急
                    self._analyze_urgent_task(task, due_date)

                self.refresh_tasks()
                if task:
                    self._play_task_enter(task.id)
                self.update_tag_filter()  # 更新标签筛选
                if hasattr(self, 'stats_tab'):
                    self.stats_tab.refresh_stats()
    
    def export_tasks(self):
        """导出任务数据"""
        from PyQt5.QtWidgets import QFileDialog
        import csv
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出任务数据",
            "tasks_export.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                # 写入表头
                writer.writerow([
                    '任务ID', '任务名称', '预计时长(分钟)', '实际时长(分钟)', 
                    '是否完成', '创建日期', '完成日期', '截止日期', 
                    '优先级', '状态', '标签', '来源'
                ])
                
                # 写入任务数据
                for task in self.task_manager.tasks:
                    writer.writerow([
                        task.id,
                        task.name,
                        task.estimated_minutes,
                        task.actual_minutes,
                        '是' if task.completed else '否',
                        task.created_date,
                        task.completed_at or '',
                        task.due_date or '',
                        task.priority,
                        task.status,
                        ', '.join(task.tags) if hasattr(task, 'tags') else '',
                        task.source
                    ])
            
            QMessageBox.information(self, "导出成功", f"任务数据已导出到：\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出任务数据时出错：\n{str(e)}")
    
    def batch_delete_tasks(self):
        """批量删除任务"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QCheckBox
        
        # 获取所有任务
        all_tasks = self.task_manager.tasks
        if not all_tasks:
            QMessageBox.information(self, "提示", "没有可删除的任务")
            return
        
        # 创建批量删除对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("批量删除任务")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 快捷操作按钮
        quick_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_completed_btn = QPushButton("选择已完成")
        select_none_btn = QPushButton("取消全选")
        
        quick_layout.addWidget(select_all_btn)
        quick_layout.addWidget(select_completed_btn)
        quick_layout.addWidget(select_none_btn)
        layout.addLayout(quick_layout)
        
        # 任务列表
        task_list = QListWidget()
        task_list.setSelectionMode(QListWidget.MultiSelection)  # 允许多选
        task_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #DDD;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #EEE;
            }
            QListWidget::item:selected {
                background-color: #FFB6C1;
                color: black;
            }
        """)
        
        for task in all_tasks:
            status = "✅" if task.completed else "⏳"
            tags = f" [{', '.join(['#'+t for t in task.tags])}]" if hasattr(task, 'tags') and task.tags else ""
            task_list.addItem(f"{status} {task.name}{tags}")
        
        layout.addWidget(task_list)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 快捷操作连接
        select_all_btn.clicked.connect(lambda: task_list.selectAll())
        select_none_btn.clicked.connect(lambda: task_list.clearSelection())
        select_completed_btn.clicked.connect(lambda: self._select_completed_tasks(task_list, all_tasks))
        
        if dialog.exec_() == QDialog.Accepted:
            selected_items = task_list.selectedItems()
            if selected_items:
                # 获取选中的任务索引
                selected_indices = [task_list.row(item) for item in selected_items]
                selected_task_ids = [all_tasks[i].id for i in selected_indices]
                
                # 确认删除
                reply = QMessageBox.question(
                    self, '确认删除',
                    f'确定要删除选中的 {len(selected_task_ids)} 个任务吗？',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    deleted_count = self.task_manager.delete_multiple_tasks(selected_task_ids)
                    self.refresh_tasks()
                    if hasattr(self, 'stats_tab'):
                        self.stats_tab.refresh_stats()
                    QMessageBox.information(self, "删除成功", f"已删除 {deleted_count} 个任务")
    
    def _select_completed_tasks(self, task_list, all_tasks):
        """选择所有已完成的任务"""
        task_list.clearSelection()
        for i, task in enumerate(all_tasks):
            if task.completed:
                task_list.item(i).setSelected(True)
    
    def clear_completed_tasks_manually(self):
        """菜单：手动清理已完成任务（会影响统计页/日历/周报中的历史，因此需要确认）"""
        count = len(self.task_manager.get_tasks(filter_completed=True))
        if count == 0:
            QMessageBox.information(self, "提示", "没有已完成的任务")
            return
        reply = QMessageBox.question(
            self, "清理已完成任务",
            f"将永久删除 {count} 个已完成任务，统计、日历和周报中对应的记录也会消失。\n"
            "（每日自动备份仍可找回）\n\n确定要清理吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.task_manager.clear_completed_tasks()
            self.refresh_tasks()

    def toggle_show_all_completed(self, checked):
        """菜单：是否显示所有已完成任务（默认只显示最近完成的）"""
        self.show_all_completed = bool(checked)
        self.refresh_tasks()

    def _is_recently_completed(self, task):
        """已完成任务只在完成后 COMPLETED_VISIBLE_DAYS 天内显示在主列表"""
        if not task.completed:
            return True
        completed_at = parse_datetime(task.completed_at)
        if completed_at is None:
            return True
        return datetime.now() - completed_at <= timedelta(days=COMPLETED_VISIBLE_DAYS)

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def open_persona_settings(self):
        from persona_dialog import PersonaDialog
        dialog = PersonaDialog(self)
        dialog.exec_()

    def open_theme_settings(self):
        dialog = ThemeDialog(self)
        dialog.exec_()

    def show_api_wizard(self):
        wizard = ApiWizard(self)
        wizard.exec_()

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()

    def show_backup_dialog(self):
        """显示备份/恢复对话框"""
        from PyQt5.QtWidgets import QFileDialog, QListWidget, QListWidgetItem

        dialog = QDialog(self)
        dialog.setWindowTitle("💾 数据备份与恢复")
        dialog.setFixedSize(500, 450)
        dialog.setStyleSheet("background-color: #FAFAFA;")

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("💾 数据备份与恢复")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #FF8FAB;")
        layout.addWidget(title)

        # 备份区域
        backup_group = QGroupBox("创建备份")
        backup_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        backup_layout = QVBoxLayout(backup_group)

        backup_btn = QPushButton("📤 创建备份")
        backup_btn.setFixedHeight(40)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FF6B8A; }
        """)
        backup_btn.clicked.connect(lambda: self._create_backup(dialog))
        backup_layout.addWidget(backup_btn)
        layout.addWidget(backup_group)

        # 恢复区域
        restore_group = QGroupBox("恢复数据")
        restore_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        restore_layout = QVBoxLayout(restore_group)

        # 备份列表
        self.backup_list = QListWidget()
        self.backup_list.setFixedHeight(120)
        self.backup_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
        """)
        self._refresh_backup_list()
        restore_layout.addWidget(self.backup_list)

        # 恢复按钮行
        btn_row = QHBoxLayout()
        restore_btn = QPushButton("📥 恢复选中")
        restore_btn.setFixedHeight(36)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        restore_btn.clicked.connect(lambda: self._restore_backup(dialog))
        btn_row.addWidget(restore_btn)

        import_btn = QPushButton("📁 导入备份文件")
        import_btn.setFixedHeight(36)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        import_btn.clicked.connect(lambda: self._import_backup(dialog))
        btn_row.addWidget(import_btn)
        btn_row.addStretch()
        restore_layout.addLayout(btn_row)
        layout.addWidget(restore_group)

        dialog.exec_()

    def _create_backup(self, parent_dialog):
        """创建备份"""
        backup_manager = self._make_backup_manager()
        success, message, path = backup_manager.create_backup()
        if success:
            QMessageBox.information(parent_dialog, "成功", f"{message}\n\n备份位置：{path}")
            self._refresh_backup_list()
        else:
            QMessageBox.warning(parent_dialog, "失败", message)

    def _refresh_backup_list(self):
        """刷新备份列表"""
        self.backup_list.clear()
        backup_manager = BackupManager()
        backups = backup_manager.get_backup_list()
        for backup in backups:
            size_kb = backup["size"] / 1024
            item = QListWidgetItem(f"📅 {backup['time']} ({size_kb:.1f} KB)")
            item.setData(Qt.UserRole, backup["path"])
            self.backup_list.addItem(item)
        if not backups:
            item = QListWidgetItem("暂无备份文件")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.backup_list.addItem(item)

    def _restore_backup(self, parent_dialog):
        """恢复选中的备份"""
        current_item = self.backup_list.currentItem()
        if not current_item:
            QMessageBox.warning(parent_dialog, "提示", "请先选择一个备份文件")
            return

        backup_path = current_item.data(Qt.UserRole)
        if not backup_path:
            return

        reply = QMessageBox.question(
            parent_dialog, "确认恢复",
            "恢复将覆盖当前所有数据，是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            backup_manager = self._make_backup_manager()
            success, message = backup_manager.restore_backup(backup_path)
            if success:
                QMessageBox.information(parent_dialog, "成功", message)
                # 刷新界面
                self.refresh_tasks()
                if hasattr(self, 'reminder_tab'):
                    self.reminder_tab.refresh_reminders()
            else:
                QMessageBox.warning(parent_dialog, "失败", message)

    def _import_backup(self, parent_dialog):
        """导入外部备份文件"""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            parent_dialog, "选择备份文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            reply = QMessageBox.question(
                parent_dialog, "确认恢复",
                "恢复将覆盖当前所有数据，是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                backup_manager = self._make_backup_manager()
                success, message = backup_manager.restore_backup(file_path)
                if success:
                    QMessageBox.information(parent_dialog, "成功", message)
                    self.refresh_tasks()
                    if hasattr(self, 'reminder_tab'):
                        self.reminder_tab.refresh_reminders()
                else:
                    QMessageBox.warning(parent_dialog, "失败", message)

    def show_achievement_dialog(self):
        """显示成就对话框"""
        dialog = AchievementDialog(self.achievement_manager, self)
        dialog.exec_()

    def show_smart_sort_dialog(self):
        """显示智能排序对话框"""
        try:
            from smart_priority import SmartPriorityEngine
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton

            dialog = QDialog(self)
            dialog.setWindowTitle("📊 智能任务排序")
            dialog.setFixedSize(500, 600)
            dialog.setStyleSheet("background-color: #FAFAFA;")

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            # 标题
            title = QLabel("智能优先级排序")
            title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
            title.setStyleSheet("color: #FF8FAB;")
            layout.addWidget(title)

            # 说明
            desc = QLabel("基于截止时间、优先级、标签重要性等多维度智能排序")
            desc.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(desc)

            # 任务列表
            list_widget = QListWidget()
            list_widget.setStyleSheet("""
                QListWidget {
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 5px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #F0F0F0;
                }
                QListWidget::item:selected {
                    background: #FFF0F3;
                    color: #333;
                }
            """)

            engine = SmartPriorityEngine(self.task_manager, self.stats_manager)
            sorted_tasks = engine.sort_tasks_by_priority()

            for task in sorted_tasks:
                score = engine.calculate_smart_priority(task)

                # 显示格式：分数 | 任务名
                item_text = f"[{score:.0f}分] {task.name}"
                if task.due_date:
                    due_str = task.due_date if isinstance(task.due_date, str) else task.due_date.strftime("%Y-%m-%d %H:%M")
                    item_text += f" 📅 {due_str[:10] if len(due_str) >= 10 else due_str}"
                list_widget.addItem(item_text)

            layout.addWidget(list_widget)

            # 详情显示
            detail_label = QLabel("点击任务查看排序详情")
            detail_label.setStyleSheet("color: #888; font-size: 11px; padding: 10px; background: white; border-radius: 6px;")
            layout.addWidget(detail_label)

            def on_item_clicked(item):
                idx = list_widget.row(item)
                if idx < len(sorted_tasks):
                    task = sorted_tasks[idx]
                    breakdown = engine.get_priority_breakdown(task)
                    detail_text = f"""
任务：{task.name}
总分：{breakdown['total_score']:.1f}
├─ 用户优先级：{breakdown['user_priority']:.1f}分
├─ 时间紧迫度：{breakdown['urgency']:.1f}分
├─ 标签重要性：{breakdown['tag_importance']:.1f}分
├─ 任务年龄：{breakdown['age']:.1f}分
└─ 历史完成率调整：{breakdown['completion_rate']:+.1f}分

💡 {breakdown['suggestion']}
"""
                    detail_label.setText(detail_text)
                    detail_label.setStyleSheet("color: #333; font-size: 11px; padding: 10px; background: white; border-radius: 6px;")

            list_widget.itemClicked.connect(on_item_clicked)

            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.setFixedHeight(40)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF8FAB;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #FF6B8A; }
            """)
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec_()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"智能排序失败: {str(e)}")

    def show_weekly_report(self):
        """显示周报"""
        try:
            from weekly_report import WeeklyReportGenerator
            from PyQt5.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QPushButton, QLabel

            generator = WeeklyReportGenerator(self.task_manager, self.stats_manager)
            report = generator.generate_report(week_offset=0)

            dialog = QDialog(self)
            dialog.setWindowTitle("📋 本周工作周报")
            dialog.setFixedSize(600, 700)
            dialog.setStyleSheet("background-color: #FAFAFA;")

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            # 标题
            title = QLabel("📊 本周工作周报")
            title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
            title.setStyleSheet("color: #FF8FAB;")
            layout.addWidget(title)

            # 效率评分
            score_label = QLabel(f"效率评分：{report['score']:.0f}/100")
            score_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            if report['score'] >= 80:
                score_label.setStyleSheet("color: #4CAF50;")
            elif report['score'] >= 60:
                score_label.setStyleSheet("color: #FF9800;")
            else:
                score_label.setStyleSheet("color: #F44336;")
            layout.addWidget(score_label)

            # 报告内容
            report_text = QTextEdit()
            report_text.setReadOnly(True)
            report_text.setStyleSheet("""
                QTextEdit {
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 13px;
                }
            """)
            report_text.setPlainText(generator.format_report_text(report))
            layout.addWidget(report_text)

            # 按钮
            btn_layout = QHBoxLayout()

            copy_btn = QPushButton("📋 复制报告")
            copy_btn.setFixedHeight(36)
            copy_btn.setStyleSheet("""
                QPushButton {
                    background: #E3F2FD;
                    color: #1976D2;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                }
                QPushButton:hover { background: #BBDEFB; }
            """)
            copy_btn.clicked.connect(lambda: self._copy_report(generator.format_report_text(report)))
            btn_layout.addWidget(copy_btn)

            close_btn = QPushButton("关闭")
            close_btn.setFixedHeight(36)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF8FAB;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #FF6B8A; }
            """)
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)
            dialog.exec_()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"生成周报失败: {str(e)}")

    def _copy_report(self, text: str):
        """复制报告到剪贴板"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "成功", "周报已复制到剪贴板！")

    def open_tag_manager(self):
        """打开标签管理对话框"""
        dialog = TagManagerDialog(self.tag_manager, self.task_manager, self)
        dialog.exec_()
        # 刷新标签筛选下拉框
        self.update_tag_filter()

    def _add_user_message(self, message):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        bubble = QFrame(container)
        bubble.setObjectName("userBubble")
        bubble.setStyleSheet("""
            QFrame#userBubble {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 160, 186, 0.95), stop:1 rgba(255, 120, 160, 0.92));
                border-radius: 16px;
                padding: 10px 15px;
                border: 1px solid rgba(255, 255, 255, 0.6);
            }
        """)
        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("color: white; font-size: 14px;")
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)

        container_layout.addWidget(bubble)
        container_layout.addStretch()

        self.chat_container_layout.insertWidget(
            self.chat_container_layout.count() - 1,
            container
        )
        self._scroll_to_bottom()

    def _add_ai_message(self, message, with_action_button=None, show_adoption=False):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()

        bubble = QFrame(container)
        bubble.setObjectName("aiBubble")
        bubble.setStyleSheet("""
            QFrame#aiBubble {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.92), stop:1 rgba(255, 255, 255, 0.72));
                border-radius: 16px;
                padding: 10px 15px;
                border: 1px solid rgba(255, 255, 255, 0.95);
            }
        """)

        content_layout = QVBoxLayout(bubble)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("color: #333; font-size: 14px;")
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_layout.addWidget(label)

        if with_action_button:
            content_layout.addWidget(with_action_button)
        
        # 📊 建议采纳按钮（只在AI给出建议时显示，且明确启用）
        # 只有当 show_adoption=True 时才显示采纳按钮
        has_suggestion = False
        if show_adoption:
            suggestion_keywords = ['建议', '推荐', '应该', '可以', '需要', '最好', '记得', '提醒']
            has_suggestion = any(keyword in message for keyword in suggestion_keywords)
        
        if has_suggestion:
            adoption_layout = QHBoxLayout()
            adoption_layout.setSpacing(10)
            
            adopt_btn = QPushButton("✅ 采纳")
            adopt_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8F5E9;
                    color: #4CAF50;
                    border: 1px solid #81C784;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #C8E6C9;
                }
                QPushButton:disabled {
                    background-color: #F5F5F5;
                    color: #BDBDBD;
                    border: 1px solid #E0E0E0;
                }
            """)
            adopt_btn.setCursor(Qt.PointingHandCursor)
            adopt_btn.clicked.connect(lambda: self._on_suggestion_adopted(True, adopt_btn, reject_btn))
            adoption_layout.addWidget(adopt_btn)
            
            reject_btn = QPushButton("❌ 忽略")
            reject_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFEBEE;
                    color: #F44336;
                    border: 1px solid #E57373;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #FFCDD2;
                }
                QPushButton:disabled {
                    background-color: #F5F5F5;
                    color: #BDBDBD;
                    border: 1px solid #E0E0E0;
                }
            """)
            reject_btn.setCursor(Qt.PointingHandCursor)
            reject_btn.clicked.connect(lambda: self._on_suggestion_adopted(False, adopt_btn, reject_btn))
            adoption_layout.addWidget(reject_btn)
            
            adoption_layout.addStretch()
            content_layout.addLayout(adoption_layout)
        
        # 🔒 AI 伦理：添加局限性说明按钮
        ethics_btn = QPushButton("⚠️ AI 局限性说明")
        ethics_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFF3E0;
                color: #F57C00;
                border: 1px solid #FFB74D;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFE0B2;
            }
        """)
        ethics_btn.setCursor(Qt.PointingHandCursor)
        ethics_btn.clicked.connect(lambda: self._show_ai_limitations(message))
        content_layout.addWidget(ethics_btn)

        container_layout.addWidget(bubble)

        self.chat_container_layout.insertWidget(
            self.chat_container_layout.count() - 1,
            container
        )
        self._scroll_to_bottom()
        return container

    def _show_ai_limitations(self, ai_message: str):
        """显示 AI 局限性说明"""
        # 分析 AI 消息类型
        decision_type = self._detect_decision_type(ai_message)
        
        # 生成局限性说明（确保 ethics_analyzer 已初始化）
        if hasattr(self, 'ethics_analyzer') and self.ethics_analyzer:
            explanation = self.ethics_analyzer.explain_decision(
                decision_type,
                {
                    "message": ai_message,
                    "has_due_date": "截止" in ai_message or "明天" in ai_message,
                    "has_importance": "重要" in ai_message or "紧急" in ai_message
                }
            )
            
            # 格式化显示
            warning_text = AIEthicsWidget.format_limitation_warning(explanation)
            
            # 显示对话框
            QMessageBox.information(self, "⚠️ AI 局限性说明", warning_text)
    
    def _on_suggestion_adopted(self, adopted: bool, adopt_btn=None, reject_btn=None):
        """
        处理建议采纳/忽略
        
        Args:
            adopted: True 表示采纳，False 表示忽略
            adopt_btn: 采纳按钮（用于禁用）
            reject_btn: 忽略按钮（用于禁用）
        """
        # 禁用按钮，防止重复点击
        if adopt_btn:
            adopt_btn.setEnabled(False)
        if reject_btn:
            reject_btn.setEnabled(False)

        # 显示简短提示（不弹窗，只在状态栏显示）
        if adopted:
            self.statusBar().showMessage("✅ 已记录采纳建议", 3000)
        else:
            self.statusBar().showMessage("❌ 已记录忽略建议", 3000)
    
    def _detect_decision_type(self, message: str) -> str:
        """检测 AI 决策类型"""
        if "优先级" in message or "先做" in message or "优先" in message:
            return "priority_adjustment"
        elif "分解" in message or "步骤" in message:
            return "task_decomposition"
        elif "分钟" in message or "小时" in message or "时间" in message:
            return "time_estimation"
        elif "计划" in message or "安排" in message:
            return "study_plan"
        else:
            return "priority_adjustment"  # 默认

    def _add_ai_streaming_message(self):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()

        bubble = QFrame(container)
        bubble.setObjectName("streamingBubble")
        bubble.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                padding: 10px 15px;
                border: 1px solid #E8E8E8;
            }
        """)

        self._ai_streaming_label = QLabel("")
        self._ai_streaming_label.setWordWrap(True)
        self._ai_streaming_label.setStyleSheet("color: #333; font-size: 14px;")
        self._ai_streaming_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ai_streaming_label)

        container_layout.addWidget(bubble)

        self.chat_container_layout.insertWidget(
            self.chat_container_layout.count() - 1,
            container
        )
        self._ai_streaming_container = container
        self._scroll_to_bottom()
        return container

    def _update_streaming_message(self, text):
        if hasattr(self, '_ai_streaming_label') and self._ai_streaming_label:
            self._ai_streaming_label.setText(text)
            self._scroll_to_bottom()

    def _finish_streaming_message(self):
        if hasattr(self, '_ai_streaming_container') and self._ai_streaming_container:
            self._ai_streaming_container.hide()
            self._ai_streaming_container.deleteLater()
            self._ai_streaming_container = None
        if hasattr(self, '_ai_streaming_label'):
            self._ai_streaming_label = None

    def _scroll_to_bottom(self):
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _get_context_prompt(self, include_memory=True):
        config = self.config_manager.load_config()
        base_prompt = config.get("system_prompt", "你是一个友好的 AI 助手。")

        # 获取当前日期和时间
        from datetime import datetime
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_names[now.weekday()]

        pending_tasks = [t for t in self.task_manager.tasks if not t.completed]
        completed_today = self.task_manager.get_today_completed()

        context_parts = []
        # 添加当前时间信息
        context_parts.append(f"【当前时间】{current_date} {weekday} {current_time}")

        # 添加历史记忆 — 仅在 include_memory=True 时注入
        if include_memory and hasattr(self, 'memory_manager') and self.memory_manager:
            recent_message = self.conversation_history[-1]["content"] if self.conversation_history else ""
            memory_context = self.memory_manager.get_context_for_chat(recent_message, max_memories=3)
            if memory_context:
                # 明确告诉AI这是它的记忆
                context_parts.append(f"你有长期记忆功能，以下是相关的历史记忆，请根据这些记忆来回答用户问题：\n{memory_context}")

        if pending_tasks:
            tasks_text = "\n".join([f"- {t.name} (预计{t.estimated_minutes}分钟)" for t in pending_tasks[:5]])
            context_parts.append(f"【未完成任务】\n{tasks_text}")
        if completed_today:
            completed_text = "\n".join([f"- {t.name}" for t in completed_today])
            context_parts.append(f"【今日已完成】\n{completed_text}")

        if context_parts:
            context_text = "\n\n" + "\n\n".join(context_parts)
            return base_prompt + context_text
        return base_prompt

    def send_chat_message(self):
        message = self.chat_input.text().strip()
        if not message:
            return

        if hasattr(self, '_api_call_thread') and self._api_call_thread and self._api_call_thread.isRunning():
            return

        self._set_ai_inputs_enabled(False)
        self._add_user_message(message)
        self.chat_input.clear()

        self._add_ai_streaming_message()

        self._add_to_history("user", message)
        
        # 添加用户消息到记忆（确保 memory_manager 已初始化）
        if hasattr(self, 'memory_manager') and self.memory_manager:
            self.memory_manager.add_memory(
                content=message,
                memory_type="auto",
                context={"source": "user_message"}
            )
        
        # 意图判断使用简洁的系统提示，不包含记忆和上下文
        system_prompt = "你是一个意图识别助手。请根据用户的输入判断意图类型，只返回JSON格式的结果。"

        self._pending_goal = message
        self._send_intent_check(message, system_prompt)
        return
    
    def _send_intent_check(self, goal, system_prompt):
        """意图判断（恢复原有逻辑）"""
        # 获取当前日期和时间
        from datetime import datetime
        import json
        
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_names[now.weekday()]
        
        # 获取当前任务列表
        pending_tasks = [t for t in self.task_manager.tasks if not t.completed]
        tasks_info = "\n".join([
            f"{i+1}. {t.name} (预计{t.estimated_minutes}分钟{f', 截止:{t.due_date}' if t.due_date else ''})"
            for i, t in enumerate(pending_tasks[:10])
        ])
        
        # 获取最近的对话历史（用于上下文判断）
        recent_history = ""
        if self.conversation_history:
            recent_messages = self.conversation_history[-4:]  # 最近4条消息
            for msg in recent_messages:
                role = "用户" if msg["role"] == "user" else "AI"
                content = msg["content"][:200]  # 截取前200字符
                recent_history += f"{role}: {content}\n"
        
        check_prompt = f"""用户说：「{goal}」

当前时间：{current_date} {weekday} {current_time}

当前任务列表：
{tasks_info if tasks_info else "暂无任务"}

最近对话历史：
{recent_history if recent_history else "无历史对话"}

请判断用户的意图，并严格按照以下JSON格式回复（不要添加任何解释）：

{{
  "intent": "意图类型"
}}

意图类型（intent）必须是以下之一：
1. "可以拆解" - 用户描述了一个**目标/任务/计划**，希望拆解成多个具体子任务。关键词：规划、安排、分解、拆解、准备、完成。通常句式是"我要/我想/帮我...".
2. "普通对话" - 用户在提问、聊天、咨询建议、询问时间、打招呼、表达感受等。注意：用户如果只是说"好的"、"可以"、"行"等简单确认词而没有明确任务方向，也归为此类。
3. "创建单个任务" - 用户想添加一个**简单的待办事项**，通常句式是"添加/记下/记录...任务"或直接说一个具体事项（如"买牛奶"、"给妈妈打电话"）。
4. "设定计时提醒" - 用户想要设定计时器、番茄钟、倒计时提醒、定时任务。
5. "创建提醒" - 用户想要创建一个定时提醒，关键词：提醒、闹钟、定时、几点。例如"提醒我明天8点开会"、"设置一个下午3点的提醒"。

**重要判断规则：**
- **上下文关联**：结合"最近对话历史"判断。如果AI刚刚问"是否需要设定计时"，用户回复"好的"，应判断为"设定计时提醒"
- **简洁回复处理**：当用户只回复"是的"、"好的"、"可以"、"行"、"需要"等简短确认词时，优先参考最近一条AI消息的内容来判断意图
- **否定回复**：用户说"不用"、"不需要"、"算了"等否定词，应判断为"普通对话"
- **模糊输入**：如果用户只说一个名词（如"跑步"、"学习"），优先判断为"创建单个任务"
- 如果用户说"设定计时"、"开始番茄钟"、"帮我计时"、"开始计时"等，应判断为"设定计时提醒"
- 如果用户只是确认时间规划但没有明确要求计时，判断为"普通对话"
- 如果用户明确说要"提醒"某事，判断为"创建提醒"
- **"我要..."表达**：用户说"我要考试"、"我要准备面试"、"我要复习"等，表示有一个目标，应判断为"可以拆解"
- **事件陈述**：用户说"我明天要考试"、"下周有面试"等，表示有一个重要事件，应判断为"可以拆解"（可以帮用户准备）

场景示例：
- 用户说"我要期中考试了" → "可以拆解"（用户有一个考试目标，需要准备）
- 用户说"准备明天的面试" → "可以拆解"（目标是准备面试，需要拆解）
- 用户说"我要复习英语" → "可以拆解"（用户有一个学习目标）
- 用户说"下周要交报告" → "可以拆解"（有一个任务目标，可以拆解步骤）
- 用户说"帮我查一下天气" → "普通对话"（只是查询信息）
- 用户说"记一下明天买牛奶" → "创建单个任务"（简单待办）
- 用户说"提醒我明天8点开会" → "创建提醒"（明确要提醒）
- 用户说"好的" + AI最近问"需要设定番茄钟吗" → "设定计时提醒"（上下文确认）
- 用户说"不用了谢谢" → "普通对话"（否定）

请严格按照JSON格式回复，不要添加任何其他内容。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": check_prompt}
        ]

        self._streaming_text = ""

        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message(self._streaming_text)
            except Exception as e:
                print(f"[_send_intent_check on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    # 注意：意图判断结果不保存到历史，避免上下文混乱

                    # 尝试解析JSON格式的响应
                    try:
                        import json
                        # 移除可能的markdown代码块标记
                        json_str = final_content.strip()
                        if json_str.startswith("```"):
                            json_str = json_str.split("\n", 1)[1] if "\n" in json_str else json_str
                        if json_str.endswith("```"):
                            json_str = json_str.rsplit("\n", 1)[0] if "\n" in json_str else json_str
                        json_str = json_str.strip()

                        response_data = json.loads(json_str)
                        intent = response_data.get("intent", "普通对话")

                        if intent == "可以拆解":
                            # 先询问用户是否要拆解
                            self._ask_to_create_tasks(goal, "拆解")
                        elif intent == "创建单个任务":
                            # 先询问用户是否要创建单个任务
                            self._ask_to_create_tasks(goal, "单个")
                        elif intent == "设定计时提醒":
                            # 设定计时提醒，自动启动番茄钟
                            self._handle_timer_intent(goal)
                        elif intent == "创建提醒":
                            # 创建提醒
                            self._create_reminder_from_intent(goal)
                        else:
                            # 普通对话，需要再次调用AI获取真正回复
                            self._do_normal_chat(goal)
                            return  # 不在这里设置enabled，让_do_normal_chat处理

                    except (json.JSONDecodeError, KeyError) as e:
                        # JSON解析失败，使用旧的字符串匹配方式
                        print(f"JSON解析失败: {e}, 使用字符串匹配")
                        if "可以拆解" in final_content:
                            # 先询问用户是否要拆解
                            self._ask_to_create_tasks(goal, "拆解")
                        elif "创建单个任务" in final_content:
                            # 先询问用户是否要创建单个任务
                            self._ask_to_create_tasks(goal, "单个")
                        elif "设定计时提醒" in final_content:
                            # 设定计时提醒
                            self._handle_timer_intent(goal)
                        elif "创建提醒" in final_content:
                            # 创建提醒
                            self._create_reminder_from_intent(goal)
                        else:
                            # 普通对话，需要再次调用AI获取真正回复
                            self._do_normal_chat(goal)
                            return  # 不在这里设置enabled，让_do_normal_chat处理
                else:
                    self._add_ai_message("抱歉，我没理解你的意思，请再说一次。")
            except Exception as e:
                print(f"[_send_intent_check on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_send_intent_check on_error] {e}")
            self._set_ai_inputs_enabled(True)

        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _create_single_task_from_intent(self, user_input):
        """从用户输入中提取单个任务信息并创建（使用AI智能提取）"""
        from datetime import datetime
        import json
        
        self._add_user_message(f"好的，帮我把「{user_input}」加入任务")
        self._set_ai_inputs_enabled(False)
        self._add_ai_streaming_message()

        # 使用简洁的系统提示，不包含任何历史记忆
        system_prompt = "你是一个专业的效率助手。请专注于用户当前的任务，不要参考之前的历史对话。"
        
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        # 获取所有可用标签
        all_tags = self.tag_manager.get_all_tags()
        preset_tags = self.tag_manager.get_preset_tags()
        
        # 构建标签说明
        tag_descriptions = """
可用标签分类：
- 任务类型：学习、工作、生活、娱乐、运动、阅读、编程
- 优先级：紧急、重要、日常、可选
- 时间：今日、本周、长期
- 状态：进行中、待开始、暂停
"""
        
        user_prompt = f"""请从用户的输入中提取任务信息。

当前日期：{current_date}，当前时间：{current_time}

用户输入：{user_input}

{tag_descriptions}

请严格按照以下JSON格式返回（不要添加任何解释）：
{{
  "task_name": "任务名称",
  "estimated_minutes": 预估分钟数,
  "due_date": "截止时间（YYYY-MM-DD HH:MM格式）或null",
  "tags": ["标签1", "标签2"]
}}

要求：
1. task_name: 提取核心任务名称，去掉"帮我"、"将"、"加入任务"等无关词汇
2. estimated_minutes: 根据任务性质合理预估时间（15-120分钟）
3. due_date: 
   - 如果用户指定了日期/时间，转换为YYYY-MM-DD HH:MM格式
   - 如果用户只说了日期没说时间，默认设为当天18:00
   - 如果没有指定截止时间，设为null
4. tags: 根据任务内容智能选择1-3个合适的标签，从可用标签中选择
   - 例如"写代码"可选"编程"、"工作"
   - 例如"跑步"可选"运动"、"生活"
   - 例如"复习考试"可选"学习"、"重要"
   - 如果任务很紧急，添加"紧急"标签
   - 如果是今天要做的，添加"今日"标签

示例：
用户输入："将拉屎在2026/4/27加入任务"
返回：{{"task_name": "拉屎", "estimated_minutes": 15, "due_date": "2026-04-27 18:00", "tags": ["生活", "日常"]}}

用户输入："明天下午3点开会"
返回：{{"task_name": "开会", "estimated_minutes": 60, "due_date": "明天日期 15:00", "tags": ["工作", "重要"]}}

只输出JSON，不要其他内容。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        self._streaming_text = ""
        
        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message("正在提取任务信息...\n" + self._streaming_text)
            except Exception as e:
                print(f"[_create_single_task_from_intent on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    try:
                        # 解析JSON
                        json_str = final_content.strip()
                        if json_str.startswith("```"):
                            lines = json_str.split("\n")
                            json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

                        task_data = json.loads(json_str)
                        task_name = task_data.get("task_name", "").strip()
                        estimated_minutes = max(5, min(180, int(task_data.get("estimated_minutes", 30))))
                        due_date = task_data.get("due_date")
                        tags = task_data.get("tags", [])

                        # 过滤有效标签
                        valid_tags = [t for t in tags if t in all_tags]

                        if due_date and due_date != "null":
                            due_str = due_date
                        else:
                            due_str = None

                        if task_name:
                            # 创建任务（带标签）
                            self.task_manager.add_task(task_name, estimated_minutes, source="ai", due_date=due_str, tags=valid_tags)
                            self.refresh_tasks()

                            due_info = f"，截止时间：{due_str}" if due_str else ""
                            tags_info = f"，标签：{', '.join(['#'+t for t in valid_tags])}" if valid_tags else ""
                            self._add_ai_message(f"✅ 已创建任务：「{task_name}」({estimated_minutes}分钟{due_info}{tags_info})")

                            # 添加任务创建记忆（确保 memory_manager 已初始化）
                            if hasattr(self, 'memory_manager') and self.memory_manager:
                                self.memory_manager.add_memory(
                                    content=f"创建任务：「{task_name}」{due_info}",
                                    memory_type="short_term",
                                    tags=["task_creation"],
                                    context={"source": "single_task", "task_name": task_name}
                                )
                        else:
                            self._add_ai_message("<font color='red'>未能识别任务名称，请重新描述</font>")

                    except json.JSONDecodeError as e:
                        self._add_ai_message(f"<font color='red'>JSON解析失败: {e}</font>\n原始响应：{final_content[:200]}")
                    except Exception as e:
                        self._add_ai_message(f"<font color='red'>创建任务失败: {e}</font>")
                else:
                    self._add_ai_message("<font color='red'>抱歉，未能提取任务信息</font>")
            except Exception as e:
                print(f"[_create_single_task_from_intent on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_create_single_task_from_intent on_error] {e}")
            self._set_ai_inputs_enabled(True)
        
        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _create_reminder_from_intent(self, user_input):
        """从用户输入中提取提醒信息并创建（使用AI智能提取）"""
        from datetime import datetime, timedelta
        import json

        self._add_user_message(f"好的，帮我创建提醒「{user_input}」")
        self._set_ai_inputs_enabled(False)
        self._add_ai_streaming_message()

        # 使用简洁的系统提示，不包含任何历史记忆
        system_prompt = "你是一个专业的效率助手。请专注于用户当前的提醒请求，不要参考之前的历史对话。"

        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_names[now.weekday()]

        user_prompt = f"""请从用户的输入中提取提醒信息。

当前日期：{current_date}，{weekday}，当前时间：{current_time}

用户输入：{user_input}

请严格按照以下JSON格式返回（不要添加任何解释）：
{{
  "title": "提醒标题",
  "remind_time": "提醒时间（YYYY-MM-DD HH:MM格式）",
  "description": "提醒描述（可选，没有则为空字符串）",
  "repeat_type": "重复类型"
}}

要求：
1. title: 提取提醒的核心标题，简洁明了（如"开会"、"吃药"、"运动"）
2. remind_time: 提醒时间
   - 如果用户指定了具体日期和时间，直接转换为 YYYY-MM-DD HH:MM 格式
   - 如果用户说"明天"，则设为明天的日期
   - 如果用户说"后天"，则设为后天的日期
   - 如果用户只说了时间没说日期（如"8点"），默认设为今天
   - 如果用户说的时间已经过了今天，自动设为明天
   - 如果没有指定具体时间，默认设为上午9:00
3. description: 提醒的详细描述（如果有额外信息）
4. repeat_type: 重复类型，必须是以下之一：
   - "none" - 不重复（默认）
   - "daily" - 每天重复
   - "weekly" - 每周重复
   - "monthly" - 每月重复

示例：
用户输入："提醒我明天8点开会"
返回：{{"title": "开会", "remind_time": "2026-04-30 08:00", "description": "", "repeat_type": "none"}}

用户输入："每天早上7点提醒我吃药"
返回：{{"title": "吃药", "remind_time": "2026-04-29 07:00", "description": "每天按时吃药", "repeat_type": "daily"}}

用户输入："后天下午3点提醒我参加面试"
返回：{{"title": "参加面试", "remind_time": "2026-05-01 15:00", "description": "面试", "repeat_type": "none"}}

只输出JSON，不要其他解释。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        self._streaming_text = ""

        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message(self._streaming_text)
            except Exception as e:
                print(f"[_create_reminder_from_intent on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    try:
                        # 移除可能的markdown代码块标记
                        json_str = final_content.strip()
                        if json_str.startswith("```"):
                            lines = json_str.split("\n")
                            json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
                        json_str = json_str.strip()

                        data = json.loads(json_str)
                        title = data.get("title", "提醒")
                        remind_time_str = data.get("remind_time", "")
                        description = data.get("description", "")
                        repeat_type = data.get("repeat_type", "none")

                        # 解析提醒时间
                        try:
                            remind_time = datetime.strptime(remind_time_str, "%Y-%m-%d %H:%M")
                        except:
                            # 解析失败，默认1小时后
                            remind_time = now + timedelta(hours=1)

                        # 创建提醒
                        self.reminder_manager.add_reminder(title, remind_time, description, repeat_type)

                        # 刷新提醒列表
                        if hasattr(self, 'reminder_tab'):
                            self.reminder_tab.refresh_reminders()

                        # 格式化时间显示
                        time_str = remind_time.strftime("%Y-%m-%d %H:%M")
                        repeat_text = {
                            "none": "",
                            "daily": "（每天重复）",
                            "weekly": "（每周重复）",
                            "monthly": "（每月重复）"
                        }.get(repeat_type, "")

                        self._add_to_history("assistant", f"已创建提醒「{title}」")
                        self._add_ai_message(
                            f"<font color='green'><b>✅ 提醒创建成功！</b></font>\n\n"
                            f"⏰ <b>{title}</b>\n"
                            f"📅 {time_str} {repeat_text}\n"
                            f"{f'📝 {description}' if description else ''}"
                        )

                    except json.JSONDecodeError as e:
                        self._add_ai_message(f"<font color='red'>JSON解析失败: {e}</font>\n原始响应：{final_content[:200]}")
                    except Exception as e:
                        self._add_ai_message(f"<font color='red'>创建提醒失败: {e}</font>")
                else:
                    self._add_ai_message("<font color='red'>抱歉，未能提取提醒信息</font>")
            except Exception as e:
                print(f"[_create_reminder_from_intent on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_create_reminder_from_intent on_error] {e}")
            self._set_ai_inputs_enabled(True)

        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _handle_timer_intent(self, user_input):
        """处理设定计时提醒的意图"""
        import re
        from datetime import datetime
        
        # 获取未完成任务
        pending_tasks = [t for t in self.task_manager.tasks if not t.completed]
        
        # 尝试从用户输入中提取时间（分钟）
        time_match = re.search(r'(\d+)\s*(分钟|小时|h|hour)', user_input)
        if time_match:
            time_value = int(time_match.group(1))
            unit = time_match.group(2)
            if unit in ['小时', 'h', 'hour']:
                time_value *= 60
        else:
            # 默认25分钟（番茄钟标准时长）
            time_value = 25
        
        # 尝试匹配任务名称
        matched_task = None
        for task in pending_tasks:
            # 简单匹配：检查任务名是否在用户输入中
            if task.name in user_input:
                matched_task = task
                break
        
        # 如果用户只是确认（如"好的"、"可以"、"行"），自动选择第一个任务
        confirmation_words = ["好的", "可以", "行", "是的", "需要", "嗯", "好", "ok", "OK", "Ok"]
        is_confirmation = any(word in user_input for word in confirmation_words) and len(user_input.strip()) <= 10
        
        if matched_task:
            # 找到匹配的任务，使用任务的时间
            task_name = matched_task.name
            task_minutes = matched_task.estimated_minutes
            self._add_ai_message(f"好的，我来帮你启动「{task_name}」的番茄钟计时（{task_minutes}分钟）⏰\n\n专注模式已开启，加油！💪")
            # 启动番茄钟
            dialog = PomodoroDialog(task_minutes, task_name, self)
            dialog.finished.connect(lambda duration, name: self.on_pomodoro_finished(matched_task, duration))
            dialog.exec_()
        elif is_confirmation and pending_tasks:
            # 用户确认，自动选择第一个任务
            first_task = pending_tasks[0]
            self._add_ai_message(f"好的，我来帮你启动「{first_task.name}」的番茄钟计时（{first_task.estimated_minutes}分钟）⏰\n\n专注模式已开启，加油！💪")
            dialog = PomodoroDialog(first_task.estimated_minutes, first_task.name, self)
            dialog.finished.connect(lambda duration, name: self.on_pomodoro_finished(first_task, duration))
            dialog.exec_()
        elif pending_tasks:
            # 没有匹配到任务，自动选择第一个任务
            first_task = pending_tasks[0]
            self._add_ai_message(f"好的，我来帮你启动「{first_task.name}」的番茄钟计时（{first_task.estimated_minutes}分钟）⏰\n\n专注模式已开启，加油！💪")
            dialog = PomodoroDialog(first_task.estimated_minutes, first_task.name, self)
            dialog.finished.connect(lambda duration, name: self.on_pomodoro_finished(first_task, duration))
            dialog.exec_()
        else:
            # 没有任务，启动默认计时器
            self._add_ai_message(f"好的，我来帮你启动一个 {time_value} 分钟的计时器 ⏰\n\n专注模式已开启，加油！💪")
            dialog = PomodoroDialog(time_value, "专注时间", self)
            dialog.exec_()
        
        self._set_ai_inputs_enabled(True)

    def _do_normal_chat(self, message):
        self._add_ai_streaming_message()

        system_prompt = self._get_context_prompt()

        messages = [{"role": "system", "content": system_prompt}]
        # 使用最近的历史（不包括当前消息，因为当前消息已经在历史中了）
        for h in self.conversation_history[-8:]:
            messages.append({"role": h["role"], "content": h["content"]})

        self._streaming_text = ""

        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message(self._streaming_text)
            except Exception as e:
                print(f"[_do_normal_chat on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    self._add_to_history("assistant", final_content)
                    rendered = render_latex(final_content)
                    self._add_ai_message(rendered)

                    # 添加AI回复到记忆（确保 memory_manager 已初始化）
                    if hasattr(self, 'memory_manager') and self.memory_manager:
                        self.memory_manager.add_memory(
                            content=final_content,
                            memory_type="auto",
                            tags=["ai_response"],
                            context={"source": "ai_message"}
                        )
            except Exception as e:
                print(f"[_do_normal_chat on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_do_normal_chat on_error] {e}")
            self._set_ai_inputs_enabled(True)

        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _ask_to_create_tasks(self, goal, task_type="拆解"):
        """
        询问用户是否要创建任务
        
        Args:
            goal: 目标内容
            task_type: 任务类型（"拆解" 或 "单个"）
        """
        # 创建确认按钮
        btn = QPushButton("✅ 确认创建")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        if task_type == "拆解":
            btn.clicked.connect(lambda: self._create_tasks_from_goal(goal))
            label_text = f"🤖 AI 建议将「{goal}」拆解成多个任务，是否创建？"
        else:
            btn.clicked.connect(lambda: self._create_single_task_from_intent(goal))
            label_text = f"🤖 AI 建议创建任务「{goal}」，是否创建？"
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #666; font-size: 13px;")
        label.setWordWrap(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(label)
        layout.addWidget(btn)
        
        self._add_ai_message("", with_action_button=container)
    
    def _show_create_tasks_button(self, goal):
        btn = QPushButton("🤖 创建任务")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn.clicked.connect(lambda: self._create_tasks_from_goal(goal))

        label = QLabel("这是一个目标，要拆解成任务吗？")
        label.setStyleSheet("color: #666; font-size: 13px;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(label)
        layout.addWidget(btn)

        self._add_ai_message("", with_action_button=container)

    def _create_tasks_from_goal(self, goal):
        self._add_user_message(f"好的，帮我把「{goal}」拆解成任务")
        self._set_ai_inputs_enabled(False)

        self._add_ai_streaming_message()

        # 使用简洁的系统提示，不包含任何历史记忆
        system_prompt = "你是一个专业的效率助手。请专注于用户当前的目标，不要参考之前的历史对话。"

        # 获取当前日期和时间
        from datetime import datetime
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        # 获取所有可用标签
        all_tags = self.tag_manager.get_all_tags()
        
        # 构建标签说明
        tag_descriptions = """
可用标签分类：
- 任务类型：学习、工作、生活、娱乐、运动、阅读、编程
- 优先级：紧急、重要、日常、可选
- 时间：今日、本周、长期
- 状态：进行中、待开始、暂停
"""

        user_prompt = f"""请将以下目标拆解成 3~6 个具体的子任务。

当前日期：{current_date}，当前时间：{current_time}

{tag_descriptions}

返回格式必须是严格的 JSON 数组：
[{{"name": "任务名称", "estimated_minutes": 预估分钟数, "due_date": "截止时间或null", "tags": ["标签1", "标签2"]}}]

要求：
1. name: 任务名称要具体可执行，不要笼统
2. estimated_minutes: 根据任务难度合理预估时间（15-120分钟）
   - 简单任务（如整理笔记）：15-30分钟
   - 中等任务（如做题、阅读）：30-60分钟
   - 复杂任务（如写报告、复习章节）：60-120分钟
3. due_date: 截止时间（格式：YYYY-MM-DD HH:MM）
   - 如果用户指定了截止时间，按用户要求设置
   - 否则，合理分配到未来几天，从今天开始安排
   - 每个任务的截止时间要错开，避免堆积
4. tags: 根据任务内容智能选择1-2个合适的标签，从可用标签中选择
   - 例如"写代码"可选"编程"、"工作"
   - 例如"跑步"可选"运动"、"生活"
   - 例如"复习考试"可选"学习"、"重要"

目标：{goal}

只输出 JSON 数组，不要其他解释。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        self._streaming_text = ""
        self._goal_for_tasks = goal

        def on_chunk(chunk, accumulated):
            try:
                self._streaming_text += chunk
                self._update_streaming_message("正在分析目标...\n" + self._streaming_text)
            except Exception as e:
                print(f"[_create_tasks_from_goal on_chunk] {e}")

        def on_complete(final_content):
            try:
                self._finish_streaming_message()
                if final_content:
                    self._parse_and_create_tasks(final_content, goal)
                else:
                    self._add_ai_message("<font color='red'>抱歉，未能解析任务列表</font>")
            except Exception as e:
                print(f"[_create_tasks_from_goal on_complete] {e}")
                try:
                    self._add_ai_message(f"<font color='red'>处理出错: {e}</font>")
                except Exception:
                    pass
            self._set_ai_inputs_enabled(True)

        def on_error(error_msg):
            try:
                self._finish_streaming_message()
                self._add_ai_message(f"<font color='red'>错误: {error_msg}</font>")
            except Exception as e:
                print(f"[_create_tasks_from_goal on_error] {e}")
            self._set_ai_inputs_enabled(True)

        self._api_call_thread = AsyncAPICallStream(messages)
        self._api_call_thread.chunk_ready.connect(on_chunk)
        self._api_call_thread.stream_finished.connect(on_complete)
        self._api_call_thread.error_occurred.connect(on_error)
        self._api_call_thread.start()

    def _parse_and_create_tasks(self, json_str, goal):
        try:
            json_str = json_str.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            tasks = json.loads(json_str)
            if not isinstance(tasks, list):
                raise ValueError("返回格式不是数组")

            # 获取所有有效标签（预设+自定义）
            all_tags = self.tag_manager.get_all_tags()
            preset_tags = self.tag_manager.get_preset_tags()

            added_count = 0
            task_info_list = []
            total_minutes = 0
            has_due_date = False
            first_due_date = None
            first_task_name = ""
            for task_data in tasks:
                name = task_data.get("name", "").strip()
                minutes = max(5, min(180, int(task_data.get("estimated_minutes", 30))))
                total_minutes += minutes
                due_date = task_data.get("due_date")
                if due_date and (due_date == "null" or due_date is None):
                    due_date = None

                # 记录第一个有截止时间的任务信息
                if due_date and not has_due_date:
                    has_due_date = True
                    first_due_date = due_date
                    first_task_name = name

                # 获取标签并过滤有效标签
                tags = task_data.get("tags", [])
                valid_tags = []
                for t in tags:
                    # 精确匹配
                    if t in all_tags:
                        valid_tags.append(t)
                    # 尝试去除空格后匹配
                    elif t.strip() in all_tags:
                        valid_tags.append(t.strip())
                    # 如果不在预设标签中，自动添加为自定义标签
                    elif t.strip():
                        self.tag_manager.add_custom_tag(t.strip())
                        valid_tags.append(t.strip())

                if name:
                    self.task_manager.add_task(name, minutes, source="ai", due_date=due_date, tags=valid_tags)
                    added_count += 1
                    due_info = f" 📅 {due_date}" if due_date else ""
                    tags_info = f" 🏷️ {', '.join(['#'+t for t in valid_tags])}" if valid_tags else ""
                    task_info_list.append(f"• {name} ⏱ {minutes}分钟{due_info}{tags_info}")

            self.refresh_tasks()
            if hasattr(self, 'stats_tab'):
                self.stats_tab.refresh_stats()

            total_hours = total_minutes // 60
            remain_mins = total_minutes % 60
            time_str = f"{total_hours}小时{remain_mins}分钟" if total_hours > 0 else f"{total_minutes}分钟"

            self._add_to_history("assistant", f"已将「{goal}」拆解为 {added_count} 个任务")

            # 如果有截止时间，显示创建提醒按钮
            if has_due_date and first_due_date:
                self._show_tasks_with_reminder_option(goal, added_count, time_str, task_info_list, first_task_name, first_due_date)
            else:
                self._add_ai_message(
                    f"<font color='green'><b>✅ 成功!</b></font> 已创建 {added_count} 个任务，预计总时长 {time_str}：\n\n" +
                    "\n".join(task_info_list)
                )

            # 添加任务创建记忆（确保 memory_manager 已初始化）
            if hasattr(self, 'memory_manager') and self.memory_manager:
                self.memory_manager.add_memory(
                    content=f"目标「{goal}」已拆解为{added_count}个任务，预计总时长{time_str}",
                    memory_type="long_term",
                    tags=["task_creation", "goal_decomposition"],
                    context={"source": "task_creation", "task_count": added_count}
                )

        except json.JSONDecodeError as e:
            self._add_ai_message(f"<font color='red'><b>❌ JSON解析失败:</b> {e}</font>\n原始响应：{json_str[:200]}")
        except Exception as e:
            self._add_ai_message(f"<font color='red'><b>❌ 处理失败:</b> {e}</font>")

    def _show_tasks_with_reminder_option(self, goal, task_count, time_str, task_info_list, task_name, due_date):
        """显示任务创建结果，并提供创建提醒的选项"""
        # 创建容器
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(10)

        # 任务信息
        info_label = QLabel(
            f"<font color='green'><b>✅ 成功!</b></font> 已创建 {task_count} 个任务，预计总时长 {time_str}：\n\n" +
            "\n".join(task_info_list)
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.PlainText)
        layout.addWidget(info_label)

        # 提醒询问
        ask_label = QLabel(f"\n💡 任务「{task_name}」有截止时间，需要创建提醒吗？")
        ask_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(ask_label)

        # 按钮行
        btn_layout = QHBoxLayout()

        # 创建提醒按钮
        create_btn = QPushButton("⏰ 创建提醒")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8FAB;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FF6B8A;
            }
        """)
        create_btn.clicked.connect(lambda: self._quick_create_reminder(task_name, due_date))
        btn_layout.addWidget(create_btn)

        # 稍后按钮
        later_btn = QPushButton("暂不需要")
        later_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #666;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #BDBDBD;
            }
        """)
        btn_layout.addWidget(later_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._add_ai_message("", with_action_button=container)

    def _quick_create_reminder(self, task_name, due_date):
        """快速创建提醒（从任务截止时间）"""
        from datetime import datetime

        try:
            # 解析截止时间
            if isinstance(due_date, str):
                remind_time = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            else:
                remind_time = due_date

            # 创建提醒
            self.reminder_manager.add_reminder(
                title=f"任务提醒：{task_name}",
                remind_time=remind_time,
                description=f"任务「{task_name}」即将到期，请及时完成！"
            )

            # 刷新提醒列表
            if hasattr(self, 'reminder_tab'):
                self.reminder_tab.refresh_reminders()

            time_str = remind_time.strftime("%Y-%m-%d %H:%M")
            self._add_ai_message(
                f"<font color='green'><b>✅ 提醒已创建！</b></font>\n\n"
                f"⏰ 任务「{task_name}」\n"
                f"📅 提醒时间：{time_str}"
            )
        except Exception as e:
            self._add_ai_message(f"<font color='red'>创建提醒失败: {e}</font>")

    def _add_to_history(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        # 保留最近 10 条对话历史，确保上下文连贯
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def _on_ai_result(self, result, chat_output):
        if chat_output:
            rendered = render_latex(result)
            chat_output.append(f"<b>AI:</b> {rendered}")

    def _on_ai_error(self, error_msg, chat_output):
        if chat_output:
            chat_output.append(f"<font color='red'><b>AI:</b> 错误: {error_msg}</font>")

    def _set_ai_inputs_enabled(self, enabled):
        if hasattr(self, 'send_btn'):
            self.send_btn.setEnabled(enabled)
        if hasattr(self, 'chat_input'):
            self.chat_input.setEnabled(enabled)
        if hasattr(self, 'voice_btn'):
            self.voice_btn.setEnabled(enabled)

    def ai_breakdown(self):
        self.tab_widget.setCurrentIndex(0)
        self._add_ai_message("💡 请在下方输入您的目标，例如：「准备数学考试」或「完成项目报告」，我会帮您拆解成具体任务。")

    def generate_summary(self):
        self.tab_widget.setCurrentIndex(0)
        today_tasks = self.task_manager.get_today_tasks()
        completed_tasks = self.task_manager.get_today_completed()

        if not today_tasks:
            self._add_ai_message("📭 今天还没有任务记录，添加一些任务后再来生成总结吧！")
            return

        message = f"📊 今日进度：已完成 {len(completed_tasks)}/{len(today_tasks)} 个任务\n\n"
        message += "✅ 已完成任务：\n"
        for t in completed_tasks:
            message += f"  • {t.name}\n"

        pending = [t for t in today_tasks if not t.completed]
        if pending:
            message += "\n⏳ 未完成任务：\n"
            for t in pending:
                message += f"  • {t.name}\n"

        self._add_ai_message(message)

    def voice_input(self):
        if hasattr(self, '_voice_thread') and self._voice_thread.isRunning():
            self._voice_thread.stop()
            self._restore_voice_btn()
            return

        try:
            from voice_input import VoiceRecognitionThread, VoiceInputDialog, get_default_model_path
        except ImportError as e:
            self._add_ai_message(f"🎤 导入语音模块失败: {e}")
            return

        model_path = get_default_model_path()
        if not model_path or not os.path.exists(model_path):
            self._add_ai_message("🎤 未找到语音模型文件\n请下载 vosk-model-small-cn-0.22 到 models 目录")
            return

        self.voice_btn.setText("🔴")
        self.voice_btn.set_tint("#FF4D4D", "#FFFFFF")

        self._voice_dialog = VoiceInputDialog(self)
        self._voice_thread = VoiceRecognitionThread(model_path)

        def on_result(text):
            self._restore_voice_btn()
            self._voice_dialog.set_result(text)
            self._voice_dialog.accept()

        def on_error(msg):
            self._restore_voice_btn()
            self._voice_dialog.set_status("错误: " + msg)
            self._add_ai_message(f"<font color='red'>🎤 识别错误: {msg}</font>")

        self._voice_thread.result_ready.connect(on_result)
        self._voice_thread.error_occurred.connect(on_error)

        def on_dialog_accepted():
            self._restore_voice_btn()
            if hasattr(self, '_voice_thread') and self._voice_thread.isRunning():
                self._voice_thread.stop()
            text = self._voice_dialog.recognized_text
            if text:
                self.chat_input.setText(text)

        def on_dialog_rejected():
            self._restore_voice_btn()
            if hasattr(self, '_voice_thread') and self._voice_thread.isRunning():
                self._voice_thread.stop()

        self._voice_dialog.accepted.connect(on_dialog_accepted)
        self._voice_dialog.rejected.connect(on_dialog_rejected)

        from PyQt5.QtCore import QTimer
        self._voice_timeout_timer = QTimer()
        self._voice_timeout_timer.setSingleShot(True)
        self._voice_timeout_timer.timeout.connect(lambda: (self._voice_thread.stop(), self._voice_dialog.reject(), self._restore_voice_btn(), self._add_ai_message("🎤 识别超时")))
        self._voice_timeout_timer.start(30000)

        self._voice_thread.start()
        self._voice_dialog.show()

    def _restore_voice_btn(self):
        if hasattr(self, '_voice_timeout_timer'):
            self._voice_timeout_timer.stop()
        if hasattr(self, 'voice_btn'):
            self.voice_btn.setText("🎤")
            self.voice_btn.set_tint(*getattr(self, "_voice_btn_tint", ("#FFFFFF", "#555555")))


def _exception_hook(exc_type, exc_value, exc_tb):
    """全局异常钩子 — 防止 Qt 信号槽中未捕获的异常导致闪退"""
    import traceback
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[FATAL] 未捕获的异常:\n{msg}", file=sys.stderr)
    # 写入数据目录下的日志文件以便事后分析
    log_error(msg)
    # 尝试弹出错误对话框（GUI 环境）
    try:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "😵 程序遇到错误",
            f"发生了未预期的错误，请将以下信息反馈给开发者：\n\n{exc_value}")
    except Exception:
        pass


if __name__ == "__main__":
    # 记录启动路径信息（调试用）
    log_error(
        f"STARTUP frozen={getattr(sys, 'frozen', False)}, "
        f"exec={sys.executable if getattr(sys, 'frozen', False) else 'N/A'}\n"
        f"tasks.json path: {get_data_path('tasks.json')} "
        f"(exists={os.path.exists(get_data_path('tasks.json'))})"
    )

    sys.excepthook = _exception_hook
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setStyle("Fusion")

    window = MainWindow()
    fade_in_window(window)
    window.show()
    sys.exit(app.exec_())
