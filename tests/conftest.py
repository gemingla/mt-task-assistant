import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import utils  # noqa: E402


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """把所有数据文件重定向到临时目录，测试不会触碰真实的 tasks.json 等文件"""
    def fake_get_data_path(relative_path=""):
        return os.path.join(str(tmp_path), relative_path) if relative_path else str(tmp_path)

    monkeypatch.setattr(utils, "get_data_path", fake_get_data_path)
    for module_name, attr, filename in (
        ("task_manager", "TASKS_FILE", "tasks.json"),
        ("stats_manager", "STATS_FILE", "stats.json"),
        ("tag_manager", "TAGS_FILE", "tags.json"),
        ("config", "CONFIG_FILE", "config.json"),
    ):
        module = __import__(module_name)
        monkeypatch.setattr(module, attr, fake_get_data_path(filename))
    for module_name in ("backup_manager", "task_manager", "stats_manager", "tag_manager", "config"):
        module = __import__(module_name)
        if hasattr(module, "get_data_path"):
            monkeypatch.setattr(module, "get_data_path", fake_get_data_path)
    return tmp_path


@pytest.fixture(scope="session")
def qapp():
    """ReminderManager 依赖 QObject/QTimer，需要一个 Qt 应用实例"""
    from PyQt5.QtCore import QCoreApplication
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app
