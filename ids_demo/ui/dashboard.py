from __future__ import annotations

import os
from typing import Dict, List, Tuple

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, QSize, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDialog,
)


class AnimatedCounter(QLabel):
    def __init__(self, title: str, color: str) -> None:
        super().__init__("0")
        self._value = 0
        self._target = 0
        self._step = 1
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self.setObjectName("CounterValue")
        self.setStyleSheet(f"color: {color};")
        self.title = title

    def set_target(self, value: int) -> None:
        self._target = value
        diff = abs(self._target - self._value)
        self._step = max(1, diff // 20)
        if not self._timer.isActive():
            self._timer.start(18)

    def _tick(self) -> None:
        if self._value < self._target:
            self._value = min(self._target, self._value + self._step)
        elif self._value > self._target:
            self._value = max(self._target, self._value - self._step)
        else:
            self._timer.stop()
        self.setText(str(self._value))


class LivePulseWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(100, 100)
        self._pulse = 0
        self._attack_mode_ticks = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _tick(self) -> None:
        self._pulse = (self._pulse + 4) % 100
        if self._attack_mode_ticks > 0:
            self._attack_mode_ticks -= 1
        self.update()

    def trigger_attack(self) -> None:
        self._attack_mode_ticks = 40

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(12, 12, -12, -12)
        center = rect.center()
        max_radius = min(rect.width(), rect.height()) // 2

        if self._attack_mode_ticks > 0:
            base_color = QColor("#ff6f5f")
            ring_color = QColor("#ffb68f")
        else:
            base_color = QColor("#37f5b3")
            ring_color = QColor("#35cfff")

        # Draw three expanding rings for a radar-like live effect.
        for i in range(3):
            offset = (self._pulse + i * 33) % 100
            radius = int((offset / 100) * max_radius)
            alpha = max(30, 180 - offset)
            pen = QPen(ring_color)
            pen.setWidth(2)
            ring_color.setAlpha(alpha)
            pen.setColor(ring_color)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)

        painter.setPen(Qt.NoPen)
        painter.setBrush(base_color)
        painter.drawEllipse(center, 10, 10)


class AttackDistributionWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.target_data = {
            "FILE_EVENT": 0,
            "USB_EVENT": 0,
            "REMOTE_ATTACK": 0,
        }
        self.current_data = {
            "FILE_EVENT": 0,
            "USB_EVENT": 0,
            "REMOTE_ATTACK": 0,
        }
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate_step)
        self.setMinimumHeight(210)

    def update_data(self, data: Dict[str, int]) -> None:
        for key in self.target_data:
            self.target_data[key] = int(data.get(key, 0))
        if not self._timer.isActive():
            self._timer.start(20)

    def _animate_step(self) -> None:
        changed = False
        for key in self.current_data:
            cur = self.current_data[key]
            tgt = self.target_data[key]
            if cur < tgt:
                self.current_data[key] = min(tgt, cur + max(1, (tgt - cur) // 6))
                changed = True
            elif cur > tgt:
                self.current_data[key] = max(tgt, cur - max(1, (cur - tgt) // 6))
                changed = True
        self.update()
        if not changed:
            self._timer.stop()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(18, 18, -18, -32)
        max_val = max(
            1,
            self.current_data.get("FILE_EVENT", 0),
            self.current_data.get("USB_EVENT", 0),
            self.current_data.get("REMOTE_ATTACK", 0),
        )

        labels = ["FILE_EVENT", "USB_EVENT", "REMOTE_ATTACK"]
        colors = [QColor("#35cfff"), QColor("#37f5b3"), QColor("#ffa754")]

        bar_width = rect.width() // 8
        spacing = rect.width() // 5
        start_x = rect.x() + spacing // 2

        painter.setPen(QPen(QColor("#456777"), 1))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        for i, label in enumerate(labels):
            value = self.current_data.get(label, 0)
            h = int((value / max_val) * (rect.height() - 20))
            x = start_x + i * spacing
            y = rect.bottom() - h

            painter.setBrush(colors[i])
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bar_width, h, 5, 5)

            painter.setPen(QColor("#9cc8d6"))
            painter.drawText(x - 12, rect.bottom() + 18, label.replace("_", " "))
            painter.drawText(x + 4, y - 6, str(value))


class PhotoViewerDialog(QDialog):
    def __init__(self, photos: List[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.photos = photos
        self.index = 0
        self.setWindowTitle("Captured Evidence Photos")
        self.resize(980, 700)

        root = QVBoxLayout(self)

        self.image_label = QLabel("No image")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(440)
        self.image_label.setStyleSheet("background:#081622; border:1px solid #1c475f; border-radius:10px;")

        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("color:#87bcd0;")

        nav_row = QHBoxLayout()
        prev_btn = QPushButton("Previous")
        next_btn = QPushButton("Next")
        prev_btn.clicked.connect(self._show_prev)
        next_btn.clicked.connect(self._show_next)
        nav_row.addWidget(prev_btn)
        nav_row.addWidget(next_btn)
        nav_row.addStretch(1)

        self.thumb_list = QListWidget()
        self.thumb_list.setViewMode(QListWidget.IconMode)
        self.thumb_list.setResizeMode(QListWidget.Adjust)
        self.thumb_list.setMovement(QListWidget.Static)
        self.thumb_list.setSpacing(10)
        self.thumb_list.setIconSize(QSize(120, 90))
        self.thumb_list.setFixedHeight(130)
        self.thumb_list.currentRowChanged.connect(self._set_index)

        for photo in self.photos:
            item = QListWidgetItem()
            pix = QPixmap(photo)
            if pix.isNull():
                thumb = QPixmap(120, 90)
                thumb.fill(QColor("#2b3f4d"))
            else:
                thumb = pix.scaled(120, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(thumb))
            item.setText(os.path.basename(photo))
            self.thumb_list.addItem(item)

        root.addWidget(self.image_label)
        root.addWidget(self.meta_label)
        root.addLayout(nav_row)
        root.addWidget(self.thumb_list)

        if self.photos:
            self.thumb_list.setCurrentRow(0)
            self._show_image(0)

    def _set_index(self, idx: int) -> None:
        if idx >= 0:
            self._show_image(idx)

    def _show_prev(self) -> None:
        if not self.photos:
            return
        self.index = (self.index - 1) % len(self.photos)
        self.thumb_list.setCurrentRow(self.index)

    def _show_next(self) -> None:
        if not self.photos:
            return
        self.index = (self.index + 1) % len(self.photos)
        self.thumb_list.setCurrentRow(self.index)

    def _show_image(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.photos):
            return
        self.index = idx
        path = self.photos[idx]
        pix = QPixmap(path)
        if pix.isNull():
            self.image_label.setText("Unable to load image")
            self.meta_label.setText(path)
            return

        scaled = pix.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.meta_label.setText(path)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._show_image(self.index)


class ToastPopup(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("ToastPopup")
        self.setWindowFlags(Qt.SubWindow)
        self.hide()

        layout = QVBoxLayout(self)
        self.title = QLabel("")
        self.title.setObjectName("ToastTitle")
        self.body = QLabel("")
        self.body.setWordWrap(True)
        self.body.setObjectName("ToastBody")
        layout.addWidget(self.title)
        layout.addWidget(self.body)

        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_toast(self, title: str, body: str) -> None:
        self.title.setText(title)
        self.body.setText(body)
        self.adjustSize()

        parent_size = self.parent().size()
        self.move(parent_size.width() - self.width() - 24, 26)
        self.show()
        self.raise_()

        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(450)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._anim = anim

        self._hide_timer.start(3500)


class DashboardWindow(QMainWindow):
    event_received = Signal(dict)
    settings_requested = Signal()
    simulate_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cyber Security IDS Dashboard")
        self.toast_enabled = True
        self._status_tick = 0
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.alert_banner = QLabel("SYSTEM ONLINE")
        self.alert_banner.setObjectName("AlertBanner")
        self.alert_banner.setAlignment(Qt.AlignCenter)

        header_row = QHBoxLayout()
        title = QLabel("Security Operations Center")
        title.setObjectName("HeaderTitle")
        self.monitor_activity = QLabel("Live Monitoring: ACTIVE")
        self.monitor_activity.setObjectName("MonitorLive")
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        self.sim_btn = QPushButton("Simulate Remote Attack")
        self.sim_btn.clicked.connect(self.simulate_requested.emit)
        header_row.addWidget(title)
        header_row.addSpacing(12)
        header_row.addWidget(self.monitor_activity)
        header_row.addStretch(1)
        header_row.addWidget(self.settings_btn)
        header_row.addWidget(self.sim_btn)

        counters_grid = QGridLayout()
        self.counter_total = self._create_counter_card("Total Events", "#35cfff")
        self.counter_file = self._create_counter_card("File Events", "#37f5b3")
        self.counter_usb = self._create_counter_card("USB Events", "#f2e56e")
        self.counter_remote = self._create_counter_card("Remote Attacks", "#ffa754")

        counters_grid.addWidget(self.counter_total["card"], 0, 0)
        counters_grid.addWidget(self.counter_file["card"], 0, 1)
        counters_grid.addWidget(self.counter_usb["card"], 0, 2)
        counters_grid.addWidget(self.counter_remote["card"], 0, 3)

        lower_row = QHBoxLayout()

        left_box = QFrame()
        left_box.setObjectName("Panel")
        left_layout = QVBoxLayout(left_box)
        left_layout.addWidget(QLabel("Attack Categories"))
        self.chart = AttackDistributionWidget()
        left_layout.addWidget(self.chart)

        right_box = QFrame()
        right_box.setObjectName("Panel")
        right_layout = QVBoxLayout(right_box)
        right_layout.addWidget(QLabel("System Status"))
        self.status_monitor = QLabel("Monitoring: Unknown")
        self.status_webcam = QLabel("Webcam: Unknown")
        self.status_telegram = QLabel("Telegram: Unknown")
        self.status_folders = QLabel("Monitored Folders: 0")
        for lbl in [self.status_monitor, self.status_webcam, self.status_telegram, self.status_folders]:
            lbl.setObjectName("StatusLine")
            right_layout.addWidget(lbl)
        self.live_pulse = LivePulseWidget()
        right_layout.addWidget(self.live_pulse, alignment=Qt.AlignCenter)

        lower_row.addWidget(left_box, 3)
        lower_row.addWidget(right_box, 2)

        logs_box = QFrame()
        logs_box.setObjectName("Panel")
        logs_layout = QVBoxLayout(logs_box)
        logs_layout.addWidget(QLabel("Recent Attack Logs"))
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Time", "Attack Type", "Description", "View Photos", "ID"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(4, True)
        self.table.setAlternatingRowColors(True)
        logs_layout.addWidget(self.table)

        layout.addWidget(self.alert_banner)
        layout.addLayout(header_row)
        layout.addLayout(counters_grid)
        layout.addLayout(lower_row)
        layout.addWidget(logs_box, 1)

        self.setCentralWidget(root)
        self.showMaximized()

        self.toast = ToastPopup(root)

        self.event_received.connect(self._handle_new_event)

        self._activity_timer = QTimer()
        self._activity_timer.timeout.connect(self._animate_monitor_label)
        self._activity_timer.start(360)

        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #061017;
                color: #d8f6ff;
                font-family: 'Trebuchet MS';
                font-size: 13px;
            }
            #HeaderTitle {
                font-size: 24px;
                font-weight: 700;
                color: #3dd3ff;
            }
            #MonitorLive {
                color: #5cf0c5;
                font-weight: 700;
                border: 1px solid #1d6a59;
                border-radius: 8px;
                padding: 6px 10px;
                background: #0d2c2a;
            }
            #AlertBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a2233, stop:1 #0f3f47);
                border: 1px solid #36f6c4;
                border-radius: 8px;
                font-weight: 700;
                padding: 8px;
                min-height: 32px;
            }
            QFrame#Panel {
                background: #0b1e2a;
                border: 1px solid #153547;
                border-radius: 10px;
                padding: 8px;
            }
            QFrame#CounterCard {
                background: #0b1f2d;
                border: 1px solid #154258;
                border-radius: 10px;
                min-height: 98px;
            }
            QLabel#CounterTitle {
                color: #8dbfd0;
            }
            QLabel#CounterValue {
                font-size: 28px;
                font-weight: 700;
            }
            QPushButton {
                background: #102f43;
                border: 1px solid #35f9c8;
                border-radius: 8px;
                padding: 9px 13px;
                color: #dfffff;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #184661;
            }
            QLabel#StatusLine {
                padding: 5px;
                border-radius: 6px;
                background: #0e2a38;
                border: 1px solid #1a4254;
            }
            QTableWidget {
                background: #081622;
                alternate-background-color: #0d1f2b;
                border: 1px solid #17384a;
                gridline-color: #1f4356;
            }
            QHeaderView::section {
                background: #10344b;
                color: #d7f5ff;
                padding: 6px;
                border: 1px solid #245068;
            }
            QFrame#ToastPopup {
                background: #123042;
                border: 1px solid #37f5b3;
                border-radius: 9px;
                min-width: 320px;
                max-width: 420px;
                padding: 8px;
            }
            QLabel#ToastTitle {
                font-size: 14px;
                font-weight: 700;
                color: #73ffe0;
            }
            QLabel#ToastBody {
                color: #c8ebf7;
            }
            """
        )

        self._run_startup_animations()

    def _run_startup_animations(self) -> None:
        cards = [
            self.counter_total["card"],
            self.counter_file["card"],
            self.counter_usb["card"],
            self.counter_remote["card"],
        ]
        for idx, card in enumerate(cards):
            effect = QGraphicsOpacityEffect(card)
            effect.setOpacity(0.0)
            card.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(520)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.setLoopCount(1)
            QTimer.singleShot(120 * idx, anim.start)
            setattr(self, f"_card_anim_{idx}", anim)

    def _animate_monitor_label(self) -> None:
        self._status_tick = (self._status_tick + 1) % 4
        dots = "." * self._status_tick
        self.monitor_activity.setText(f"Live Monitoring: ACTIVE{dots}")

    def _create_counter_card(self, title: str, color: str):
        card = QFrame()
        card.setObjectName("CounterCard")
        layout = QVBoxLayout(card)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("CounterTitle")
        counter = AnimatedCounter(title, color)
        layout.addWidget(title_lbl)
        layout.addWidget(counter)
        return {"card": card, "counter": counter}

    def set_alert_preferences(self, toast_enabled: bool) -> None:
        self.toast_enabled = bool(toast_enabled)

    def update_counters(self, counts: Dict[str, int]) -> None:
        self.counter_total["counter"].set_target(counts.get("total", 0))
        self.counter_file["counter"].set_target(counts.get("FILE_EVENT", 0))
        self.counter_usb["counter"].set_target(counts.get("USB_EVENT", 0))
        self.counter_remote["counter"].set_target(counts.get("REMOTE_ATTACK", 0))
        self.chart.update_data(counts)

    def update_system_status(
        self,
        monitoring_active: bool,
        webcam_active: bool,
        telegram_active: bool,
        monitored_folders: int,
    ) -> None:
        self.status_monitor.setText(f"Monitoring: {'Active' if monitoring_active else 'Stopped'}")
        self.status_webcam.setText(f"Webcam: {'Available' if webcam_active else 'Not Detected'}")
        self.status_telegram.setText(f"Telegram: {'Connected' if telegram_active else 'Not Configured/Failed'}")
        self.status_folders.setText(f"Monitored Folders: {monitored_folders}")

    def set_logs(self, rows: List[Tuple]) -> None:
        self.table.setRowCount(0)
        for row in rows:
            event_id, attack_type, event_time, desc, p1, p2, p3 = row
            self._append_row(event_id, event_time, attack_type, desc, [p1, p2, p3])

    def append_log(self, event_id: int, event_time: str, attack_type: str, desc: str, photos: List[str]) -> None:
        self._append_row(event_id, event_time, attack_type, desc, photos, prepend=True)

    def _append_row(
        self,
        event_id: int,
        event_time: str,
        attack_type: str,
        desc: str,
        photos: List[str],
        prepend: bool = False,
    ) -> None:
        row_idx = 0 if prepend else self.table.rowCount()
        self.table.insertRow(row_idx)
        self.table.setItem(row_idx, 0, QTableWidgetItem(event_time))
        self.table.setItem(row_idx, 1, QTableWidgetItem(attack_type))
        self.table.setItem(row_idx, 2, QTableWidgetItem(desc))

        btn = QPushButton("View")
        btn.clicked.connect(lambda: self._show_photos(photos))
        self.table.setCellWidget(row_idx, 3, btn)
        self.table.setItem(row_idx, 4, QTableWidgetItem(str(event_id)))

    def _show_photos(self, photos: List[str]) -> None:
        valid = [p for p in photos if p and os.path.exists(p)]
        if not valid:
            QMessageBox.information(self, "Photos", "No photos captured for this event.")
            return
        viewer = PhotoViewerDialog(valid, self)
        viewer.exec()

    def flash_alert(self, text: str) -> None:
        self.alert_banner.setText(text)
        anim = QPropertyAnimation(self.alert_banner, b"windowOpacity")
        anim.setDuration(1000)
        anim.setStartValue(0.45)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutBounce)
        anim.start()
        self._last_anim = anim

    def show_attack_toast(self, title: str, description: str) -> None:
        if self.toast_enabled:
            self.toast.show_toast(title, description)

    def _handle_new_event(self, payload: dict) -> None:
        title = payload.get("title", "ALERT")
        desc = payload.get("description", "")
        self.live_pulse.trigger_attack()
        self.flash_alert(title)
        self.show_attack_toast(title, desc)
