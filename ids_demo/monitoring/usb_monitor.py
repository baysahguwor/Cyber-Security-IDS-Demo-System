from __future__ import annotations

import threading
import time
from typing import Callable, Dict, Set

import psutil


class USBMonitorService:
    def __init__(self, callback: Callable[[str], None], poll_seconds: int = 2) -> None:
        self.callback = callback
        self.poll_seconds = poll_seconds
        self._running = False
        self._thread: threading.Thread | None = None
        self._known_mounts: Set[str] = set()

    @staticmethod
    def _get_removable_devices() -> Dict[str, str]:
        devices: Dict[str, str] = {}
        for part in psutil.disk_partitions(all=False):
            opts = (part.opts or "").lower()
            if "removable" in opts or "usb" in opts:
                devices[part.mountpoint] = part.device
        return devices

    def _loop(self) -> None:
        self._known_mounts = set(self._get_removable_devices().keys())
        while self._running:
            current = self._get_removable_devices()
            current_mounts = set(current.keys())
            new_mounts = current_mounts - self._known_mounts

            for mount in new_mounts:
                device = current.get(mount, "Unknown USB")
                description = (
                    "USB Device Detected\n"
                    f"Device Name: {device}\n"
                    f"Drive Letter: {mount}"
                )
                self.callback(description)

            self._known_mounts = current_mounts
            time.sleep(self.poll_seconds)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
