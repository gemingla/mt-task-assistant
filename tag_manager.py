"""
标签管理器 - 管理任务标签、预设标签和标签颜色
"""
import json
import os
from typing import Dict, List, Tuple
from utils import get_data_path

TAGS_FILE = get_data_path("tags.json")

# 预设标签及其颜色
PRESET_TAGS = {
    # 任务类型
    "学习": "#2196F3",      # 蓝色
    "工作": "#FF9800",      # 橙色
    "生活": "#4CAF50",      # 绿色
    "娱乐": "#9C27B0",      # 紫色
    "运动": "#FF5722",      # 深橙色
    "阅读": "#795548",      # 棕色
    "编程": "#00BCD4",      # 青色
    
    # 优先级
    "紧急": "#F44336",      # 红色
    "重要": "#FFC107",      # 黄色
    "日常": "#607D8B",      # 蓝灰色
    "可选": "#9E9E9E",      # 灰色
    
    # 时间
    "今日": "#E91E63",      # 粉色
    "本周": "#009688",      # 青绿色
    "长期": "#3F51B5",      # 靛蓝色
    
    # 状态
    "进行中": "#FF9800",    # 橙色
    "待开始": "#03A9F4",    # 浅蓝色
    "暂停": "#9E9E9E",      # 灰色
}


class TagManager:
    """标签管理器"""
    
    def __init__(self):
        self.custom_tags = {}  # 用户自定义标签
        self.load_tags()
    
    def load_tags(self):
        """加载用户自定义标签"""
        if os.path.exists(TAGS_FILE):
            try:
                with open(TAGS_FILE, 'r', encoding='utf-8') as f:
                    self.custom_tags = json.load(f)
            except Exception as e:
                print(f"加载标签失败: {e}")
                self.custom_tags = {}
        else:
            self.custom_tags = {}
    
    def save_tags(self):
        """保存用户自定义标签"""
        try:
            with open(TAGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.custom_tags, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存标签失败: {e}")
    
    def get_tag_color(self, tag: str) -> str:
        """获取标签颜色"""
        # 优先使用预设标签颜色
        if tag in PRESET_TAGS:
            return PRESET_TAGS[tag]
        # 其次使用自定义标签颜色
        if tag in self.custom_tags:
            return self.custom_tags[tag]
        # 默认颜色
        return "#757575"  # 灰色
    
    def set_tag_color(self, tag: str, color: str):
        """设置标签颜色（仅对自定义标签有效）"""
        if tag not in PRESET_TAGS:
            self.custom_tags[tag] = color
            self.save_tags()
    
    def add_custom_tag(self, tag: str, color: str = "#757575"):
        """添加自定义标签"""
        if tag and tag not in PRESET_TAGS:
            self.custom_tags[tag] = color
            self.save_tags()
    
    def remove_custom_tag(self, tag: str):
        """删除自定义标签"""
        if tag in self.custom_tags:
            del self.custom_tags[tag]
            self.save_tags()
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签（预设+自定义）"""
        all_tags = list(PRESET_TAGS.keys()) + list(self.custom_tags.keys())
        return sorted(set(all_tags))
    
    def get_preset_tags(self) -> Dict[str, str]:
        """获取预设标签"""
        return PRESET_TAGS.copy()
    
    def get_custom_tags(self) -> Dict[str, str]:
        """获取自定义标签"""
        return self.custom_tags.copy()
    
    def is_preset_tag(self, tag: str) -> bool:
        """判断是否为预设标签"""
        return tag in PRESET_TAGS
    
    def get_tag_statistics(self, task_manager) -> Dict[str, int]:
        """获取标签统计信息"""
        stats = {}
        for task in task_manager.tasks:
            if hasattr(task, 'tags'):
                for tag in task.tags:
                    stats[tag] = stats.get(tag, 0) + 1
        return stats
    
    def get_tag_style(self, tag: str, clickable: bool = False) -> str:
        """获取标签的CSS样式
        
        Args:
            tag: 标签名称
            clickable: 是否可点击（添加悬停效果）
        """
        color = self.get_tag_color(tag)
        bg_color = self._lighten_color(color, 0.85)
        
        hover_style = ""
        if clickable:
            hover_style = f"""
                QLabel:hover {{
                    background-color: {self._lighten_color(color, 0.7)};
                    border: 2px solid {color};
                }}
            """
        
        return f"""
            QLabel {{
                background-color: {bg_color};
                color: {color};
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            {hover_style}
        """
    
    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """将颜色变浅（用于背景色）"""
        try:
            # 移除 # 号
            hex_color = hex_color.lstrip('#')
            # 转换为RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # 变浅
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)
            
            # 确保在有效范围内
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#F5F5F5"  # 默认浅灰色
