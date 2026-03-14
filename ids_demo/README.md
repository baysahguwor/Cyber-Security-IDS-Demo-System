# Cyber Security IDS Demo System

Educational intrusion detection demo with a cyber-security dashboard UI.

## Features

- File/folder monitoring with create, delete, and rename detection.
- USB insertion detection.
- One-click remote attack simulation.
- SQLite event logging with evidence photo paths.
- Webcam capture (3 photos per detected event).
- Telegram alerts with one attached evidence image.
- Login system with configurable credentials.
- Full-screen SOC style dashboard with animated counters and attack chart.
- Settings for Telegram, folder list, user credentials, and log management.

## Default Login

- Username: demo
- Password: demo

## Install

```powershell
cd .\ids_demo
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Storage

- SQLite database: database/events.db
- App settings: database/settings.json
- Captured images: photos/

## Notes

- This project is a demo for academic and educational presentations.
- It is not intended for production security operations.
