from __future__ import annotations

from datetime import datetime, time

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsWindow(QWidget):
    folders_changed = Signal()
    credentials_changed = Signal()
    telegram_changed = Signal()
    logs_changed = Signal()
    alert_preferences_changed = Signal()

    def __init__(self, config, database, telegram_alerter) -> None:
        super().__init__()
        self.config = config
        self.database = database
        self.telegram_alerter = telegram_alerter
        self.setWindowTitle("IDS Settings")
        self.resize(900, 620)
        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        tabs.addTab(self._telegram_tab(), "Telegram")
        tabs.addTab(self._folders_tab(), "Folder Monitoring")
        tabs.addTab(self._alerts_tab(), "Alert Behavior")
        tabs.addTab(self._user_tab(), "User Management")
        tabs.addTab(self._log_tab(), "Log Management")

        layout.addWidget(tabs)

        self.setStyleSheet(
            """
            QWidget {
                background: #08141f;
                color: #d6f4ff;
                font-family: 'Trebuchet MS';
                font-size: 13px;
            }
            QFrame {
                background: #0c1f2d;
                border: 1px solid #1a4257;
                border-radius: 10px;
                padding: 8px;
            }
            QLineEdit, QListWidget, QDateEdit {
                background: #102736;
                border: 1px solid #20465a;
                border-radius: 7px;
                padding: 7px;
                color: #def8ff;
            }
            QPushButton {
                background: #133145;
                border: 1px solid #31f6c2;
                border-radius: 7px;
                padding: 8px 12px;
                color: #ddffff;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #18445f;
            }
            """
        )

    def _telegram_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        box = QFrame()
        form = QFormLayout(box)

        self.bot_token_input = QLineEdit()
        self.chat_id_input = QLineEdit()
        form.addRow("Bot Token", self.bot_token_input)
        form.addRow("Chat ID", self.chat_id_input)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save Telegram")
        save_btn.clicked.connect(self._save_telegram)
        test_btn = QPushButton("Test")
        test_btn.clicked.connect(self._test_telegram)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(test_btn)

        self.telegram_status = QLabel("")

        root.addWidget(box)
        root.addLayout(btn_row)
        root.addWidget(self.telegram_status)
        root.addStretch(1)
        return page

    def _folders_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)

        box = QFrame()
        box_layout = QVBoxLayout(box)
        self.folder_list = QListWidget()
        box_layout.addWidget(self.folder_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Folder")
        add_btn.clicked.connect(self._add_folder)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_folder)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)

        root.addWidget(box)
        root.addLayout(btn_row)
        root.addStretch(1)
        return page

    def _user_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        box = QFrame()
        form = QFormLayout(box)

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form.addRow("New Username", self.username_input)
        form.addRow("New Password", self.password_input)

        save_btn = QPushButton("Update Credentials")
        save_btn.clicked.connect(self._save_credentials)

        root.addWidget(box)
        root.addWidget(save_btn)
        root.addStretch(1)
        return page

    def _alerts_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)

        box = QFrame()
        box_layout = QVBoxLayout(box)

        self.sound_enabled_check = QCheckBox("Enable alert sound")
        self.toast_enabled_check = QCheckBox("Enable attack toast popup")
        box_layout.addWidget(self.sound_enabled_check)
        box_layout.addWidget(self.toast_enabled_check)

        save_btn = QPushButton("Save Alert Preferences")
        save_btn.clicked.connect(self._save_alert_preferences)

        self.alert_pref_status = QLabel("")

        root.addWidget(box)
        root.addWidget(save_btn)
        root.addWidget(self.alert_pref_status)
        root.addStretch(1)
        return page

    def _log_tab(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)

        export_box = QFrame()
        export_layout = QHBoxLayout(export_box)
        export_btn = QPushButton("Export Logs to CSV")
        export_btn.clicked.connect(self._export_logs)
        export_layout.addWidget(export_btn)

        delete_box = QFrame()
        delete_layout = QFormLayout(delete_box)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.delete_photos_check = QCheckBox("Delete associated photos")
        del_btn = QPushButton("Delete Logs by Date Range")
        del_btn.clicked.connect(self._delete_logs)

        delete_layout.addRow("Start Date", self.start_date)
        delete_layout.addRow("End Date", self.end_date)
        delete_layout.addRow("", self.delete_photos_check)
        delete_layout.addRow("", del_btn)

        root.addWidget(export_box)
        root.addWidget(delete_box)
        root.addStretch(1)
        return page

    def _load_values(self) -> None:
        tg = self.config.get_telegram_config()
        self.bot_token_input.setText(tg.bot_token)
        self.chat_id_input.setText(tg.chat_id)

        self.folder_list.clear()
        for folder in self.config.get_monitored_folders():
            self.folder_list.addItem(folder)

        alert_prefs = self.config.get_alert_preferences()
        self.sound_enabled_check.setChecked(alert_prefs.get("sound_enabled", True))
        self.toast_enabled_check.setChecked(alert_prefs.get("toast_enabled", True))

    def _save_telegram(self) -> None:
        self.config.update_telegram_config(
            self.bot_token_input.text().strip(),
            self.chat_id_input.text().strip(),
        )
        self.telegram_status.setText("Telegram settings saved.")
        self.telegram_changed.emit()

    def _save_alert_preferences(self) -> None:
        self.config.update_alert_preferences(
            sound_enabled=self.sound_enabled_check.isChecked(),
            toast_enabled=self.toast_enabled_check.isChecked(),
        )
        self.alert_pref_status.setText("Alert preferences saved.")
        self.alert_preferences_changed.emit()

    def _test_telegram(self) -> None:
        ok = self.telegram_alerter.test_connection()
        self.telegram_status.setText("Telegram OK" if ok else "Telegram test failed")

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        if self.config.add_folder(folder):
            self.folder_list.addItem(folder)
            self.folders_changed.emit()

    def _remove_folder(self) -> None:
        item = self.folder_list.currentItem()
        if not item:
            return
        path = item.text()
        if self.config.remove_folder(path):
            self.folder_list.takeItem(self.folder_list.row(item))
            self.folders_changed.emit()

    def _save_credentials(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Validation", "Username and password are required.")
            return
        self.config.update_credentials(username, password)
        self.credentials_changed.emit()
        QMessageBox.information(self, "Updated", "Credentials updated successfully.")

    def _export_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "events.csv", "CSV Files (*.csv)")
        if not path:
            return
        count = self.database.export_to_csv(path)
        QMessageBox.information(self, "Export Complete", f"Exported {count} events.")

    def _delete_logs(self) -> None:
        start_dt = datetime.combine(self.start_date.date().toPython(), time.min)
        end_dt = datetime.combine(self.end_date.date().toPython(), time.max)

        deleted = self.database.delete_logs_by_date_range(
            start_dt.isoformat(timespec="seconds"),
            end_dt.isoformat(timespec="seconds"),
            delete_photos=self.delete_photos_check.isChecked(),
        )
        self.logs_changed.emit()
        QMessageBox.information(self, "Deletion Complete", f"Deleted {deleted} events.")
