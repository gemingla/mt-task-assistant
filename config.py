import json
import os
from utils import get_data_path


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
        if not os.path.exists(self.config_path):
            self.save_config(DEFAULT_CONFIG.copy())
            return DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.save_config(DEFAULT_CONFIG.copy())
            return DEFAULT_CONFIG.copy()

    def save_config(self, config):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
