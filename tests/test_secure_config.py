"""API Key 加密存储：DPAPI 往返、旧明文迁移、备份中不含明文"""
import json
import sys

import pytest

from secure_store import protect, unprotect, DPAPI_PREFIX


def test_protect_roundtrip():
    token = protect("sk-测试-123")
    assert token != "sk-测试-123"
    assert unprotect(token) == "sk-测试-123"
    assert protect("") == "" and unprotect("") == ""


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI 仅在 Windows 上可用")
def test_dpapi_token_and_tamper_detection():
    token = protect("sk-secret")
    assert token.startswith(DPAPI_PREFIX)
    with pytest.raises(ValueError):
        unprotect(DPAPI_PREFIX + "AAAA" + token[len(DPAPI_PREFIX) + 4:])


def read_raw(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_api_key_never_stored_in_plaintext(data_dir):
    from config import ConfigManager
    path = str(data_dir / "config.json")
    manager = ConfigManager(path)
    config = manager.load_config()
    config["api_key"] = "sk-secret-value"
    manager.save_config(config)

    raw = read_raw(path)
    assert "api_key" not in raw
    assert "sk-secret-value" not in json.dumps(raw)
    assert manager.load_config()["api_key"] == "sk-secret-value"


def test_legacy_plaintext_key_is_migrated(data_dir):
    from config import ConfigManager
    path = str(data_dir / "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"api_url": "https://x", "api_key": "sk-legacy"}, f)

    assert ConfigManager(path).load_config()["api_key"] == "sk-legacy"
    raw = read_raw(path)
    assert "api_key" not in raw and raw["api_key_enc"]


def test_undecryptable_key_becomes_empty(data_dir):
    from config import ConfigManager
    path = str(data_dir / "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"api_key_enc": DPAPI_PREFIX + "bm90LXZhbGlk"}, f)
    assert ConfigManager(path).load_config()["api_key"] == ""


def test_backup_keeps_key_encrypted_and_restores(data_dir):
    from config import ConfigManager
    from backup_manager import BackupManager
    path = str(data_dir / "config.json")
    manager = ConfigManager(path)
    config = manager.load_config()
    config["api_key"] = "sk-backup-me"
    manager.save_config(config)

    bm = BackupManager(config_manager=manager)
    ok, _, backup_path = bm.create_backup()
    assert ok
    with open(backup_path, encoding="utf-8") as f:
        assert "sk-backup-me" not in f.read()

    config["api_key"] = "sk-changed"
    manager.save_config(config)
    bm.restore_backup(backup_path)
    assert manager.load_config()["api_key"] == "sk-backup-me"


def test_ai_client_reads_decrypted_key(data_dir, monkeypatch):
    import ai_client
    from config import ConfigManager
    path = str(data_dir / "config.json")
    monkeypatch.setattr(ai_client, "get_config_path", lambda: path)
    manager = ConfigManager(path)
    config = manager.load_config()
    config["api_key"] = "sk-for-client"
    manager.save_config(config)
    assert ai_client._load_config()["api_key"] == "sk-for-client"
