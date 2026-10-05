import os
import copy
from utils import get_data_path, atomic_write_json, load_json_with_backup, log_error
from secure_store import protect, unprotect


CONFIG_FILE = get_data_path("config.json")

# 这些字段在磁盘上只保存加密后的 <字段>_enc，内存中使用解密后的明文
SECRET_FIELDS = ("api_key",)

DEFAULT_CONFIG = {
    "api_url": "",
    "api_key": "",
    "model": "",
    "system_prompt": "你是一个专业的效率助手，请用简洁清晰的语言帮助用户管理时间。",
    "auto_start": False,
    "theme": {
        "preset": "萌兔粉",
        "custom": {
            "bg_color": "#F5F5F5",
            "button_color": "#FF8FAB",
            "card_bg_color": "#FFFFFF",
            "text_color": "#2D2D2D",
            "border_color": "#E0E0E0"
        }
    }
}


class ConfigManager:
    def __init__(self, config_path=None):
        self.config_path = config_path or CONFIG_FILE

    def load_config(self):
        # 主文件损坏时回退到 .bak；两者都不可用才使用默认配置，
        # 且只有文件确实不存在时才写回磁盘，避免把用户的 API Key 等配置清空
        stored = load_json_with_backup(self.config_path)
        if not isinstance(stored, dict):
            if not os.path.exists(self.config_path):
                self.save_config(copy.deepcopy(DEFAULT_CONFIG))
            return copy.deepcopy(DEFAULT_CONFIG)

        config = self._decrypt(stored)
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = copy.deepcopy(value)

        # 旧版本明文保存的密钥：读取后立即加密写回
        if any(stored.get(field) for field in SECRET_FIELDS):
            self.save_config(config)
        return config

    def save_config(self, config):
        try:
            atomic_write_json(self.config_path, self._encrypt(config))
        except Exception as e:
            print(f"保存配置失败: {e}")

    def load_stored_config(self):
        """磁盘上的原始配置（密钥为密文），用于备份，避免备份文件中出现明文密钥"""
        stored = load_json_with_backup(self.config_path)
        return stored if isinstance(stored, dict) else self._encrypt(copy.deepcopy(DEFAULT_CONFIG))

    @staticmethod
    def _encrypt(config):
        data = dict(config)
        for field in SECRET_FIELDS:
            secret = data.pop(field, "")
            if secret:
                data[f"{field}_enc"] = protect(secret)
            # 传入的配置只有密文（如从备份恢复）时保留密文
            elif not data.get(f"{field}_enc"):
                data.pop(f"{field}_enc", None)
        return data

    @staticmethod
    def _decrypt(stored):
        config = dict(stored)
        for field in SECRET_FIELDS:
            token = config.pop(f"{field}_enc", "")
            if config.get(field):
                continue  # 旧版明文
            try:
                config[field] = unprotect(token)
            except ValueError as e:
                log_error(f"配置项 {field} 解密失败，需要重新填写: {e}")
                config[field] = ""
        return config
