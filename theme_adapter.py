"""
主题适配器：让散落在各处、写死了浅色样式的控件与对话框自动适配玻璃主题

- transform_qss(): 纯函数，按当前主题改写样式表中的颜色
    浅色主题：近白色的不透明底色 → 半透明白（透出玻璃背景）
    深色主题：深色文字 → 浅色文字；浅色底色 → 半透明暗玻璃；浅色边框 → 淡白边
  饱和度高的颜色（主题粉、绿色按钮、红色警告等）与 white 文字保持不变。
- ThemeAdapter: 安装在 QApplication 上的事件过滤器。控件显示或样式表变化时，
  以“原始样式表”为准重新改写，因此切换主题可以无损来回切换；
  自定义对话框首次显示时自动包上动态玻璃背景。
"""

import re

from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QDialog, QMessageBox, QFileDialog, QColorDialog, QInputDialog,
    QProgressDialog, QWizard, QVBoxLayout, QApplication, QMenu,
)

# ==================== 样式表改写（纯函数） ====================

_COLOR_TOKEN = re.compile(
    r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|\bwhite\b|\bblack\b"
    r"|rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*(?:,\s*[\d.]+\s*)?\)", re.IGNORECASE)
_DECLARATION = re.compile(r"(?<![\w-])([a-z-]+)\s*:\s*([^;{}]+)", re.IGNORECASE)

DARK_TEXT = "#F2F2F7"
DARK_MUTED = "rgba(255, 255, 255, 0.62)"


def _parse(token):
    """解析颜色；rgba() 的透明度可写成 0-1 或 0-255"""
    if token.lower().startswith("rgb"):
        parts = [float(x) for x in re.findall(r"[\d.]+", token)]
        color = QColor(int(parts[0]), int(parts[1]), int(parts[2]))
        if len(parts) == 4:
            alpha = parts[3]
            color.setAlphaF(alpha if alpha <= 1 else alpha / 255)
        return color
    color = QColor(token)
    return color if color.isValid() else None


def _is_translucent(token):
    return token.lower().startswith("rgba")


def _is_neutral(color, max_saturation=0.25):
    return color.hslSaturationF() <= max_saturation


DARK_COLORED_TEXT_LIGHTNESS = 0.74


def _map_text(token, dark):
    color = _parse(token)
    if not dark or color is None or _is_translucent(token):
        return token
    lightness = color.lightnessF()
    if not _is_neutral(color, 0.35):
        # 彩色文字保持色相，只把偏暗的提亮，保证在暗玻璃上可读
        if lightness >= DARK_COLORED_TEXT_LIGHTNESS - 0.12:
            return token
        hue, sat, _, _ = color.getHslF()
        return QColor.fromHslF(max(hue, 0.0), min(sat, 0.85), DARK_COLORED_TEXT_LIGHTNESS).name()
    if lightness < 0.42:
        return DARK_TEXT
    if lightness < 0.75:
        return DARK_MUTED
    return token


def _has_solid_colored_background(body):
    """规则块自身有不透明的深色/彩色底（如绿色按钮）时，其文字颜色是针对该底色设计的，不应改写"""
    for match in _DECLARATION.finditer(body):
        if match.group(1).lower() not in ("background", "background-color"):
            continue
        for token in _COLOR_TOKEN.findall(match.group(2)):
            color = _parse(token)
            if color is not None and color.alphaF() >= 0.5 and color.lightnessF() < 0.85:
                return True
    return False


def _map_background(token, dark):
    color = _parse(token)
    if color is None or color.lightnessF() < 0.85 or color.alphaF() < 0.2:
        return token  # 深色/彩色底（按钮等）与几乎透明的底保持不变
    r, g, b = color.red(), color.green(), color.blue()
    if dark:
        if _is_neutral(color):
            return f"rgba(255, 255, 255, {0.06 + 0.08 * color.alphaF():.2f})"
        return f"rgba({r}, {g}, {b}, 0.16)"
    if _is_translucent(token):
        return token  # 浅色主题下已是半透明的保持原样
    return f"rgba({r}, {g}, {b}, 0.62)"


def _map_border(token, dark):
    color = _parse(token)
    if not dark or color is None or color.lightnessF() < 0.8 or not _is_neutral(color) or color.alphaF() < 0.2:
        return token
    return "rgba(255, 255, 255, 0.16)"


_PROPERTY_MAPPERS = {
    "color": _map_text,
    "background": _map_background,
    "background-color": _map_background,
    "alternate-background-color": _map_background,
}


def _mapper_for(prop):
    prop = prop.lower()
    if prop in _PROPERTY_MAPPERS:
        return _PROPERTY_MAPPERS[prop]
    if prop.startswith("border") and "radius" not in prop and "width" not in prop and "style" not in prop:
        return _map_border
    return None


def _transform_body(body, dark):
    keep_text = dark and _has_solid_colored_background(body)

    def repl_declaration(match):
        prop, value = match.group(1), match.group(2)
        mapper = _mapper_for(prop)
        if mapper is None or (keep_text and mapper is _map_text):
            return match.group(0)
        new_value = _COLOR_TOKEN.sub(lambda m: mapper(m.group(0), dark), value)
        return match.group(0).replace(value, new_value, 1)

    return _DECLARATION.sub(repl_declaration, body)


def transform_qss(qss, dark):
    """按主题改写样式表中的颜色（逐个规则块处理）；不认识的属性与颜色保持原样"""
    if not qss:
        return qss
    if "{" not in qss:
        return _transform_body(qss, dark)
    return re.sub(r"\{([^{}]*)\}", lambda m: "{" + _transform_body(m.group(1), dark) + "}", qss)


# ==================== 事件过滤器 ====================

_ORIG = "_ta_original_qss"
_OUT = "_ta_output_qss"
_GLASSED = "_ta_glassed"

# 系统/标准对话框结构复杂，不做玻璃包装（但仍会改写其中控件的颜色）
_SKIP_GLASS_DIALOGS = (QMessageBox, QFileDialog, QColorDialog, QInputDialog, QProgressDialog, QWizard)


class ThemeAdapter(QObject):
    def __init__(self, app, main_window):
        super().__init__(app)
        self._main_window = main_window
        self._theme = {}
        self._dark = False
        self._busy = False
        app.installEventFilter(self)

    # ---------- 公共接口 ----------

    def set_theme(self, theme):
        from glass_effects import glass_palette
        self._theme = dict(theme)
        self._dark = glass_palette(theme)["dark"]
        for widget in QApplication.allWidgets():
            if self._in_scope(widget):
                self.adapt(widget, force=True)
            if widget.property(_GLASSED):
                self._retheme_glass_dialog(widget)

    def adapt(self, widget, force=False):
        """以控件的原始样式表为准，按当前主题改写"""
        if self._busy:
            return
        current = widget.styleSheet()
        if not current and widget.property(_ORIG) is None:
            return
        if current != widget.property(_OUT) or widget.property(_ORIG) is None:
            # 代码里重新设置过样式表：把它当作新的原始样式
            widget.setProperty(_ORIG, current)
        elif not force:
            return
        output = transform_qss(widget.property(_ORIG), self._dark)
        widget.setProperty(_OUT, output)
        if output != current:
            self._busy = True
            try:
                widget.setStyleSheet(output)
            finally:
                self._busy = False

    # ---------- 事件处理 ----------

    def eventFilter(self, obj, event):
        etype = event.type()
        if etype in (QEvent.Show, QEvent.StyleChange) and not self._busy and isinstance(obj, QWidget):
            try:
                if isinstance(obj, QDialog) and etype == QEvent.Show and obj.isWindow():
                    self._glassify_dialog(obj)
                if self._in_scope(obj):
                    self.adapt(obj)
                    if etype == QEvent.Show and obj.isWindow():
                        for child in obj.findChildren(QWidget):
                            self.adapt(child)
            except RuntimeError:
                pass  # 控件已被销毁
        return False

    def _in_scope(self, widget):
        """只处理属于本应用主窗口的控件（菜单除外，菜单由全局样式控制）"""
        if isinstance(widget, QMenu) or widget is self._main_window or widget.property("ta_skip"):
            return False
        window = widget.window()
        main = self._main_window
        while window is not None:
            if window is main:
                return True
            parent = window.parentWidget()
            window = parent.window() if parent is not None else None
        return False

    # ---------- 对话框玻璃化 ----------

    def _glassify_dialog(self, dialog):
        if dialog.property(_GLASSED) or isinstance(dialog, _SKIP_GLASS_DIALOGS):
            return
        if not self._in_scope(dialog) or dialog.layout() is None:
            return
        if dialog.windowFlags() & 0x00000800:  # 无边框小弹窗（如任务卡片里的时间编辑）保持原样
            return
        from glass_effects import AuroraBackground, GlassPanel, glass_palette

        dialog.setProperty(_GLASSED, True)
        original_size = dialog.size()  # Show 事件时尺寸已确定
        # 包装前测量内容需要的尺寸（包装后新容器尚未布局，测不到）
        content_hint = dialog.sizeHint().expandedTo(dialog.minimumSizeHint())
        old_layout = dialog.layout()
        content = QWidget()
        content.setObjectName("glassDialogContent")
        content.setLayout(old_layout)  # 把原布局及其中的控件整体移入 content

        aurora = AuroraBackground()
        panel = GlassPanel(radius=16, sheen=False)
        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(aurora)
        aurora_layout = QVBoxLayout(aurora)
        aurora_layout.setContentsMargins(10, 10, 10, 10)
        aurora_layout.addWidget(panel)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(4, 4, 4, 4)
        panel_layout.addWidget(content)

        dialog._glass_aurora, dialog._glass_panel = aurora, panel
        aurora.set_animated(self._main_window.aurora.is_animated()
                            if hasattr(self._main_window, "aurora") else True)
        self._retheme_glass_dialog(dialog)

        # 在原尺寸基础上加上玻璃边距（宽、高分别处理固定/可变），且不小于内容实际需要的尺寸
        # （部分对话框写死的固定尺寸本来就小于内容，Qt 之前会自动撑大）
        margin = 28
        width = max(original_size.width(), content_hint.width()) + margin
        height = max(original_size.height(), content_hint.height()) + margin
        if dialog.minimumWidth() == dialog.maximumWidth():
            dialog.setFixedWidth(width)
        if dialog.minimumHeight() == dialog.maximumHeight():
            dialog.setFixedHeight(height)
        dialog.resize(width, height)

        # 对话框自身的整体底色（裸声明会作用到所有子控件）改为透明，由玻璃背景接管
        own = dialog.property(_ORIG) if dialog.property(_ORIG) is not None else dialog.styleSheet()
        stripped = _strip_dialog_background(own)
        output = transform_qss(stripped, self._dark)
        dialog.setProperty(_ORIG, stripped)
        dialog.setProperty(_OUT, output)
        self._busy = True
        try:
            dialog.setStyleSheet(output)
        finally:
            self._busy = False

    def _retheme_glass_dialog(self, dialog):
        from glass_effects import glass_palette
        aurora = getattr(dialog, "_glass_aurora", None)
        if aurora is None:
            return
        aurora.set_theme(self._theme)
        dialog._glass_panel.set_theme(glass_palette(self._theme))


def _strip_dialog_background(qss):
    """去掉对话框样式表里作用于自身/所有子控件的底色，保留其它规则"""
    if not qss:
        return qss
    if "{" not in qss:  # 裸声明，如 "background-color: #FAFAFA;"
        return re.sub(r"background(-color)?\s*:\s*[^;]+;?", "", qss)

    def clean_block(match):
        selector, body = match.group(1), match.group(2)
        targets = [s.strip() for s in selector.split(",")]
        if any(t in ("QDialog", "QWidget", "*") or t.startswith("QDialog#") for t in targets):
            body = re.sub(r"background(-color)?\s*:\s*[^;]+;?", "", body)
        return f"{selector}{{{body}}}"

    return re.sub(r"([^{}]+)\{([^{}]*)\}", clean_block, qss)
