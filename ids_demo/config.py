import json
import os
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "database"
PHOTOS_DIR = BASE_DIR / "photos"
DB_PATH = DATA_DIR / "events.db"
SETTINGS_PATH = DATA_DIR / "settings.json"


def _hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()


@dataclass
class TelegramConfig:
    bot_token: str = ""
    chat_id: str = ""


class ConfigManager:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        self._settings = self._load_or_create()

    @property
    def settings(self) -> Dict:
        return self._settings

    def _default_settings(self) -> Dict:
        return {
            "auth": {
                "username": "demo",
                "password_hash": _hash_password("demo"),
            },
            "telegram": {
                "bot_token": "",
                "chat_id": "",
            },
            "monitoring": {
                "folders": [],
            },
            "alerts": {
                "sound_enabled": True,
                "toast_enabled": True,
            },
            "meta": {
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        }

    def _load_or_create(self) -> Dict:
        if not SETTINGS_PATH.exists():
            data = self._default_settings()
            self._write(data)
            return data

        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = self._default_settings()
            self._write(data)
            return data

        # Ensure missing keys are restored safely.
        default_data = self._default_settings()
        for k, v in default_data.items():
            data.setdefault(k, v)

        data["auth"].setdefault("username", "demo")
        data["auth"].setdefault("password_hash", _hash_password("demo"))
        data["telegram"].setdefault("bot_token", "")
        data["telegram"].setdefault("chat_id", "")
        data["monitoring"].setdefault("folders", [])
        data.setdefault("alerts", {})
        data["alerts"].setdefault("sound_enabled", True)
        data["alerts"].setdefault("toast_enabled", True)
        data.setdefault("meta", {})
        data["meta"].setdefault("created_at", datetime.utcnow().isoformat())
        data["meta"]["updated_at"] = datetime.utcnow().isoformat()

        self._write(data)
        return data

    def _write(self, data: Dict) -> None:
        data["meta"]["updated_at"] = datetime.utcnow().isoformat()
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def validate_login(self, username: str, password: str) -> bool:
        stored_user = self._settings["auth"].get("username", "demo")
        stored_hash = self._settings["auth"].get("password_hash", _hash_password("demo"))
        return username == stored_user and _hash_password(password) == stored_hash

    def update_credentials(self, username: str, password: str) -> None:
        self._settings["auth"]["username"] = username.strip() or "demo"
        self._settings["auth"]["password_hash"] = _hash_password(password.strip() or "demo")
        self._write(self._settings)

    def get_telegram_config(self) -> TelegramConfig:
        tg = self._settings.get("telegram", {})
        return TelegramConfig(
            bot_token=tg.get("bot_token", ""),
            chat_id=tg.get("chat_id", ""),
        )

    def update_telegram_config(self, bot_token: str, chat_id: str) -> None:
        self._settings["telegram"]["bot_token"] = bot_token.strip()
        self._settings["telegram"]["chat_id"] = chat_id.strip()
        self._write(self._settings)

    def get_monitored_folders(self) -> List[str]:
        return self._settings.get("monitoring", {}).get("folders", [])

    def get_alert_preferences(self) -> Dict[str, bool]:
        alerts = self._settings.get("alerts", {})
        return {
            "sound_enabled": bool(alerts.get("sound_enabled", True)),
            "toast_enabled": bool(alerts.get("toast_enabled", True)),
        }

    def update_alert_preferences(self, sound_enabled: bool, toast_enabled: bool) -> None:
        self._settings.setdefault("alerts", {})
        self._settings["alerts"]["sound_enabled"] = bool(sound_enabled)
        self._settings["alerts"]["toast_enabled"] = bool(toast_enabled)
        self._write(self._settings)

    def add_folder(self, path: str) -> bool:
        path = os.path.normpath(path)
        folders = self._settings["monitoring"].setdefault("folders", [])
        if path in folders:
            return False
        folders.append(path)
        self._write(self._settings)
        return True

    def remove_folder(self, path: str) -> bool:
        path = os.path.normpath(path)
        folders = self._settings["monitoring"].setdefault("folders", [])
        if path not in folders:
            return False
        folders.remove(path)
        self._write(self._settings)
        return True
