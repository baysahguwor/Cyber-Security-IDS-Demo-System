from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class StartupCheckDialog(QDialog):
    def __init__(self, checks: Dict[str, bool], details: Dict[str, str], parent=None) -> None:
        super().__init__(parent)
        self.checks = checks
        self.details = details
        self.setWindowTitle("IDS Startup Readiness")
        self.resize(640, 420)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        title = QLabel("Pre-Launch System Readiness")
        title.setObjectName("StartupTitle")
        subtitle = QLabel("Validate key services before opening dashboard")
        subtitle.setObjectName("StartupSubtitle")

        root.addWidget(title)
        root.addWidget(subtitle)

        for name in ["database", "webcam", "telegram", "folders"]:
            row = QFrame()
            row.setObjectName("CheckRow")
            row_layout = QHBoxLayout(row)
            ok = self.checks.get(name, False)
            status = "READY" if ok else "CHECK"
            color = "#3cf7bc" if ok else "#ffb35f"

            left = QLabel(name.upper())
            right = QLabel(status)
            right.setStyleSheet(f"color:{color}; font-weight:700;")
            detail = QLabel(self.details.get(name, ""))
            detail.setObjectName("Detail")

            info_col = QVBoxLayout()
            info_col.addWidget(left)
            info_col.addWidget(detail)

            row_layout.addLayout(info_col)
            row_layout.addStretch(1)
            row_layout.addWidget(right)
            root.addWidget(row)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Exit")
        continue_btn = QPushButton("Continue to Login")
        cancel_btn.clicked.connect(self.reject)
        continue_btn.clicked.connect(self.accept)
        btn_row.addStretch(1)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(continue_btn)

        root.addStretch(1)
        root.addLayout(btn_row)

        self.setStyleSheet(
            """
            QDialog {
                background: #07131d;
                color: #d6f4ff;
                font-family: 'Trebuchet MS';
                font-size: 13px;
            }
            #StartupTitle {
                font-size: 24px;
                font-weight: 700;
                color: #43d7ff;
            }
            #StartupSubtitle {
                color: #8cb9cb;
                margin-bottom: 10px;
            }
            QFrame#CheckRow {
                background: #0d2231;
                border: 1px solid #1a4158;
                border-radius: 9px;
                padding: 8px;
            }
            QLabel#Detail {
                color: #8fbdd0;
            }
            QPushButton {
                background: #123449;
                border: 1px solid #35f9c8;
                border-radius: 8px;
                padding: 8px 12px;
                color: #dfffff;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #17475f;
            }
            """
        )
