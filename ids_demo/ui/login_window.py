from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoginWindow(QWidget):
    login_success = Signal()

    def __init__(self, auth_callback) -> None:
        super().__init__()
        self.auth_callback = auth_callback
        self.setWindowTitle("IDS Demo Login")
        self.setMinimumSize(700, 420)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setObjectName("LoginCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(14)

        title = QLabel("Cyber Security IDS Demo")
        title.setObjectName("LoginTitle")
        subtitle = QLabel("Security Operations Access")
        subtitle.setObjectName("LoginSubtitle")

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.status = QLabel("")
        self.status.setObjectName("LoginStatus")

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.login_btn = QPushButton("Access Dashboard")
        self.login_btn.clicked.connect(self._try_login)
        button_row.addWidget(self.login_btn)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.user_input)
        card_layout.addWidget(self.pass_input)
        card_layout.addWidget(self.status)
        card_layout.addLayout(button_row)

        root.addStretch(1)
        root.addWidget(card, alignment=Qt.AlignCenter)
        root.addStretch(1)

        self.setStyleSheet(
            """
            QWidget {
                background: #071018;
                color: #d7f5ff;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            #LoginCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0c1f2d, stop:1 #071018);
                border: 1px solid #19e3b5;
                border-radius: 14px;
                min-width: 420px;
            }
            #LoginTitle {
                font-size: 28px;
                font-weight: 700;
                color: #38d4ff;
            }
            #LoginSubtitle {
                color: #8eb8c9;
                margin-bottom: 6px;
            }
            QLineEdit {
                background: #0f2738;
                border: 1px solid #1e3b4c;
                border-radius: 8px;
                padding: 10px;
                color: #ddf7ff;
            }
            QLineEdit:focus {
                border: 1px solid #34f5c5;
            }
            QPushButton {
                background: #123349;
                border: 1px solid #35f8c9;
                border-radius: 8px;
                padding: 10px 16px;
                color: #dfffff;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #17415c;
            }
            #LoginStatus {
                color: #ff7070;
                min-height: 20px;
            }
            """
        )

    def _try_login(self) -> None:
        if self.auth_callback(self.user_input.text().strip(), self.pass_input.text()):
            self.status.setText("")
            self.login_success.emit()
            return
        self.status.setText("Invalid username or password")
