import csv
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import DB_PATH


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attack_type TEXT,
                    event_time TEXT,
                    description TEXT,
                    photo1 TEXT,
                    photo2 TEXT,
                    photo3 TEXT
                )
                """
            )
            conn.commit()

    def insert_event(
        self,
        attack_type: str,
        event_time: str,
        description: str,
        photo1: str = "",
        photo2: str = "",
        photo3: str = "",
    ) -> int:
        with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO events (attack_type, event_time, description, photo1, photo2, photo3)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (attack_type, event_time, description, photo1, photo2, photo3),
                )
                conn.commit()
                return int(cur.lastrowid)

    def fetch_recent_events(self, limit: int = 100) -> List[Tuple]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT id, attack_type, event_time, description, photo1, photo2, photo3
                FROM events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cur.fetchall()

    def get_counts(self) -> Dict[str, int]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            file_events = conn.execute(
                "SELECT COUNT(*) FROM events WHERE attack_type = 'FILE_EVENT'"
            ).fetchone()[0]
            usb_events = conn.execute(
                "SELECT COUNT(*) FROM events WHERE attack_type = 'USB_EVENT'"
            ).fetchone()[0]
            remote_events = conn.execute(
                "SELECT COUNT(*) FROM events WHERE attack_type = 'REMOTE_ATTACK'"
            ).fetchone()[0]

        return {
            "total": total,
            "FILE_EVENT": file_events,
            "USB_EVENT": usb_events,
            "REMOTE_ATTACK": remote_events,
        }

    def export_to_csv(self, output_path: str) -> int:
        rows = self.fetch_recent_events(limit=100000)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id",
                "attack_type",
                "event_time",
                "description",
                "photo1",
                "photo2",
                "photo3",
            ])
            writer.writerows(rows)
        return len(rows)

    def delete_logs_by_date_range(
        self,
        start_iso: str,
        end_iso: str,
        delete_photos: bool = False,
    ) -> int:
        with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    SELECT id, photo1, photo2, photo3
                    FROM events
                    WHERE event_time >= ? AND event_time <= ?
                    """,
                    (start_iso, end_iso),
                )
                rows = cur.fetchall()

                if delete_photos:
                    for _, p1, p2, p3 in rows:
                        for p in (p1, p2, p3):
                            if p and os.path.exists(p):
                                try:
                                    os.remove(p)
                                except OSError:
                                    pass

                conn.execute(
                    "DELETE FROM events WHERE event_time >= ? AND event_time <= ?",
                    (start_iso, end_iso),
                )
                conn.commit()
                return len(rows)

    @staticmethod
    def now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")
