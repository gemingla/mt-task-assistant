"""标签管理与添加/编辑标签对话框"""
from ui_common import *  # noqa: F401,F403


class TagManagerDialog(QDialog):
    """标签管理对话框"""
    
    def __init__(self, tag_manager, task_manager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.task_manager = task_manager
        self.setWindowTitle("🏷️ 标签管理")
        self.setFixedSize(600, 500)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("🏷️ 标签管理")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #333;")
        layout.addWidget(title)
        
        # 预设标签区域
        preset_group = QGroupBox("预设标签")
        preset_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        # 使用 QWidget 容器来放置标签
        preset_container = QWidget()
        preset_container_layout = QVBoxLayout(preset_container)
        preset_container_layout.setContentsMargins(10, 15, 10, 10)
        preset_container_layout.setSpacing(8)
        
        # 当前行的布局
        current_row_layout = QHBoxLayout()
        current_row_layout.setSpacing(8)
        row_width = 0
        max_width = 550  # 每行最大宽度
        
        preset_tags = self.tag_manager.get_preset_tags()
        for tag, color in preset_tags.items():
            tag_label = QLabel(f"  #{tag}  ")
            tag_label.setStyleSheet(f"""
                background-color: {self._lighten_color(color, 0.85)};
                color: {color};
                border-radius: 12px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
            """)
            tag_label.setFixedHeight(26)
            tag_label.adjustSize()
            
            # 检查是否需要换行
            tag_width = tag_label.width()
            if row_width + tag_width > max_width and row_width > 0:
                current_row_layout.addStretch()
                preset_container_layout.addLayout(current_row_layout)
                current_row_layout = QHBoxLayout()
                current_row_layout.setSpacing(8)
                row_width = 0
            
            current_row_layout.addWidget(tag_label)
            row_width += tag_width + 8
        
        # 添加最后一行
        current_row_layout.addStretch()
        preset_container_layout.addLayout(current_row_layout)
        
        preset_group_layout = QVBoxLayout(preset_group)
        preset_group_layout.setContentsMargins(0, 0, 0, 0)
        preset_group_layout.addWidget(preset_container)
        
        layout.addWidget(preset_group)
        
        # 自定义标签区域
        custom_group = QGroupBox("自定义标签")
        custom_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        custom_layout = QVBoxLayout(custom_group)
        
        # 标签列表
        self.custom_tag_list = QListWidget()
        self.custom_tag_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                background-color: #FAFAFA;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
        """)
        self.refresh_custom_tags()
        custom_layout.addWidget(self.custom_tag_list)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加标签")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self.add_custom_tag)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ 编辑标签")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        edit_btn.clicked.connect(self.edit_custom_tag)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ 删除标签")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_btn.clicked.connect(self.delete_custom_tag)
        btn_layout.addWidget(delete_btn)
        
        custom_layout.addLayout(btn_layout)
        layout.addWidget(custom_group)
        
        # 标签统计
        stats_group = QGroupBox("标签统计")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        stats_layout = QVBoxLayout(stats_group)
        
        stats_text = QTextBrowser()
        stats_text.setMaximumHeight(100)
        stats_text.setStyleSheet("border: 1px solid #E0E0E0; border-radius: 5px; background-color: #FAFAFA;")
        self.update_stats(stats_text)
        stats_layout.addWidget(stats_text)
        
        layout.addWidget(stats_group)
    
    def create_tag_widget(self, tag, color, editable=True):
        """创建标签显示组件"""
        widget = QWidget()
        widget.setFixedHeight(28)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # 颜色指示器
        color_indicator = QLabel()
        color_indicator.setFixedSize(14, 14)
        color_indicator.setStyleSheet(f"""
            background-color: {color};
            border-radius: 7px;
        """)
        layout.addWidget(color_indicator)
        
        # 标签名称
        tag_label = QLabel(f"#{tag}")
        tag_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        layout.addWidget(tag_label)
        layout.addStretch()  # 添加弹性空间防止拉伸
        
        return widget
    
    def refresh_custom_tags(self):
        """刷新自定义标签列表"""
        self.custom_tag_list.clear()
        custom_tags = self.tag_manager.get_custom_tags()
        
        for tag, color in custom_tags.items():
            item = QListWidgetItem()
            widget = self.create_tag_widget(tag, color)
            item.setSizeHint(widget.sizeHint())
            self.custom_tag_list.addItem(item)
            self.custom_tag_list.setItemWidget(item, widget)
    
    def add_custom_tag(self):
        """添加自定义标签"""
        dialog = AddTagDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            tag_name, color = dialog.get_result()
            if tag_name:
                self.tag_manager.add_custom_tag(tag_name, color)
                self.refresh_custom_tags()
                QMessageBox.information(self, "成功", f"标签「{tag_name}」已添加！")
    
    def edit_custom_tag(self):
        """编辑自定义标签"""
        current_item = self.custom_tag_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要编辑的标签！")
            return
        
        # 获取当前标签名称（从列表中获取）
        row = self.custom_tag_list.row(current_item)
        custom_tags = list(self.tag_manager.get_custom_tags().keys())
        if row < len(custom_tags):
            old_tag = custom_tags[row]
            old_color = self.tag_manager.get_tag_color(old_tag)
            
            dialog = AddTagDialog(self, old_tag, old_color)
            if dialog.exec_() == QDialog.Accepted:
                new_tag, new_color = dialog.get_result()
                if new_tag:
                    # 删除旧标签
                    self.tag_manager.remove_custom_tag(old_tag)
                    # 添加新标签
                    self.tag_manager.add_custom_tag(new_tag, new_color)
                    self.refresh_custom_tags()
                    QMessageBox.information(self, "成功", f"标签已更新！")
    
    def delete_custom_tag(self):
        """删除自定义标签"""
        current_item = self.custom_tag_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要删除的标签！")
            return
        
        # 获取当前标签名称
        row = self.custom_tag_list.row(current_item)
        custom_tags = list(self.tag_manager.get_custom_tags().keys())
        if row < len(custom_tags):
            tag_name = custom_tags[row]
            
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除标签「{tag_name}」吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.tag_manager.remove_custom_tag(tag_name)
                self.refresh_custom_tags()
                QMessageBox.information(self, "成功", f"标签「{tag_name}」已删除！")
    
    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """将颜色变浅（用于背景色）"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#F5F5F5"
    
    def update_stats(self, stats_text):
        """更新标签统计"""
        stats = self.tag_manager.get_tag_statistics(self.task_manager)
        
        if not stats:
            stats_text.setHtml("<p style='color: #999; text-align: center;'>暂无标签统计数据</p>")
            return
        
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background-color: rgba(128, 128, 128, 0.18);'><th style='padding: 8px; text-align: left;'>标签</th><th style='padding: 8px; text-align: center;'>任务数量</th></tr>"
        
        for tag, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            color = self.tag_manager.get_tag_color(tag)
            html += f"<tr><td style='padding: 8px;'><span style='color: {color}; font-weight: bold;'>#{tag}</span></td><td style='padding: 8px; text-align: center;'>{count}</td></tr>"
        
        html += "</table>"
        stats_text.setHtml(html)


class AddTagDialog(QDialog):
    """添加/编辑标签对话框"""
    
    def __init__(self, parent=None, tag_name="", color="#757575"):
        super().__init__(parent)
        self.setWindowTitle("添加标签" if not tag_name else "编辑标签")
        self.setFixedSize(350, 200)
        self.setStyleSheet("background-color: #FFFFFF;")
        
        self.tag_name = tag_name
        self.color = color
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标签名称
        name_label = QLabel("标签名称：")
        name_label.setStyleSheet("font-size: 13px; color: #333; font-weight: bold;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit(self.tag_name)
        self.name_input.setPlaceholderText("输入标签名称...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #FFB6C1;
            }
        """)
        layout.addWidget(self.name_input)
        
        # 标签颜色
        color_label = QLabel("标签颜色：")
        color_label.setStyleSheet("font-size: 13px; color: #333; font-weight: bold;")
        layout.addWidget(color_label)
        
        self.color_btn = QPushButton()
        self.color_btn.setFixedHeight(40)
        self.update_color_btn()
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def update_color_btn(self):
        """更新颜色按钮样式"""
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color};
                border: 2px solid #E0E0E0;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                border: 2px solid #999;
            }}
        """)
    
    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(self.color), self, "选择标签颜色")
        if color.isValid():
            self.color = color.name()
            self.update_color_btn()
    
    def get_result(self):
        """获取结果"""
        return self.name_input.text().strip(), self.color
