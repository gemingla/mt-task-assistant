import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream, QIODevice


def get_style_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, "style.qss")


def load_stylesheet(app=None):
    style_path = get_style_path()
    
    if os.path.exists(style_path):
        try:
            with open(style_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
            
            if app:
                app.setStyleSheet(stylesheet)
            
            return stylesheet
        except Exception as e:
            print(f"加载样式表失败: {e}")
            return ""
    else:
        print(f"样式表文件不存在: {style_path}")
        return ""


def apply_global_styles(app):
    base_style = load_stylesheet(app)
    
    additional_style = """
        /* 确保所有窗口都有正确的字体 */
        * {
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        }
    """
    
    if app.styleSheet():
        app.setStyleSheet(app.styleSheet() + additional_style)
    else:
        app.setStyleSheet(additional_style)
    
    return app.styleSheet()


class StyleManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if StyleManager._initialized:
            return
        StyleManager._initialized = True
        
        self._stylesheet = ""
        self._theme_colors = {
            'primary': '#FF8FAB',
            'primary_light': '#FFB3CC',
            'primary_dark': '#FF6B8A',
            'background': '#F5F5F5',
            'surface': '#FFFFFF',
            'text_primary': '#333333',
            'text_secondary': '#666666',
            'text_hint': '#999999',
            'divider': '#E0E0E0',
            'success': '#4CAF50',
            'warning': '#FFA726',
            'error': '#FF5252',
        }
    
    @property
    def colors(self):
        return self._theme_colors.copy()
    
    def get_color(self, name):
        return self._theme_colors.get(name, '#000000')
    
    def load_style(self, app):
        self._stylesheet = load_stylesheet(app)
        return self._stylesheet
    
    def add_style(self, widget, style):
        current = widget.styleSheet()
        widget.setStyleSheet(current + "\n" + style)
    
    def set_property(self, widget, prop_name, prop_value):
        widget.setProperty(prop_name, prop_value)
        widget.style().unpolish(widget)
        widget.style().polish(widget)


style_manager = StyleManager()
