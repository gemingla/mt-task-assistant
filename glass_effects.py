"""
动态玻璃效果模块
- AuroraBackground: 流动极光背景（主题色光斑缓慢漂移 + 鼠标跟随光晕 + 磨砂颗粒）
- GlassPanel: 毛玻璃面板（半透明填充 + 顶部高光 + 渐变描边 + 悬停发光 + 周期性流光）
- GlassTabWidget: 带滑动玻璃指示器的标签页，切换时淡出旧页面
- SlidingPill: 分段控件的滑动高亮块
- fade_in_window: 窗口启动淡入

全部使用 QPainter 自绘，不依赖 QGraphicsEffect（避免子控件渲染异常）。
"""

import math
import random

from PyQt5.QtCore import (
    Qt, QTimer, QElapsedTimer, QPointF, QRectF, QRect, QVariantAnimation,
    QPropertyAnimation, QEasingCurve, QEvent, QObject,
)
from PyQt5.QtGui import (
    QColor, QPainter, QImage, QPixmap, QRadialGradient, QLinearGradient,
    QPainterPath, QPen, QBrush, QCursor,
)
from PyQt5.QtWidgets import QWidget, QFrame, QTabBar, QTabWidget


# ==================== 颜色工具 ====================

def _qcolor(c):
    return c if isinstance(c, QColor) else QColor(c)


def is_dark_color(c):
    c = _qcolor(c)
    return (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255 < 0.5


def mix(c1, c2, t):
    """按比例 t 将 c1 混合到 c2"""
    c1, c2 = _qcolor(c1), _qcolor(c2)
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t),
        int(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
    )


def shift_hue(c, degrees, sat_scale=1.0, light_scale=1.0):
    c = _qcolor(c)
    h, s, l, a = c.getHslF()
    if h < 0:  # 灰色没有色相，给一个默认值
        h, s = 0.75, 0.35
    h = (h + degrees / 360.0) % 1.0
    return QColor.fromHslF(h, min(1.0, s * sat_scale), min(1.0, l * light_scale), a)


def with_alpha(c, alpha):
    c = QColor(_qcolor(c))
    c.setAlpha(int(alpha))
    return c


def glass_palette(theme):
    """根据主题字典生成玻璃效果所需的配色"""
    bg = _qcolor(theme.get("bg_color", "#F5F5F5"))
    btn = _qcolor(theme.get("button_color", "#FF8FAB"))
    accent = _qcolor(theme.get("accent_color", theme.get("button_color", "#FFB6C1")))
    hover = _qcolor(theme.get("hover_color", theme.get("button_color", "#FF6B8A")))
    dark = is_dark_color(bg)

    if dark:
        base_top = mix(bg, QColor("#000000"), 0.25)
        base_bottom = mix(bg, btn, 0.18)
        blob_alpha = 150
    else:
        base_top = mix(QColor("#FFFFFF"), btn, 0.08)
        base_bottom = mix(QColor("#FFFFFF"), shift_hue(btn, 70), 0.20)
        blob_alpha = 205

    blobs = [
        btn,
        accent,
        shift_hue(btn, 150, 0.85, 1.0),
        shift_hue(btn, -70, 0.95, 1.0),
        hover,
    ]
    return {
        "dark": dark,
        "base_top": base_top,
        "base_bottom": base_bottom,
        "blobs": [with_alpha(c, blob_alpha) for c in blobs],
        "tint": QColor(255, 255, 255, 26) if dark else QColor(255, 255, 255, 88),
        "tint_bottom": QColor(255, 255, 255, 12) if dark else QColor(255, 255, 255, 48),
        "edge": QColor(255, 255, 255, 70) if dark else QColor(255, 255, 255, 215),
        "edge_soft": QColor(255, 255, 255, 18) if dark else QColor(255, 255, 255, 90),
        "glow": btn,
    }


# ==================== 动态背景 ====================

class AuroraBackground(QWidget):
    """流动极光背景，作为主窗口的 central widget 使用"""

    FPS = 24
    BUFFER_SCALE = 6  # 低分辨率渲染后平滑放大，既省性能又自带柔化

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassRoot")
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        self._palette = glass_palette({})
        self._animated = True
        self._t = random.uniform(0, 100)
        self._mouse = QPointF(0.5, 0.35)
        self._mouse_target = QPointF(0.5, 0.35)
        self._frame = 0

        rnd = random.Random(7)
        # 每个光斑：基准位置、摆动幅度、频率、相位、半径（均为相对窗口尺寸）
        self._blobs = []
        for i in range(5):
            self._blobs.append({
                "cx": [0.18, 0.82, 0.55, 0.12, 0.88][i],
                "cy": [0.22, 0.18, 0.62, 0.85, 0.78][i],
                "ax": rnd.uniform(0.10, 0.20),
                "ay": rnd.uniform(0.08, 0.16),
                "fx": rnd.uniform(0.045, 0.09),
                "fy": rnd.uniform(0.035, 0.08),
                "phase": rnd.uniform(0, math.tau),
                "r": rnd.uniform(0.38, 0.55),
            })

        self._grain = self._make_grain()
        self._clock = QElapsedTimer()
        self._clock.start()
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // self.FPS)

    # ---------- 公共接口 ----------

    def set_theme(self, theme):
        self._palette = glass_palette(theme)
        self.update()

    def palette_info(self):
        return self._palette

    def set_animated(self, animated):
        self._animated = bool(animated)
        if self._animated:
            self._clock.restart()
            self._timer.start(1000 // self.FPS)
        else:
            self._timer.stop()
        self.update()

    def is_animated(self):
        return self._animated

    # ---------- 动画 ----------

    def _tick(self):
        dt = min(self._clock.restart() / 1000.0, 0.1)
        win = self.window()
        if win.isMinimized() or not self.isVisible():
            return
        # 窗口不在前台时降低刷新频率，节省资源
        self._frame += 1
        if not win.isActiveWindow() and self._frame % 3:
            self._t += dt
            return
        self._t += dt

        if self.width() > 0 and self.height() > 0:
            pos = self.mapFromGlobal(QCursor.pos())
            tx = min(max(pos.x() / self.width(), -0.2), 1.2)
            ty = min(max(pos.y() / self.height(), -0.2), 1.2)
            self._mouse_target = QPointF(tx, ty)
        k = 1 - math.exp(-dt * 3.5)  # 指数缓动，光晕柔和地跟随鼠标
        self._mouse = QPointF(
            self._mouse.x() + (self._mouse_target.x() - self._mouse.x()) * k,
            self._mouse.y() + (self._mouse_target.y() - self._mouse.y()) * k,
        )
        self.update()

    # ---------- 绘制 ----------

    @staticmethod
    def _make_grain():
        size = 96
        img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        rnd = random.Random(42)
        for y in range(size):
            for x in range(size):
                v = rnd.randint(0, 255)
                a = rnd.randint(0, 10)
                img.setPixelColor(x, y, QColor(v, v, v, a))
        return QPixmap.fromImage(img)

    def _render_buffer(self):
        w = max(1, self.width() // self.BUFFER_SCALE)
        h = max(1, self.height() // self.BUFFER_SCALE)
        img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        pal = self._palette

        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        base = QLinearGradient(0, 0, w * 0.4, h)
        base.setColorAt(0, pal["base_top"])
        base.setColorAt(1, pal["base_bottom"])
        p.fillRect(0, 0, w, h, base)

        p.setPen(Qt.NoPen)
        t = self._t
        span = max(w, h)
        for blob, color in zip(self._blobs, pal["blobs"]):
            x = (blob["cx"] + blob["ax"] * math.sin(t * blob["fx"] * math.tau + blob["phase"])) * w
            y = (blob["cy"] + blob["ay"] * math.cos(t * blob["fy"] * math.tau + blob["phase"] * 1.3)) * h
            # 半径缓慢“呼吸”
            r = blob["r"] * span * (1 + 0.08 * math.sin(t * 0.25 + blob["phase"]))
            g = QRadialGradient(QPointF(x, y), r)
            g.setColorAt(0, color)
            g.setColorAt(0.45, with_alpha(color, color.alpha() * 0.45))
            g.setColorAt(1, with_alpha(color, 0))
            p.setBrush(g)
            p.drawEllipse(QPointF(x, y), r, r)

        # 鼠标跟随光晕
        mx, my = self._mouse.x() * w, self._mouse.y() * h
        mr = span * 0.35
        g = QRadialGradient(QPointF(mx, my), mr)
        g.setColorAt(0, QColor(255, 255, 255, 55 if pal["dark"] else 120))
        g.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(g)
        p.drawEllipse(QPointF(mx, my), mr, mr)
        p.end()
        return img

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawImage(QRect(0, 0, self.width(), self.height()), self._render_buffer())
        p.drawTiledPixmap(self.rect(), self._grain)
        p.end()


# ==================== 毛玻璃面板 ====================

class GlassPanel(QFrame):
    """毛玻璃面板：放在 AuroraBackground 上即可呈现透出背景的玻璃质感"""

    def __init__(self, parent=None, radius=18, sheen=True):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAttribute(Qt.WA_Hover, True)
        self._radius = radius
        self._palette = glass_palette({})
        self._hover = 0.0
        self._sheen = -1.0  # <0 表示当前没有流光

        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(260)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._hover_anim.valueChanged.connect(self._set_hover)

        self._sheen_anim = QVariantAnimation(self)
        self._sheen_anim.setDuration(1600)
        self._sheen_anim.setStartValue(0.0)
        self._sheen_anim.setEndValue(1.0)
        self._sheen_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._sheen_anim.valueChanged.connect(self._set_sheen)
        self._sheen_anim.finished.connect(lambda: self._set_sheen(-1.0))

        self._sheen_timer = QTimer(self)
        self._sheen_timer.setSingleShot(True)
        self._sheen_timer.timeout.connect(self._play_sheen)
        self._sheen_enabled = sheen
        if sheen:
            self._schedule_sheen(first=True)

    def set_theme(self, palette):
        self._palette = palette
        self.update()

    def set_sheen_enabled(self, enabled):
        self._sheen_enabled = enabled
        if enabled:
            self._schedule_sheen()
        else:
            self._sheen_timer.stop()

    def _schedule_sheen(self, first=False):
        delay = random.randint(1200, 3500) if first else random.randint(9000, 16000)
        self._sheen_timer.start(delay)

    def _play_sheen(self):
        if self.isVisible() and not self.window().isMinimized():
            self._sheen_anim.start()
        if self._sheen_enabled:
            self._schedule_sheen()

    def _set_hover(self, v):
        self._hover = float(v)
        self.update()

    def _set_sheen(self, v):
        self._sheen = float(v)
        self.update()

    def _animate_hover(self, target):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover)
        self._hover_anim.setEndValue(target)
        self._hover_anim.start()

    def enterEvent(self, event):
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        pal = self._palette
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.75, 0.75, -0.75, -0.75)
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)

        # 1. 半透明填充（上亮下暗）
        fill = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        tint = pal["tint"]
        fill.setColorAt(0, with_alpha(tint, min(255, tint.alpha() + 25 * self._hover)))
        fill.setColorAt(1, pal["tint_bottom"])
        p.fillPath(path, fill)

        # 2. 顶部镜面高光
        hl = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + min(90.0, rect.height() * 0.5)))
        hl.setColorAt(0, QColor(255, 255, 255, 40 if pal["dark"] else 95))
        hl.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, hl)

        # 3. 流光：一条斜向光带从左扫到右
        if self._sheen >= 0:
            p.save()
            p.setClipPath(path)
            band = max(120.0, rect.width() * 0.22)
            x = -band + (rect.width() + band * 2) * self._sheen
            g = QLinearGradient(QPointF(x - band, 0), QPointF(x + band, rect.height() * 0.35))
            peak = 34 if pal["dark"] else 80
            g.setColorAt(0, QColor(255, 255, 255, 0))
            g.setColorAt(0.5, QColor(255, 255, 255, peak))
            g.setColorAt(1, QColor(255, 255, 255, 0))
            p.fillRect(rect, g)
            p.restore()

        # 4. 渐变描边（左上亮、右下淡），悬停时混入主题色发光
        edge = QLinearGradient(rect.topLeft(), rect.bottomRight())
        glow = pal["glow"]
        edge.setColorAt(0, mix(pal["edge"], with_alpha(glow, 230), self._hover * 0.55))
        edge.setColorAt(0.5, mix(pal["edge_soft"], with_alpha(glow, 120), self._hover * 0.5))
        edge.setColorAt(1, mix(pal["edge"], with_alpha(glow, 200), self._hover * 0.35))
        p.setPen(QPen(QBrush(edge), 1.4))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        p.end()


# ==================== 滑动高亮块 ====================

class SlidingPill(QWidget):
    """放在分段按钮容器中，平滑滑动到当前选中按钮下方"""

    def __init__(self, container, color="#FF6B9D", radius=8):
        super().__init__(container)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._color = QColor(color)
        self._radius = radius
        self._target = None
        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(320)
        self._anim.setEasingCurve(QEasingCurve.OutBack)
        container.installEventFilter(self)
        self.lower()

    def set_color(self, color):
        self._color = QColor(color)
        self.update()

    def move_to(self, button, animate=True):
        self._target = button
        if not animate or not self.isVisible() or self.width() == 0:
            self._anim.stop()
            self.setGeometry(button.geometry())
            self.lower()
            return
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(button.geometry())
        self._anim.start()

    def eventFilter(self, obj, event):
        # 容器尺寸/布局变化时立即对齐
        if event.type() in (QEvent.Resize, QEvent.LayoutRequest, QEvent.Show) and self._target is not None:
            if self._anim.state() != QPropertyAnimation.Running:
                QTimer.singleShot(0, lambda: self._target and self.setGeometry(self._target.geometry()))
        return False

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, self._color.lighter(112))
        g.setColorAt(1, self._color)
        path = QPainterPath()
        path.addRoundedRect(r, self._radius, self._radius)
        p.fillPath(path, g)
        hl = QLinearGradient(r.topLeft(), QPointF(r.left(), r.center().y()))
        hl.setColorAt(0, QColor(255, 255, 255, 90))
        hl.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, hl)
        p.setPen(QPen(QColor(255, 255, 255, 140), 1))
        p.drawPath(path)
        p.end()


# ==================== 标签页 ====================

class GlassTabBar(QTabBar):
    """选中标签下方有一块平滑滑动的玻璃高亮"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._indicator = QRectF()
        self._color = QColor("#FF6B9D")
        self._dark = False
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(360)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        self.currentChanged.connect(self._slide)
        self.setDrawBase(False)
        self.setExpanding(False)

    def set_colors(self, color, dark=False):
        self._color = QColor(color)
        self._dark = dark
        self.update()

    def _target_rect(self, index):
        if index < 0:
            return QRectF()
        return QRectF(self.tabRect(index)).adjusted(4, 5, -4, -5)

    def _on_anim(self, v):
        self._indicator = v
        self.update()

    def _slide(self, index):
        target = self._target_rect(index)
        if self._indicator.isNull() or not self.isVisible():
            self._indicator = target
            self.update()
            return
        self._anim.stop()
        self._anim.setStartValue(self._indicator)
        self._anim.setEndValue(target)
        self._anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._anim.state() != QVariantAnimation.Running:
            self._indicator = self._target_rect(self.currentIndex())

    def tabLayoutChange(self):
        super().tabLayoutChange()
        if self._anim.state() != QVariantAnimation.Running:
            self._indicator = self._target_rect(self.currentIndex())

    def paintEvent(self, event):
        if not self._indicator.isNull():
            # 滚动按钮出现时 tabRect 会随偏移变化，这里每次重新取目标位置
            if self._anim.state() != QVariantAnimation.Running:
                self._indicator = self._target_rect(self.currentIndex())
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            r = self._indicator
            path = QPainterPath()
            path.addRoundedRect(r, r.height() / 2, r.height() / 2)
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, QColor(255, 255, 255, 60 if self._dark else 200))
            g.setColorAt(1, QColor(255, 255, 255, 25 if self._dark else 120))
            p.fillPath(path, g)
            p.setPen(QPen(with_alpha(self._color, 150), 1.2))
            p.drawPath(path)
            # 底部主题色小光条
            bar = QRectF(r.center().x() - r.width() * 0.18, r.bottom() - 3, r.width() * 0.36, 3)
            p.setPen(Qt.NoPen)
            p.setBrush(self._color)
            p.drawRoundedRect(bar, 1.5, 1.5)
            p.end()
        super().paintEvent(event)


class _FadeOverlay(QWidget):
    """切换标签时覆盖在旧页面位置上的快照，淡出并轻微位移"""

    def __init__(self, parent, pixmap, direction):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._pixmap = pixmap
        self._direction = direction
        self._progress = 0.0

    def set_progress(self, v):
        self._progress = float(v)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setOpacity(max(0.0, 1.0 - self._progress))
        p.drawPixmap(int(-28 * self._direction * self._progress), 0, self._pixmap)
        p.end()


class GlassTabWidget(QTabWidget):
    """使用 GlassTabBar，并在切换标签时播放淡出过渡"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._glass_bar = GlassTabBar(self)
        self.setTabBar(self._glass_bar)
        self.setDocumentMode(True)
        self._glass_bar.setDrawBase(False)  # setDocumentMode 会重新打开底线
        self._overlay = None
        self._overlay_anim = None
        self._prev_index = -1
        self._prev_pixmap = None
        self._glass_bar.tabBarClicked.connect(self._capture)
        self.currentChanged.connect(self._transition)

    def glass_tab_bar(self):
        return self._glass_bar

    def _capture(self, index):
        page = self.currentWidget()
        if page is not None and index != self.currentIndex():
            self._prev_index = self.currentIndex()
            self._prev_pixmap = page.grab()

    def _transition(self, index):
        pixmap, prev = self._prev_pixmap, self._prev_index
        self._prev_pixmap = None
        page = self.widget(index)
        if pixmap is None or page is None:
            return
        if self._overlay is not None:
            self._overlay.deleteLater()
        overlay = _FadeOverlay(page.parentWidget(), pixmap, 1 if index > prev else -1)
        overlay.setGeometry(page.geometry())
        overlay.show()
        overlay.raise_()
        self._overlay = overlay

        anim = QVariantAnimation(overlay)
        anim.setDuration(240)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(overlay.set_progress)
        anim.finished.connect(overlay.deleteLater)
        anim.finished.connect(lambda: setattr(self, "_overlay", None) if self._overlay is overlay else None)
        anim.start()
        self._overlay_anim = anim


# ==================== 窗口淡入 ====================

def fade_in_window(window, duration=380):
    window.setWindowOpacity(0.0)
    anim = QPropertyAnimation(window, b"windowOpacity", window)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


def make_scroll_areas_transparent(root):
    """让 root 下所有滚动区域的 viewport 不再填充底色，从而透出玻璃背景"""
    from PyQt5.QtWidgets import QAbstractScrollArea, QScrollArea
    for area in root.findChildren(QAbstractScrollArea):
        area.viewport().setAutoFillBackground(False)
        if isinstance(area, QScrollArea) and area.widget() is not None:
            area.widget().setAutoFillBackground(False)
