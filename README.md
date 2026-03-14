# IDS Demo Documentation

## 1. Project Purpose

Cyber Security IDS Demo System is an educational desktop application that simulates basic intrusion detection behavior in a professional Security Operations Center style interface.

This project is designed for:
- cybersecurity presentations
- classroom and lab demonstrations
- academic project showcases
- portfolio demonstrations for security-themed software

It is intentionally built as a visual and functional demo, not as a production-grade intrusion detection platform.

## 2. What the Program Does

The application monitors selected folders and removable USB activity, allows one-click remote attack simulation, captures webcam evidence images when events occur, logs all events to SQLite, and can send Telegram alerts.

Main detection categories:
- FILE_EVENT
- USB_EVENT
- REMOTE_ATTACK

For each event, the app can:
- save event details to database/events.db
- capture up to 3 photos to photos/
- send Telegram alert text and one image
- update dashboard counters, chart, logs, and live alert visuals

## 3. Technology Stack

Backend and services:
- Python 3.10+
- sqlite3
- watchdog
- psutil
- opencv-python
- requests

Frontend:
- PySide6 desktop UI

## 4. Folder Structure

Key project files:
- main.py: app startup and controller flow
- config.py: credentials, folder list, Telegram config, alert preferences
- database.py: SQLite schema and event operations
- monitoring/file_monitor.py: file and folder event watcher
- monitoring/usb_monitor.py: USB insertion detection loop
- detection/webcam_capture.py: webcam capture service
- detection/attack_simulator.py: remote attack simulation payload
- alerts/telegram_alert.py: Telegram Bot API integration
- ui/login_window.py: login page
- ui/dashboard.py: SOC dashboard, animations, logs, photo viewer, toasts
- ui/settings_window.py: configuration tabs
- ui/startup_check.py: startup readiness panel

Runtime data paths:
- database/events.db
- database/settings.json
- photos/

## 5. Installation

From the project root:

```powershell
cd .\ids_demo
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If your machine has multiple Python versions, use the exact interpreter you want for the virtual environment.

## 6. Running the Program

```powershell
cd .\ids_demo
python main.py
```

Startup flow:
1. Readiness dialog appears (database, webcam, Telegram, monitored folders).
2. Click Continue to Login.
3. Sign in with default credentials (or updated credentials).
4. Dashboard opens in full screen.

Default login:
- username: demo
- password: demo

## 7. How to Use the Dashboard

Top actions:
- Settings: open configuration window
- Simulate Remote Attack: trigger demo remote intrusion event

Live panels:
- Overview Counters: Total Events, File Events, USB Events, Remote Attacks
- Attack Categories: animated bar chart distribution
- Recent Attack Logs: latest events with View Photos button
- System Status: monitor state, webcam status, Telegram status, monitored folder count
- Live pulse indicator and alert banner for active event feedback

Photo viewing:
- Click View in any log row to open the evidence photo viewer.
- Use Previous/Next or thumbnail strip to browse captured images.

## 8. Settings Guide

### 8.1 Telegram Tab

Fields:
- Bot Token
- Chat ID

Actions:
- Save Telegram
- Test

Purpose:
- enables sending event alerts to a Telegram chat

### 8.2 Folder Monitoring Tab

Actions:
- Add Folder
- Remove Selected

Purpose:
- defines directories watched for create/delete/rename events

### 8.3 Alert Behavior Tab

Options:
- Enable alert sound
- Enable attack toast popup

Purpose:
- control audible and visual immediate notifications

### 8.4 User Management Tab

Actions:
- set new username
- set new password

Purpose:
- update application login credentials stored in settings

### 8.5 Log Management Tab

Actions:
- Export Logs to CSV
- Delete logs by date range
- Optional: delete associated photos

Purpose:
- archive or clean event history for demo resets

## 9. Event Scenarios

### 9.1 File System Monitoring Event

Examples:
- file created
- file deleted
- file renamed
- folder created
- folder deleted
- folder renamed

Result:
- event logged as FILE_EVENT
- webcam capture attempt (3 images)
- Telegram alert attempt
- dashboard updates in real time

### 9.2 USB Detection Event

When removable media is inserted:
- event logged as USB_EVENT
- description includes device and drive
- webcam and Telegram flow triggered
- dashboard updates

### 9.3 Simulated Remote Attack Event

Using dashboard button:
- Simulate Remote Attack

Generated event:
- attack type REMOTE_ATTACK
- source IP and activity text (port scan simulation)
- webcam, logging, Telegram, and UI updates triggered

## 10. Presentation Tips

For a strong demo:
1. Configure Telegram before presenting.
2. Add one or two monitored folders with test files.
3. Keep webcam connected and permissions enabled.
4. Trigger one file event, one USB event, and one simulated remote attack.
5. Show logs table growth, attack distribution chart movement, and photo viewer.

## 11. Troubleshooting

### App does not start
- ensure dependencies are installed from requirements.txt
- confirm you are running inside the same environment where packages were installed

### No webcam photos captured
- verify camera is connected and not locked by another app
- app continues gracefully even if webcam is unavailable

### Telegram test fails
- verify bot token and chat id are correct
- ensure internet access is available
- test again after saving settings

### No file events appear
- confirm monitored folders are added in settings
- make sure changes happen inside selected folders

### USB events not detected
- USB detection relies on removable partition visibility from the OS
- try reconnecting the device and wait a few seconds for polling

## 12. Security and Scope Notice

This is a demonstration IDS system for learning and showcasing concepts.

It does not provide:
- hardened endpoint protection
- kernel-level threat detection
- enterprise-grade SOC integrations
- guaranteed forensic integrity

Use this project only for educational and demonstration purposes.
