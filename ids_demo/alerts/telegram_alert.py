from __future__ import annotations

from typing import Optional

import requests

from config import TelegramConfig


class TelegramAlerter:
    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    def _api_base(self, token: str) -> str:
        return f"https://api.telegram.org/bot{token}"

    def send_alert(
        self,
        attack_type: str,
        timestamp: str,
        description: str,
        photo_path: Optional[str] = None,
    ) -> bool:
        cfg: TelegramConfig = self.config_provider.get_telegram_config()
        if not cfg.bot_token or not cfg.chat_id:
            return False

        message = (
            "🚨 IDS ALERT DETECTED\n\n"
            f"Attack Type: {attack_type}\n"
            f"Time: {timestamp}\n\n"
            "Description:\n"
            f"{description}\n\n"
            "System: Demo IDS Monitor"
        )

        try:
            msg_resp = requests.post(
                f"{self._api_base(cfg.bot_token)}/sendMessage",
                data={"chat_id": cfg.chat_id, "text": message},
                timeout=8,
            )
            ok = msg_resp.ok

            if photo_path:
                with open(photo_path, "rb") as f:
                    photo_resp = requests.post(
                        f"{self._api_base(cfg.bot_token)}/sendPhoto",
                        data={"chat_id": cfg.chat_id, "caption": "Captured evidence image"},
                        files={"photo": f},
                        timeout=12,
                    )
                ok = ok and photo_resp.ok
            return ok
        except (requests.RequestException, OSError):
            return False

    def test_connection(self) -> bool:
        cfg: TelegramConfig = self.config_provider.get_telegram_config()
        if not cfg.bot_token:
            return False
        try:
            resp = requests.get(f"{self._api_base(cfg.bot_token)}/getMe", timeout=6)
            return resp.ok
        except requests.RequestException:
            return False
