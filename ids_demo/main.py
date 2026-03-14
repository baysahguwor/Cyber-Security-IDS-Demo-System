from __future__ import annotations

import sys
import threading
from typing import Dict

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QDialog

from alerts.telegram_alert import TelegramAlerter
from config import ConfigManager
from database import DatabaseManager
from detection.attack_simulator import AttackSimulator
from detection.webcam_capture import WebcamCapture
from monitoring.file_monitor import FileMonitorService
from monitoring.usb_monitor import USBMonitorService
from ui.dashboard import DashboardWindow
from ui.login_window import LoginWindow
from ui.settings_window import SettingsWindow
from ui.startup_check import StartupCheckDialog


class EventBridge(QObject):
    new_event = Signal(str, str)
    processed_event = Signal(dict)


class IDSApplication:
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.services_started = False

        self.config = ConfigManager()
        self.db = DatabaseManager()
        self.webcam = WebcamCapture()
        self.telegram = TelegramAlerter(self.config)
        self.simulator = AttackSimulator()

        self.bridge = EventBridge()
        self.bridge.new_event.connect(self._handle_event)
        self.bridge.processed_event.connect(self._apply_processed_event)

        self.file_monitor = FileMonitorService(self._file_event_callback)
        self.usb_monitor = USBMonitorService(self._usb_event_callback)

        self.login_window = LoginWindow(self.config.validate_login)
        self.dashboard = DashboardWindow()
        self.settings_window = SettingsWindow(self.config, self.db, self.telegram)

        self.login_window.login_success.connect(self._on_login_success)
        self.dashboard.settings_requested.connect(self._open_settings)
        self.dashboard.simulate_requested.connect(self._simulate_remote_attack)
        self.settings_window.folders_changed.connect(self._reload_folders)
        self.settings_window.telegram_changed.connect(self._refresh_dashboard)
        self.settings_window.logs_changed.connect(self._refresh_dashboard)
        self.settings_window.alert_preferences_changed.connect(self._apply_alert_preferences)

        self.qt_app.aboutToQuit.connect(self.shutdown)
        self._apply_alert_preferences()

    def _on_login_success(self) -> None:
        self.login_window.close()
        self._start_services()
        self._refresh_dashboard()
        self.dashboard.show()

    def _start_services(self) -> None:
        folders = self.config.get_monitored_folders()
        self.file_monitor.set_folders(folders)
        self.usb_monitor.start()
        self.services_started = True

    def _reload_folders(self) -> None:
        folders = self.config.get_monitored_folders()
        self.file_monitor.set_folders(folders)
        self._refresh_dashboard()

    def _open_settings(self) -> None:
        self.settings_window._load_values()
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _simulate_remote_attack(self) -> None:
        attack_type, desc = self.simulator.simulate_remote_attack()
        self.bridge.new_event.emit(attack_type, desc)

    def _apply_alert_preferences(self) -> None:
        alert_prefs = self.config.get_alert_preferences()
        self.dashboard.set_alert_preferences(toast_enabled=alert_prefs.get("toast_enabled", True))

    def _play_alert_sound(self) -> None:
        prefs = self.config.get_alert_preferences()
        if not prefs.get("sound_enabled", True):
            return

        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONHAND)
        except Exception:
            self.qt_app.beep()

    def _file_event_callback(self, description: str) -> None:
        self.bridge.new_event.emit("FILE_EVENT", description)

    def _usb_event_callback(self, description: str) -> None:
        self.bridge.new_event.emit("USB_EVENT", description)

    def _handle_event(self, attack_type: str, description: str) -> None:
        worker = threading.Thread(
            target=self._process_event_worker,
            args=(attack_type, description),
            daemon=True,
        )
        worker.start()

    def _process_event_worker(self, attack_type: str, description: str) -> None:
        timestamp = self.db.now_iso()
        photo_paths = self.webcam.capture_images(count=3, prefix=attack_type.lower())
        p = photo_paths + ["", "", ""]

        event_id = self.db.insert_event(
            attack_type=attack_type,
            event_time=timestamp,
            description=description,
            photo1=p[0],
            photo2=p[1],
            photo3=p[2],
        )

        self.telegram.send_alert(
            attack_type=attack_type,
            timestamp=timestamp,
            description=description,
            photo_path=p[0] or None,
        )

        self.bridge.processed_event.emit(
            {
                "id": event_id,
                "attack_type": attack_type,
                "event_time": timestamp,
                "description": description,
                "photos": [p[0], p[1], p[2]],
                "title": f"ALERT: {attack_type}",
            }
        )

    def _apply_processed_event(self, payload: Dict) -> None:
        self._play_alert_sound()
        self.dashboard.event_received.emit(payload)
        self.dashboard.append_log(
            payload["id"],
            payload["event_time"],
            payload["attack_type"],
            payload["description"],
            payload["photos"],
        )
        self._refresh_dashboard(update_logs=False)

    def _refresh_dashboard(self, update_logs: bool = True) -> None:
        counts = self.db.get_counts()
        self.dashboard.update_counters(counts)

        if update_logs:
            rows = self.db.fetch_recent_events(limit=100)
            self.dashboard.set_logs(rows)

        tg_cfg = self.config.get_telegram_config()
        telegram_ok = bool(tg_cfg.bot_token and tg_cfg.chat_id)

        self.dashboard.update_system_status(
            monitoring_active=self.services_started,
            webcam_active=self.webcam.is_available(),
            telegram_active=telegram_ok,
            monitored_folders=len(self.config.get_monitored_folders()),
        )

    def shutdown(self) -> None:
        try:
            self.file_monitor.stop()
        except Exception:
            pass
        try:
            self.usb_monitor.stop()
        except Exception:
            pass

    def run(self) -> int:
        checks = {
            "database": True,
            "webcam": self.webcam.is_available(),
            "telegram": bool(self.config.get_telegram_config().bot_token and self.config.get_telegram_config().chat_id),
            "folders": len(self.config.get_monitored_folders()) > 0,
        }
        details = {
            "database": f"SQLite path: {self.db.db_path}",
            "webcam": "Camera detected and ready" if checks["webcam"] else "No webcam detected; capture will be skipped",
            "telegram": "Telegram credentials configured" if checks["telegram"] else "Telegram token/chat ID missing",
            "folders": (
                f"{len(self.config.get_monitored_folders())} folder(s) configured"
                if checks["folders"]
                else "No monitored folders configured yet"
            ),
        }

        startup = StartupCheckDialog(checks, details)
        if startup.exec() != QDialog.Accepted:
            return 0

        self.login_window.show()
        return self.qt_app.exec()


def main() -> None:
    app = IDSApplication()
    raise SystemExit(app.run())


if __name__ == "__main__":
    main()
