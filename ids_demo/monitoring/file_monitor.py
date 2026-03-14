from __future__ import annotations

import os
import threading
from typing import Callable, List

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _WatchHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]) -> None:
        super().__init__()
        self.callback = callback

    def _emit(self, event: FileSystemEvent, action: str) -> None:
        src = os.path.normpath(event.src_path)
        if event.is_directory:
            kind = "Folder"
        else:
            kind = "File"
        self.callback(f"{kind} {action}: {src}")

    def on_created(self, event: FileSystemEvent) -> None:
        self._emit(event, "created")

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._emit(event, "deleted")

    def on_modified(self, event: FileSystemEvent) -> None:
        # Ignore modified noise to keep the dashboard readable.
        return

    def on_moved(self, event: FileSystemEvent) -> None:
        src = os.path.normpath(event.src_path)
        dst = os.path.normpath(getattr(event, "dest_path", ""))
        kind = "Folder" if event.is_directory else "File"
        self.callback(f"{kind} renamed: {src} -> {dst}")


class FileMonitorService:
    def __init__(self, callback: Callable[[str], None]) -> None:
        self.callback = callback
        self.observer = Observer()
        self.handler = _WatchHandler(self.callback)
        self._watched_folders: List[str] = []
        self._started = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self.observer.start()
            self._started = True

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self.observer.stop()
            self.observer.join(timeout=2)
            self._started = False

    def set_folders(self, folders: List[str]) -> None:
        with self._lock:
            # Rebuild observer schedules when folders change.
            if self._started:
                self.observer.stop()
                self.observer.join(timeout=2)
                self.observer = Observer()
                self.handler = _WatchHandler(self.callback)
                self._started = False

            self._watched_folders = []
            for folder in folders:
                if os.path.isdir(folder):
                    self.observer.schedule(self.handler, folder, recursive=True)
                    self._watched_folders.append(folder)

            self.observer.start()
            self._started = True

    @property
    def watched_folders(self) -> List[str]:
        return list(self._watched_folders)
