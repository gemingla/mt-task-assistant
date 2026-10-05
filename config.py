import json
import os
import copy
from utils import get_data_path, atomic_write_json, load_json_with_backup


CONFIG_FILE = get_data_path("config.json")

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
        config = load_json_with_backup(self.config_path)
        if not isinstance(config, dict):
            if not os.path.exists(self.config_path):
                self.save_config(copy.deepcopy(DEFAULT_CONFIG))
            return copy.deepcopy(DEFAULT_CONFIG)
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = copy.deepcopy(value)
        return config

    def save_config(self, config):
        try:
            atomic_write_json(self.config_path, config)
        except Exception as e:
            print(f"保存配置失败: {e}")
