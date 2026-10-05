"""AI 记忆管理对话框"""
from ui_common import *  # noqa: F401,F403


class MemoryManagementDialog(QDialog):
    """记忆管理对话框"""
    
    def __init__(self, memory_manager, parent=None):
        super().__init__(parent)
        self.memory_manager = memory_manager
        self.setWindowTitle("🧠 记忆管理")
        self.resize(900, 700)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索记忆...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #E0E0E0;
                border-radius: 20px;
                font-size: 13px;
                background-color: #FAFAFA;
            }
            QLineEdit:focus {
                border-color: #FFB6C1;
                background-color: white;
            }
        """)
        self.search_input.textChanged.connect(self.filter_memories)
        toolbar_layout.addWidget(self.search_input, stretch=1)
        
        # 类型筛选
        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部记忆", "短期记忆", "长期记忆"])
        self.type_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 15px;
                border: 2px solid #E0E0E0;
                border-radius: 15px;
                background-color: #FAFAFA;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #FFB6C1;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.type_combo.currentTextChanged.connect(self.filter_memories)
        toolbar_layout.addWidget(self.type_combo)
        
        # 全选按钮
        select_all_btn = QPushButton("☑️ 全选")
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        select_all_btn.clicked.connect(self.select_all)
        toolbar_layout.addWidget(select_all_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_list)
        toolbar_layout.addWidget(refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 批量操作工具栏
        batch_toolbar = QHBoxLayout()
        
        # 批量删除按钮
        batch_delete_btn = QPushButton("🗑️ 批量删除")
        batch_delete_btn.setStyleSheet("""
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
        batch_delete_btn.clicked.connect(self.show_batch_delete_menu)
        batch_toolbar.addWidget(batch_delete_btn)
        
        batch_toolbar.addStretch()
        layout.addLayout(batch_toolbar)
        
        # 统计信息
        stats = self.memory_manager.get_memory_stats()
        stats_label = QLabel(
            f"📊 总计: {stats['total_memories']} 条 | "
            f"短期: {stats['short_term_count']} 条 | "
            f"长期: {stats['long_term_count']} 条"
        )
        stats_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #F5F5F5;
                border-radius: 8px;
                font-size: 12px;
                color: #666;
            }
        """)
        layout.addWidget(stats_label)
        
        # 记忆列表
        self.memory_list = QListWidget()
        self.memory_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FAFAFA;
                padding: 5px;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 10px;
                margin: 3px;
            }
            QListWidget::item:selected {
                background-color: #FFF0F3;
                border-color: #FFB6C1;
            }
            QListWidget::item:hover {
                background-color: #F5F5F5;
            }
        """)
        self.memory_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.memory_list)
        
        # 底部操作按钮
        buttons_layout = QHBoxLayout()
        
        # 删除选中
        delete_btn = QPushButton("🗑️ 删除选中")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 25px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected)
        buttons_layout.addWidget(delete_btn)
        
        # 清空短期记忆
        clear_short_btn = QPushButton("清空短期记忆")
        clear_short_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 25px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        clear_short_btn.clicked.connect(self.clear_short_term)
        buttons_layout.addWidget(clear_short_btn)
        
        # 导出记忆
        export_btn = QPushButton("📤 导出记忆")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 25px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        export_btn.clicked.connect(self.export_memories)
        buttons_layout.addWidget(export_btn)
        
        # 导入记忆
        import_btn = QPushButton("📥 导入记忆")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 25px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        import_btn.clicked.connect(self.import_memories)
        buttons_layout.addWidget(import_btn)
        
        buttons_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px 30px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # 加载记忆列表
        self.load_memories()
    
    def load_memories(self):
        """加载记忆列表"""
        self.memory_list.clear()
        
        # 获取所有记忆
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        
        # 按创建时间排序（最新的在前）
        all_memories.sort(key=lambda m: m.created_at, reverse=True)
        
        for memory in all_memories:
            item = QListWidgetItem()
            
            # 格式化显示
            type_icon = "🟠" if memory.memory_type == "short_term" else "🟢"
            time_str = memory.created_at.strftime("%Y-%m-%d %H:%M")
            importance_stars = "⭐" * int(memory.importance * 5)
            
            display_text = f"{type_icon} [{time_str}] {memory.content[:100]}{'...' if len(memory.content) > 100 else ''}"
            
            item.setText(display_text)
            item.setData(Qt.UserRole, memory.id)  # 存储记忆ID
            
            # 设置工具提示（完整内容）
            tooltip = (
                f"类型: {'短期记忆' if memory.memory_type == 'short_term' else '长期记忆'}\n"
                f"重要性: {importance_stars} ({memory.importance:.2f})\n"
                f"创建时间: {time_str}\n"
                f"访问次数: {memory.access_count}\n"
                f"标签: {', '.join(memory.tags) if memory.tags else '无'}\n\n"
                f"完整内容:\n{memory.content}"
            )
            item.setToolTip(tooltip)
            
            self.memory_list.addItem(item)
    
    def filter_memories(self):
        """筛选记忆"""
        search_text = self.search_input.text().lower()
        type_filter = self.type_combo.currentText()
        
        for i in range(self.memory_list.count()):
            item = self.memory_list.item(i)
            memory_id = item.data(Qt.UserRole)
            
            # 查找对应的记忆
            all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
            memory = next((m for m in all_memories if m.id == memory_id), None)
            
            if memory:
                # 搜索过滤
                matches_search = search_text in memory.content.lower() if search_text else True
                
                # 类型过滤
                matches_type = True
                if type_filter == "短期记忆":
                    matches_type = memory.memory_type == "short_term"
                elif type_filter == "长期记忆":
                    matches_type = memory.memory_type == "long_term"
                
                item.setHidden(not (matches_search and matches_type))
    
    def delete_selected(self):
        """删除选中的记忆"""
        selected_items = self.memory_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要删除的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_items)} 条记忆吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            for item in selected_items:
                memory_id = item.data(Qt.UserRole)
                
                # 从短期记忆中删除
                self.memory_manager.short_term_memories = [
                    m for m in self.memory_manager.short_term_memories if m.id != memory_id
                ]
                
                # 从长期记忆中删除
                self.memory_manager.long_term_memories = [
                    m for m in self.memory_manager.long_term_memories if m.id != memory_id
                ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(selected_items)} 条记忆！")
    
    def clear_short_term(self):
        """清空短期记忆"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有短期记忆吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.memory_manager.clear_memories("short_term")
            self.refresh_list()
            QMessageBox.information(self, "成功", "已清空所有短期记忆！")
    
    def select_all(self):
        """全选可见的记忆"""
        visible_count = 0
        for i in range(self.memory_list.count()):
            item = self.memory_list.item(i)
            if not item.isHidden():
                item.setSelected(True)
                visible_count += 1
        
        QMessageBox.information(self, "提示", f"已选中 {visible_count} 条可见记忆！")
    
    def show_batch_delete_menu(self):
        """显示批量删除菜单"""
        from PyQt5.QtWidgets import QMenu
        from datetime import datetime, timedelta
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #FFEBEE;
                color: #D32F2F;
            }
        """)
        
        # 按时间删除
        time_menu = menu.addMenu("📅 按时间删除")
        
        delete_7_days = time_menu.addAction("删除 7 天前的记忆")
        delete_7_days.triggered.connect(lambda: self.delete_by_time(7))
        
        delete_30_days = time_menu.addAction("删除 30 天前的记忆")
        delete_30_days.triggered.connect(lambda: self.delete_by_time(30))
        
        delete_90_days = time_menu.addAction("删除 90 天前的记忆")
        delete_90_days.triggered.connect(lambda: self.delete_by_time(90))
        
        delete_custom = time_menu.addAction("自定义天数...")
        delete_custom.triggered.connect(self.delete_by_custom_time)
        
        # 按重要性删除
        importance_menu = menu.addMenu("⭐ 按重要性删除")
        
        delete_low = importance_menu.addAction("删除低重要性记忆 (< 0.3)")
        delete_low.triggered.connect(lambda: self.delete_by_importance(0.3, "below"))
        
        delete_medium = importance_menu.addAction("删除中等重要性记忆 (< 0.6)")
        delete_medium.triggered.connect(lambda: self.delete_by_importance(0.6, "below"))
        
        keep_high = importance_menu.addAction("只保留高重要性记忆 (>= 0.7)")
        keep_high.triggered.connect(lambda: self.delete_by_importance(0.7, "keep_above"))
        
        menu.addSeparator()
        
        # 删除筛选结果
        delete_filtered = menu.addAction("🔍 删除当前筛选结果")
        delete_filtered.triggered.connect(self.delete_filtered)
        
        # 删除未访问的记忆
        delete_unused = menu.addAction("📊 删除从未访问的记忆")
        delete_unused.triggered.connect(self.delete_never_accessed)
        
        menu.addSeparator()
        
        # 清空所有
        clear_all = menu.addAction("⚠️ 清空所有记忆")
        clear_all.triggered.connect(self.clear_all_memories)
        
        # 显示菜单
        menu.exec_(self.cursor().pos())
    
    def delete_by_time(self, days: int):
        """删除指定天数前的记忆"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 统计要删除的数量
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        to_delete = [m for m in all_memories if m.created_at < cutoff_date]
        
        if not to_delete:
            QMessageBox.information(self, "提示", f"没有 {days} 天前的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {days} 天前的所有记忆吗？\n\n"
            f"将删除 {len(to_delete)} 条记忆\n"
            f"（创建时间早于 {cutoff_date.strftime('%Y-%m-%d %H:%M')}）\n\n"
            f"此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            self.memory_manager.short_term_memories = [
                m for m in self.memory_manager.short_term_memories if m.created_at >= cutoff_date
            ]
            self.memory_manager.long_term_memories = [
                m for m in self.memory_manager.long_term_memories if m.created_at >= cutoff_date
            ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(to_delete)} 条记忆！")
    
    def delete_by_custom_time(self):
        """自定义时间删除"""
        from PyQt5.QtWidgets import QInputDialog
        from datetime import datetime, timedelta
        
        days, ok = QInputDialog.getInt(
            self,
            "自定义天数",
            "请输入要删除多少天前的记忆：",
            value=30,
            min=1,
            max=365
        )
        
        if ok:
            self.delete_by_time(days)
    
    def delete_by_importance(self, threshold: float, mode: str):
        """按重要性删除记忆
        
        Args:
            threshold: 重要性阈值
            mode: "below" 删除低于阈值, "keep_above" 保留高于阈值
        """
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        
        if mode == "below":
            to_delete = [m for m in all_memories if m.importance < threshold]
            message = f"确定要删除重要性低于 {threshold:.1f} 的所有记忆吗？\n\n将删除 {len(to_delete)} 条记忆\n此操作不可恢复！"
        else:  # keep_above
            to_delete = [m for m in all_memories if m.importance < threshold]
            message = f"确定要只保留重要性 >= {threshold:.1f} 的记忆吗？\n\n将删除 {len(to_delete)} 条记忆\n此操作不可恢复！"
        
        if not to_delete:
            QMessageBox.information(self, "提示", "没有符合条件的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            self.memory_manager.short_term_memories = [
                m for m in self.memory_manager.short_term_memories if m.importance >= threshold
            ]
            self.memory_manager.long_term_memories = [
                m for m in self.memory_manager.long_term_memories if m.importance >= threshold
            ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(to_delete)} 条记忆！")
    
    def delete_filtered(self):
        """删除当前筛选结果"""
        # 获取当前可见的记忆项
        visible_items = []
        for i in range(self.memory_list.count()):
            item = self.memory_list.item(i)
            if not item.isHidden():
                visible_items.append(item)
        
        if not visible_items:
            QMessageBox.warning(self, "提示", "当前没有可见的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除当前筛选结果吗？\n\n"
            f"将删除 {len(visible_items)} 条记忆\n"
            f"此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            for item in visible_items:
                memory_id = item.data(Qt.UserRole)
                
                self.memory_manager.short_term_memories = [
                    m for m in self.memory_manager.short_term_memories if m.id != memory_id
                ]
                self.memory_manager.long_term_memories = [
                    m for m in self.memory_manager.long_term_memories if m.id != memory_id
                ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(visible_items)} 条记忆！")
    
    def delete_never_accessed(self):
        """删除从未访问的记忆"""
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        to_delete = [m for m in all_memories if m.access_count == 0]
        
        if not to_delete:
            QMessageBox.information(self, "提示", "没有从未访问的记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除从未访问的记忆吗？\n\n"
            f"将删除 {len(to_delete)} 条记忆\n"
            f"此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除记忆
            self.memory_manager.short_term_memories = [
                m for m in self.memory_manager.short_term_memories if m.access_count > 0
            ]
            self.memory_manager.long_term_memories = [
                m for m in self.memory_manager.long_term_memories if m.access_count > 0
            ]
            
            # 保存并刷新
            self.memory_manager._save_memories()
            self.memory_manager._rebuild_indexes()
            self.refresh_list()
            
            QMessageBox.information(self, "成功", f"已删除 {len(to_delete)} 条记忆！")
    
    def clear_all_memories(self):
        """清空所有记忆"""
        all_memories = self.memory_manager.short_term_memories + self.memory_manager.long_term_memories
        
        if not all_memories:
            QMessageBox.information(self, "提示", "当前没有任何记忆！")
            return
        
        reply = QMessageBox.question(
            self,
            "⚠️ 危险操作",
            f"确定要清空所有记忆吗？\n\n"
            f"将删除全部 {len(all_memories)} 条记忆\n"
            f"此操作不可恢复！\n\n"
            f"建议先导出备份！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 二次确认
            confirm = QMessageBox.warning(
                self,
                "最后确认",
                "真的要清空所有记忆吗？\n此操作无法撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                self.memory_manager.clear_memories()
                self.refresh_list()
                QMessageBox.information(self, "成功", "已清空所有记忆！")
    
    
    def export_memories(self):
        """导出记忆"""
        from PyQt5.QtWidgets import QFileDialog
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出记忆",
            f"memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                self.memory_manager.export_memories(filename)
                QMessageBox.information(self, "成功", f"记忆已导出到：\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败：\n{str(e)}")
    
    def import_memories(self):
        """导入记忆"""
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "导入记忆",
            "",
            "JSON文件 (*.json)"
        )
        
        if filename:
            reply = QMessageBox.question(
                self,
                "导入方式",
                "选择导入方式：\n\n"
                "Yes - 合并现有记忆\n"
                "No - 替换现有记忆",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Cancel:
                try:
                    merge = (reply == QMessageBox.Yes)
                    self.memory_manager.import_memories(filename, merge=merge)
                    self.refresh_list()
                    QMessageBox.information(self, "成功", "记忆导入成功！")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导入失败：\n{str(e)}")
    
    def refresh_list(self):
        """刷新列表"""
        self.load_memories()
        self.filter_memories()
