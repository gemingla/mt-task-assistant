"""主题适配：样式表颜色改写规则"""
import re

from PyQt5.QtGui import QColor

from theme_adapter import transform_qss, _strip_dialog_background, DARK_TEXT, DARK_MUTED


def test_light_theme_makes_white_backgrounds_translucent():
    out = transform_qss("QFrame { background-color: white; color: #333; }", dark=False)
    assert "rgba(255, 255, 255, 0.62)" in out
    assert "color: #333" in out  # 浅色主题不改文字


def test_light_theme_keeps_colored_and_translucent_backgrounds():
    qss = "background-color: #FF8FAB; border: 1px solid rgba(255,255,255,0.9); background: rgba(255,255,255,0.5);"
    assert transform_qss(qss, dark=False) == qss


def test_dark_theme_text_colors():
    assert transform_qss("color: #333;", dark=True) == f"color: {DARK_TEXT};"
    out = transform_qss("QLabel { color: #999999; } x { color: #FF6B9D; } y { color: white; }", dark=True)
    assert f"color: {DARK_MUTED}" in out
    assert "color: #FF6B9D" in out   # 本身够亮的彩色文字保持
    assert "color: white" in out     # 白字保持


def test_dark_theme_lightens_dark_colored_text():
    out = transform_qss("QLabel { background: #E3F2FD; color: #1976D2; }", dark=True)
    new_color = QColor(re.search(r"color: (#[0-9a-f]{6})", out).group(1))
    assert new_color.lightnessF() > 0.7
    assert abs(new_color.hslHueF() - QColor("#1976D2").hslHueF()) < 0.02  # 色相不变


def test_dark_theme_keeps_text_on_solid_colored_background():
    qss = "QPushButton { background-color: #4CAF50; color: #1B5E20; }"
    assert transform_qss(qss, dark=True) == qss


def test_dark_theme_backgrounds_and_borders():
    out = transform_qss("QFrame { background-color: #FAFAFA; border: 2px solid #E0E0E0; border-radius: 8px; }", dark=True)
    assert "background-color: rgba(255, 255, 255, 0.14)" in out
    assert "border: 2px solid rgba(255, 255, 255, 0.16)" in out
    assert "border-radius: 8px" in out


def test_dark_theme_converts_translucent_white_cards():
    out = transform_qss("background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                        "stop:0 rgba(255, 255, 255, 0.86), stop:1 rgba(255, 255, 255, 0.62));", dark=True)
    assert "rgba(255, 255, 255, 0.86)" not in out and "stop:0 rgba(255, 255, 255, 0.13)" in out


def test_dark_theme_keeps_buttons():
    qss = "QPushButton { background-color: #4CAF50; color: white; } QPushButton:hover { background-color: #45a049; }"
    assert transform_qss(qss, dark=True) == qss


def test_transform_is_stable_from_original():
    original = "QWidget { background: #FFFFFF; color: #333333; }"
    dark = transform_qss(original, dark=True)
    assert transform_qss(original, dark=False) != dark
    assert "#333333" not in dark


def test_strip_dialog_background():
    assert "background" not in _strip_dialog_background("background-color: #FAFAFA;")
    out = _strip_dialog_background("QDialog { background-color: white; } QLineEdit { background: white; }")
    assert "QDialog {" in out and "QLineEdit { background: white; }" in out
    assert out.count("background") == 1
