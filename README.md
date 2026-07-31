# HomeWork Tracker

Desktop assignment tracking widget for Purdue Global with Google Calendar sync.

## Features

- Frameless desktop widget (pywebview) with multiple layouts (agenda, calendar, board, compact)
- Assignment tracking with due dates, points, grades, and discussion post progress
- Google Calendar sync (per-user OAuth, creates dedicated "HomeWork Tracker" calendar)
- Customizable themes, scenes, fonts, and density
- System tray integration
- Always-on-top option

## Architecture

- **Backend:** FastAPI + SQLite on CT205 (10.0.0.237:8000) — REST API for terms, courses, assignments, stats under /api/v1/
- **MCP Server:** FastMCP on CT205 port 8001 — 16 tools wrapping the REST API
- **Widget:** pywebview desktop app — talks to backend over LAN
- **Calendar:** Google Calendar API via OAuth — per-user token, no shared credentials

## Install

```powershell
# Run the installer from the project directory
powershell -ExecutionPolicy Bypass -File install.ps1
```

The installer will:
1. Check for Python 3.10+
2. Prompt for the API server address
3. Create a virtual environment and install dependencies
4. Set up a startup scheduled task and desktop shortcut
5. Optionally launch the app

## Google OAuth Setup (required for Calendar Sync)

**This repository ships no Google credentials. You must supply your own.**

1. In the [Google Cloud Console](https://console.cloud.google.com/), create a project and enable the **Google Calendar API**.
2. Under *APIs & Services → Credentials*, create an **OAuth client ID** of type **Desktop app**.
3. Download the client JSON and save it as `credentials.json` in the install directory
   (next to `app.py`). Use `credentials.json.example` as the shape reference.
4. `credentials.json` and the `token.json` produced after your first authorization are
   both gitignored. Never commit either file.

## Calendar Sync

First sync click opens your browser for Google OAuth authorization. After that, syncs are one-click. Each user gets their own token and their own "HomeWork Tracker" calendar.

## Files

| File | Purpose |
|------|---------|
| `app.py` | pywebview app, JsApi bridge, tray icon |
| `cal_sync.py` | Google Calendar sync module |
| `credentials.json` | Your own Google OAuth client (not distributed — see Google OAuth Setup) |
| `static/index.html` | Frontend (React, single-file) |
| `icon/app-icon.png` | App icon |
| `icon/app-icon.ico` | App icon (Windows ICO) |
| `install.ps1` | Installer script |

## Requirements

- Windows 10/11
- Python 3.10+
- Network access to the backend server
