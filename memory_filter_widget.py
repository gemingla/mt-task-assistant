"""
智能记忆过滤面板
展示记忆过滤效果和质量报告
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QFrame, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class MemoryFilterWidget(QWidget):
    """智能记忆过滤面板"""
    
    def __init__(self, memory_manager, parent=None):
        super().__init__(parent)
        self.memory_manager = memory_manager
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("🧠 智能记忆过滤系统")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1976D2; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # 1. 过滤统计
        stats_group = self._create_stats_group()
        scroll_layout.addWidget(stats_group)
        
        # 2. 记忆质量报告
        quality_group = self._create_quality_group()
        scroll_layout.addWidget(quality_group)
        
        # 3. 过滤规则说明
        rules_group = self._create_rules_group()
        scroll_layout.addWidget(rules_group)
        
        # 4. 操作按钮
        buttons_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 刷新数据")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_data)
        buttons_layout.addWidget(refresh_btn)
        
        reset_btn = QPushButton("🗑️ 重置统计")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        reset_btn.clicked.connect(self._reset_stats)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        scroll_layout.addLayout(buttons_layout)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def _create_stats_group(self) -> QGroupBox:
        """创建过滤统计组"""
        group = QGroupBox("📊 过滤统计")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #E3F2FD;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #1976D2;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # 获取统计数据
        stats = self.memory_manager.get_filter_stats()
        
        # 总检查次数
        total_label = QLabel(f"总检查次数：{stats['total_checked']} 次")
        total_label.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(total_label)
        
        # 记忆次数
        remember_label = QLabel(f"✅ 记忆次数：{stats['should_remember']} 次")
        remember_label.setFont(QFont("Microsoft YaHei", 12))
        remember_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(remember_label)
        
        # 跳过次数
        skip_label = QLabel(f"❌ 跳过次数：{stats['should_skip']} 次")
        skip_label.setFont(QFont("Microsoft YaHei", 12))
        skip_label.setStyleSheet("color: #F44336;")
        layout.addWidget(skip_label)
        
        # 敏感信息拦截
        sensitive_label = QLabel(f"🔒 敏感信息拦截：{stats['sensitive_blocked']} 次")
        sensitive_label.setFont(QFont("Microsoft YaHei", 12))
        sensitive_label.setStyleSheet("color: #FF9800;")
        layout.addWidget(sensitive_label)
        
        # 记忆率
        rate_label = QLabel(f"📈 记忆率：{stats['remember_rate']:.1f}%")
        rate_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        rate_label.setStyleSheet("color: #1976D2; margin-top: 10px;")
        layout.addWidget(rate_label)
        
        # 进度条
        progress = QProgressBar()
        progress.setValue(int(stats['remember_rate']))
        progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        layout.addWidget(progress)
        
        return group
    
    def _create_quality_group(self) -> QGroupBox:
        """创建记忆质量报告组"""
        group = QGroupBox("📈 记忆质量报告")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #E8F5E9;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #4CAF50;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # 获取质量报告
        report = self.memory_manager.get_memory_quality_report()
        
        # 总记忆数
        total_label = QLabel(f"总记忆数：{report['total_memories']} 条")
        total_label.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(total_label)
        
        # 短期/长期记忆
        type_layout = QHBoxLayout()
        short_label = QLabel(f"短期记忆：{report['short_term_count']} 条")
        short_label.setStyleSheet("color: #FF9800;")
        type_layout.addWidget(short_label)
        
        long_label = QLabel(f"长期记忆：{report['long_term_count']} 条")
        long_label.setStyleSheet("color: #4CAF50;")
        type_layout.addWidget(long_label)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # 平均质量
        avg_quality = report['average_quality']
        quality_label = QLabel(f"平均质量：{avg_quality:.2f}")
        quality_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        
        # 根据质量设置颜色
        if avg_quality >= 0.7:
            quality_label.setStyleSheet("color: #4CAF50;")
        elif avg_quality >= 0.4:
            quality_label.setStyleSheet("color: #FF9800;")
        else:
            quality_label.setStyleSheet("color: #F44336;")
        
        layout.addWidget(quality_label)
        
        # 质量分布
        dist = report['quality_distribution']
        dist_label = QLabel(
            f"质量分布：\n"
            f"  🌟 高质量：{dist['high']} 条\n"
            f"  👍 中等质量：{dist['medium']} 条\n"
            f"  ⚠️ 低质量：{dist['low']} 条"
        )
        dist_label.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(dist_label)
        
        return group
    
    def _create_rules_group(self) -> QGroupBox:
        """创建过滤规则说明组"""
        group = QGroupBox("📋 过滤规则说明")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #FFF3E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #FF9800;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        rules_text = """
🧠 智能记忆过滤系统会自动判断内容是否值得记忆：

✅ 会记忆的内容：
  • 包含任务、作业、考试等关键词
  • 包含时间信息（明天、下周等）
  • 包含学习相关内容
  • 包含具体数字和信息
  • 用户明确要求记住的内容

❌ 会跳过的内容：
  • 简单的问候和寒暄（你好、谢谢等）
  • 简单的确认（好的、嗯、哦等）
  • 内容过短（少于3个字符）
  • 包含敏感信息（密码、手机号等）

🔒 隐私保护：
  • 自动检测并过滤敏感信息
  • 敏感信息会被标记或脱敏处理

💡 设计理念：
  • 提高记忆质量，避免垃圾信息
  • 保护用户隐私
  • 培养批判性思维
        """
        
        rules_label = QLabel(rules_text)
        rules_label.setFont(QFont("Microsoft YaHei", 11))
        rules_label.setWordWrap(True)
        rules_label.setStyleSheet("padding: 10px;")
        layout.addWidget(rules_label)
        
        return group
    
    def _refresh_data(self):
        """刷新数据"""
        # 重新加载界面
        QMessageBox.information(
            self,
            "✅ 刷新成功",
            "数据已更新！\n\n请关闭此窗口后重新打开查看最新数据。"
        )
        
        # 关闭父对话框
        parent_dialog = self.parent()
        while parent_dialog and not isinstance(parent_dialog, QWidget):
            parent_dialog = parent_dialog.parent()
        
        if parent_dialog:
            parent_dialog.close()
    
    def _reset_stats(self):
        """重置统计数据"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有统计数据吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.memory_manager.reset_filter_stats()
            QMessageBox.information(self, "✅ 重置成功", "统计数据已重置！")
            
            # 关闭父对话框
            parent_dialog = self.parent()
            while parent_dialog and not isinstance(parent_dialog, QWidget):
                parent_dialog = parent_dialog.parent()
            
            if parent_dialog:
                parent_dialog.close()
