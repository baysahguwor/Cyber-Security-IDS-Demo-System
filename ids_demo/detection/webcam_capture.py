from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import cv2

from config import PHOTOS_DIR


class WebcamCapture:
    def __init__(self, photos_dir: Path = PHOTOS_DIR) -> None:
        self.photos_dir = photos_dir
        self.photos_dir.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        cap = cv2.VideoCapture(0)
        ok = cap.isOpened()
        cap.release()
        return ok

    def capture_images(self, count: int = 3, prefix: str = "event") -> List[str]:
        paths: List[str] = []
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return paths

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for i in range(1, count + 1):
            success, frame = cap.read()
            if not success:
                continue
            filename = self.photos_dir / f"{prefix}_{timestamp}_{i}.jpg"
            cv2.imwrite(str(filename), frame)
            paths.append(str(filename))

        cap.release()
        return paths
