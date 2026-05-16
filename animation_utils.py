from PyQt5.QtCore import (QPropertyAnimation, QVariantAnimation,
                          QEasingCurve, pyqtProperty, Qt, QPoint, QSize,
                          QParallelAnimationGroup, QSequentialAnimationGroup,
                          QPauseAnimation, QTimer)
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsBlurEffect, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor


# ========================
# 基础动画类
# ========================

class FadeAnimation:
    """增强版淡入淡出动画"""
    def __init__(self, widget, duration=300):
        self.widget = widget
        self.duration = duration
        self._opacity_effect = None
        self._animation = None

    def setup(self):
        if self._opacity_effect is None:
            self._opacity_effect = QGraphicsOpacityEffect(self.widget)
            self.widget.setGraphicsEffect(self._opacity_effect)
        return self._opacity_effect

    def fade_in(self, on_finished=None):
        effect = self.setup()
        self._animation = QPropertyAnimation(effect, b"opacity")
        self._animation.setDuration(self.duration)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        if on_finished:
            self._animation.finished.connect(on_finished)
        self._animation.start()
        return self._animation

    def fade_out(self, on_finished=None):
        effect = self.setup()
        self._animation = QPropertyAnimation(effect, b"opacity")
        self._animation.setDuration(self.duration)
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.setEasingCurve(QEasingCurve.InCubic)
        if on_finished:
            self._animation.finished.connect(on_finished)
        self._animation.start()
        return self._animation

    def stop(self):
        if self._animation:
            self._animation.stop()


class ColorTransitionAnimation:
    def __init__(self, widget, duration=200):
        self.widget = widget
        self.duration = duration
        self._animation = None
        self._current_color = QColor("#FFFFFF")

    def _get_bg_color(self):
        return self._current_color

    def _set_bg_color(self, color):
        self._current_color = color
        self.widget.setStyleSheet(
            f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()});"
        )

    bg_color = pyqtProperty(QColor, _get_bg_color, _set_bg_color)

    def transition_to(self, target_color, on_finished=None):
        if isinstance(target_color, str):
            target_color = QColor(target_color)
        self._animation = QVariantAnimation(self.widget)
        self._animation.setDuration(self.duration)
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(target_color)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.valueChanged.connect(self._set_bg_color)
        if on_finished:
            self._animation.finished.connect(on_finished)
        self._animation.start()
        return self._animation


class SlideAnimation:
    def __init__(self, widget, duration=250):
        self.widget = widget
        self.duration = duration
        self._animation = None

    def slide_in_from_left(self, on_finished=None):
        self._animation = QPropertyAnimation(self.widget, b"geometry")
        self._animation.setDuration(self.duration)
        current_geo = self.widget.geometry()
        start_geo = current_geo
        start_geo.moveLeft(-current_geo.width())
        self._animation.setStartValue(start_geo)
        self._animation.setEndValue(current_geo)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        if on_finished:
            self._animation.finished.connect(on_finished)
        self._animation.start()
        return self._animation

    def slide_out_to_left(self, on_finished=None):
        self._animation = QPropertyAnimation(self.widget, b"geometry")
        self._animation.setDuration(self.duration)
        current_geo = self.widget.geometry()
        end_geo = current_geo
        end_geo.moveLeft(-current_geo.width())
        self._animation.setStartValue(current_geo)
        self._animation.setEndValue(end_geo)
        self._animation.setEasingCurve(QEasingCurve.InCubic)
        if on_finished:
            self._animation.finished.connect(on_finished)
        self._animation.start()
        return self._animation


class ScaleAnimation:
    def __init__(self, widget, duration=200):
        self.widget = widget
        self.duration = duration
        self._animation = None
        self._original_size = None

    def scale_in(self, on_finished=None):
        if self._original_size is None:
            self._original_size = self.widget.size()
        self._animation = QPropertyAnimation(self.widget, b"geometry")
        self._animation.setDuration(self.duration)
        current_geo = self.widget.geometry()
        small_geo = current_geo
        small_geo.setSize(QSize(0, 0))
        small_geo.moveCenter(current_geo.center())
        self._animation.setStartValue(small_geo)
        self._animation.setEndValue(current_geo)
        self._animation.setEasingCurve(QEasingCurve.OutBack)
        if on_finished:
            self._animation.finished.connect(on_finished)
        self._animation.start()
        return self._animation


# ========================
# 新增动画效果
# ========================

class BounceAnimation:
    """弹跳动画 — 用于按钮点击反馈、完成任务庆祝"""
    def __init__(self, widget, duration=400):
        self.widget = widget
        self.duration = duration
        self._animation = None
        self._original_geometry = None

    def bounce(self, on_finished=None):
        """弹跳效果：先缩小再弹回"""
        geo = self.widget.geometry()
        self._original_geometry = geo

        scale_down = QVariantAnimation(self.widget)
        scale_down.setDuration(int(self.duration * 0.4))
        scale_down.setStartValue(1.0)
        scale_down.setEndValue(0.85)
        scale_down.setEasingCurve(QEasingCurve.InQuad)

        scale_up = QVariantAnimation(self.widget)
        scale_up.setDuration(int(self.duration * 0.6))
        scale_up.setStartValue(0.85)
        scale_up.setEndValue(1.0)
        scale_up.setEasingCurve(QEasingCurve.OutBack)

        group = QSequentialAnimationGroup(self.widget)
        group.addPause(0)
        group.addAnimation(scale_down)
        group.addAnimation(scale_up)

        cx, cy = geo.x() + geo.width() / 2, geo.y() + geo.height() / 2
        orig_w, orig_h = geo.width(), geo.height()

        def update_scale(value):
            w = int(orig_w * value)
            h = int(orig_h * value)
            self.widget.setGeometry(int(cx - w / 2), int(cy - h / 2), w, h)

        scale_down.valueChanged.connect(update_scale)
        scale_up.valueChanged.connect(update_scale)

        if on_finished:
            group.finished.connect(lambda: (self.widget.setGeometry(geo), on_finished()))
        else:
            group.finished.connect(lambda: self.widget.setGeometry(geo))

        group.start()
        return group


class PulseAnimation:
    """脉冲动画 — 用于提醒、加载状态"""
    def __init__(self, widget, duration=1000):
        self.widget = widget
        self.duration = duration
        self._animation = None
        self._shadow = None

    def pulse_glow(self, color=QColor(255, 107, 157), max_blur=30):
        """发光脉冲效果 — 使用阴影模拟光晕"""
        if self._shadow is None:
            self._shadow = QGraphicsDropShadowEffect(self.widget)
            self.widget.setGraphicsEffect(self._shadow)

        self._shadow.setColor(color)
        self._shadow.setOffset(0, 0)

        self._animation = QVariantAnimation(self.widget)
        self._animation.setDuration(self.duration)
        self._animation.setStartValue(5)
        self._animation.setEndValue(max_blur)
        self._animation.setEasingCurve(QEasingCurve.InOutSine)

        def update_blur(value):
            if self._shadow:
                self._shadow.setBlurRadius(value)

        self._animation.valueChanged.connect(update_blur)
        self._animation.setLoopCount(-1)  # 无限循环
        self._animation.start()
        return self._animation

    def pulse_opacity(self, min_opacity=0.3, max_opacity=1.0):
        """透明度脉冲 — 用于等待/加载指示"""
        effect = QGraphicsOpacityEffect(self.widget)
        self.widget.setGraphicsEffect(effect)

        self._animation = QVariantAnimation(self.widget)
        self._animation.setDuration(self.duration)
        self._animation.setStartValue(min_opacity)
        self._animation.setEndValue(max_opacity)
        self._animation.setEasingCurve(QEasingCurve.InOutSine)

        def update_opacity(value):
            effect.setOpacity(value)

        self._animation.valueChanged.connect(update_opacity)
        self._animation.setLoopCount(-1)
        self._animation.start()
        return self._animation

    def stop(self):
        if self._animation:
            self._animation.stop()
            self._animation = None
        if self._shadow:
            self.widget.setGraphicsEffect(None)
            self._shadow = None


class StaggerAnimation:
    """交错动画 — 用于列表项依次入场"""
    def __init__(self, widgets, stagger_delay=80, duration=300):
        self.widgets = widgets
        self.stagger_delay = stagger_delay
        self.duration = duration

    def animate_in(self, on_all_finished=None):
        """所有控件依次淡入+上移"""
        group = QParallelAnimationGroup()
        finished_count = [0]

        for i, w in enumerate(self.widgets):
            effect = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(effect)
            effect.setOpacity(0)

            # 先偏移再归位
            orig_pos = w.pos()
            w.move(orig_pos.x(), orig_pos.y() + 20)

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(self.duration)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.setStartTime(i * self.stagger_delay)

            pos_anim = QPropertyAnimation(w, b"pos")
            pos_anim.setDuration(self.duration)
            pos_anim.setStartValue(QPoint(orig_pos.x(), orig_pos.y() + 20))
            pos_anim.setEndValue(orig_pos)
            pos_anim.setEasingCurve(QEasingCurve.OutCubic)
            pos_anim.setStartTime(i * self.stagger_delay)

            group.addAnimation(anim)
            group.addAnimation(pos_anim)

        if on_all_finished:
            group.finished.connect(on_all_finished)

        group.start()
        return group


class TypingIndicatorAnimation:
    """打字指示器动画 — 三个点依次闪烁"""
    def __init__(self, labels, duration=1200):
        self.labels = labels  # 三个 QLabel 列表
        self.duration = duration
        self._timers = []
        self._opacities = [0.3, 0.3, 0.3]

    def start(self):
        """开始三点闪烁动画"""
        from PyQt5.QtCore import QTimer
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(int(self.duration / 3))
        self._tick()
        return self._timer

    def _tick(self):
        """每个 tick 点亮一个点"""
        import random
        for label in self.labels:
            label.setStyleSheet("color: #B0B0B0; font-size: 24px; font-weight: bold;")
        # 随机点亮一个点
        idx = random.randint(0, 2)
        self.labels[idx].setStyleSheet("color: #FF6B9D; font-size: 24px; font-weight: bold;")

    def stop(self):
        if hasattr(self, '_timer') and self._timer:
            self._timer.stop()
        for label in self.labels:
            label.setStyleSheet("color: #B0B0B0; font-size: 24px; font-weight: bold;")


class ShakeAnimation:
    """抖动动画 — 用于错误提示、删除确认"""
    def __init__(self, widget, duration=400):
        self.widget = widget
        self.duration = duration
        self._animation = None

    def shake_horizontal(self, on_finished=None):
        """水平抖动"""
        original_x = self.widget.x()
        self._animation = QVariantAnimation(self.widget)
        self._animation.setDuration(self.duration)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Linear)

        def update(value):
            offset = 5 * __import__('math').sin(value * 4 * __import__('math').pi)
            self.widget.move(int(original_x + offset), self.widget.y())

        self._animation.valueChanged.connect(update)
        if on_finished:
            self._animation.finished.connect(lambda: (self.widget.move(original_x, self.widget.y()), on_finished()))
        else:
            self._animation.finished.connect(lambda: self.widget.move(original_x, self.widget.y()))
        self._animation.start()
        return self._animation


class RippleAnimation:
    """涟漪按钮效果 — 点击按钮时扩散光晕"""
    def __init__(self, button, color=QColor(255, 107, 157, 80)):
        self.button = button
        self.color = color
        self._animation = None
        self._shadow = None

    def click_ripple(self, on_finished=None):
        """点击涟漪: 阴影扩散并消失"""
        if self._shadow is None:
            self._shadow = QGraphicsDropShadowEffect(self.button)
            self.button.setGraphicsEffect(self._shadow)

        self._shadow.setColor(self.color)
        self._shadow.setOffset(0, 0)

        self._animation = QVariantAnimation(self.button)
        self._animation.setDuration(500)
        self._animation.setStartValue(5)
        self._animation.setEndValue(40)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

        def update(value):
            if self._shadow:
                self._shadow.setBlurRadius(value)

        self._animation.valueChanged.connect(update)
        if on_finished:
            self._animation.finished.connect(lambda: (self._cleanup(), on_finished()))
        else:
            self._animation.finished.connect(self._cleanup)
        self._animation.start()
        return self._animation

    def _cleanup(self):
        if self._shadow:
            self._shadow.setBlurRadius(0)
        if self._animation:
            self._animation = None


# ========================
# 便捷工厂函数
# ========================

def create_bounce_animation(widget, duration=400):
    return BounceAnimation(widget, duration)


def create_pulse_animation(widget, duration=1000):
    return PulseAnimation(widget, duration)


def create_stagger_animation(widgets, stagger_delay=80, duration=300):
    return StaggerAnimation(widgets, stagger_delay, duration)


def create_typing_indicator(labels, duration=1200):
    return TypingIndicatorAnimation(labels, duration)


def create_shake_animation(widget, duration=400):
    return ShakeAnimation(widget, duration)


def create_ripple_animation(button, color=QColor(255, 107, 157, 80)):
    return RippleAnimation(button, color)


# ========================
# 旧版兼容 — 保持原有 API
# ========================

class BlurEffect:
    def __init__(self, widget):
        self.widget = widget
        self._blur_effect = None

    def apply(self, radius=10):
        if self._blur_effect is None:
            self._blur_effect = QGraphicsBlurEffect(self.widget)
        self._blur_effect.setBlurRadius(radius)
        self.widget.setGraphicsEffect(self._blur_effect)
        return self._blur_effect

    def remove(self):
        if self._blur_effect:
            self.widget.setGraphicsEffect(None)
            self._blur_effect = None

    def animate_blur(self, start_radius=0, end_radius=10, duration=200):
        self._blur_effect = QGraphicsBlurEffect(self.widget)
        self.widget.setGraphicsEffect(self._blur_effect)
        animation = QVariantAnimation(self.widget)
        animation.setDuration(duration)
        animation.setStartValue(start_radius)
        animation.setEndValue(end_radius)
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        def update_blur(value):
            if self._blur_effect:
                self._blur_effect.setBlurRadius(value)

        animation.valueChanged.connect(update_blur)
        animation.start()
        return animation


class AnimationManager:
    def __init__(self, widget):
        self.widget = widget
        self._fade = None
        self._color = None
        self._slide = None
        self._scale = None
        self._blur = None
        self._bounce = None
        self._pulse = None
        self._shake = None
        self._ripple = None

    @property
    def fade(self):
        if self._fade is None:
            self._fade = FadeAnimation(self.widget)
        return self._fade

    @property
    def color(self):
        if self._color is None:
            self._color = ColorTransitionAnimation(self.widget)
        return self._color

    @property
    def slide(self):
        if self._slide is None:
            self._slide = SlideAnimation(self.widget)
        return self._slide

    @property
    def scale(self):
        if self._scale is None:
            self._scale = ScaleAnimation(self.widget)
        return self._scale

    @property
    def blur(self):
        if self._blur is None:
            self._blur = BlurEffect(self.widget)
        return self._blur

    @property
    def bounce(self):
        if self._bounce is None:
            self._bounce = BounceAnimation(self.widget)
        return self._bounce

    @property
    def pulse(self):
        if self._pulse is None:
            self._pulse = PulseAnimation(self.widget)
        return self._pulse

    @property
    def shake(self):
        if self._shake is None:
            self._shake = ShakeAnimation(self.widget)
        return self._shake

    @property
    def ripple(self):
        if self._ripple is None:
            self._ripple = RippleAnimation(self.widget)
        return self._ripple

    def stop_all(self):
        for attr in ['_fade', '_color', '_slide', '_scale', '_bounce', '_pulse', '_shake', '_ripple']:
            obj = getattr(self, attr, None)
            if obj:
                if hasattr(obj, 'stop'):
                    obj.stop()
                elif hasattr(obj, '_animation') and obj._animation:
                    obj._animation.stop()


def create_fade_animation(widget, duration=300):
    return FadeAnimation(widget, duration)

def create_color_animation(widget, duration=200):
    return ColorTransitionAnimation(widget, duration)

def animate_widget_fade_in(widget, duration=300, on_finished=None):
    fade = FadeAnimation(widget, duration)
    return fade.fade_in(on_finished)

def animate_widget_fade_out(widget, duration=300, on_finished=None):
    fade = FadeAnimation(widget, duration)
    return fade.fade_out(on_finished)
