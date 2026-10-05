"""原子写入、损坏回退与配置保护"""
import json
import os

from utils import atomic_write_json, load_json_with_backup


def test_atomic_write_roundtrip(tmp_path):
    path = str(tmp_path / "data.json")
    atomic_write_json(path, {"a": 1, "中文": "值"})
    assert load_json_with_backup(path) == {"a": 1, "中文": "值"}
    assert not os.path.exists(path + ".tmp")


def test_atomic_write_keeps_previous_version_as_backup(tmp_path):
    path = str(tmp_path / "data.json")
    atomic_write_json(path, [1])
    atomic_write_json(path, [1, 2])
    with open(path + ".bak", encoding="utf-8") as f:
        assert json.load(f) == [1]


def test_load_falls_back_to_backup_when_main_file_corrupted(tmp_path):
    path = str(tmp_path / "data.json")
    atomic_write_json(path, {"v": 1})
    atomic_write_json(path, {"v": 2})
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"v": 2, "trunc')  # 模拟写到一半崩溃
    assert load_json_with_backup(path) == {"v": 1}


def test_load_falls_back_when_main_file_empty(tmp_path):
    path = str(tmp_path / "data.json")
    atomic_write_json(path, [1])
    atomic_write_json(path, [1, 2])
    open(path, "w").close()
    assert load_json_with_backup(path) == [1]


def test_load_returns_default_when_nothing_available(tmp_path):
    assert load_json_with_backup(str(tmp_path / "missing.json"), default=[]) == []


def test_corrupted_config_is_not_overwritten_with_defaults(data_dir):
    from config import ConfigManager
    path = str(data_dir / "config.json")
    manager = ConfigManager(path)
    manager.save_config({"api_key": "sk-secret", "theme": {"preset": "萌兔粉"}})
    manager.save_config({"api_key": "sk-secret-2", "theme": {"preset": "萌兔粉"}})
    with open(path, "w", encoding="utf-8") as f:
        f.write("{broken")

    config = manager.load_config()
    assert config["api_key"] == "sk-secret"      # 从 .bak 恢复
    with open(path, encoding="utf-8") as f:
        assert f.read() == "{broken"             # 损坏文件未被默认配置覆盖


def test_missing_config_is_created_with_defaults(data_dir):
    from config import ConfigManager, DEFAULT_CONFIG
    path = str(data_dir / "config.json")
    config = ConfigManager(path).load_config()
    assert config["theme"] == DEFAULT_CONFIG["theme"]
    assert os.path.exists(path)
    config["theme"]["preset"] = "深海蓝"           # 修改返回值不能污染默认配置
    assert DEFAULT_CONFIG["theme"]["preset"] == "萌兔粉"
