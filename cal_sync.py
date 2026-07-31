"""Google Calendar sync for Homework Widget."""
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

log = logging.getLogger("hw-widget.cal")

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
BASE = Path(__file__).parent
TOKEN_FILE = BASE / "token.json"
CREDS_FILE = BASE / "credentials.json"
SYNC_MAP_FILE = BASE / "sync_map.json"

CALENDAR_SUMMARY = "HomeWork Tracker"


def _get_creds():
    """Get or refresh Google OAuth credentials."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {CREDS_FILE}. Place your Google OAuth credentials.json in the app directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _get_service():
    return build("calendar", "v3", credentials=_get_creds())


def _load_sync_map():
    try:
        return json.loads(SYNC_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_sync_map(m):
    SYNC_MAP_FILE.write_text(json.dumps(m, indent=2), encoding="utf-8")


def _find_or_create_calendar(service):
    cals = service.calendarList().list().execute().get("items", [])
    for c in cals:
        if c.get("summary") == CALENDAR_SUMMARY:
            return c["id"]
    body = {"summary": CALENDAR_SUMMARY, "timeZone": "America/Indiana/Indianapolis"}
    created = service.calendars().insert(body=body).execute()
    return created["id"]


def sync_assignments(assignments, courses):
    """Sync assignments with due dates to Google Calendar.
    Returns dict with created, updated, skipped, removed counts.
    """
    service = _get_service()
    cal_id = _find_or_create_calendar(service)
    sync_map = _load_sync_map()
    # Assignment Tracker API v1 shape: courses carry "short" (e.g. IT497), not "code".
    course_map = {c["id"]: c.get("short") or c.get("code") or c.get("name", "?") for c in courses}

    stats = {"created": 0, "updated": 0, "skipped": 0, "removed": 0, "errors": 0}
    seen_ids = set()

    for a in assignments:
        aid = a.get("id", "")
        # API v1 returns "due" (YYYY-MM-DD); older shape used "due_date".
        due = a.get("due") or a.get("due_date")
        if not due:
            stats["skipped"] += 1
            continue

        seen_ids.add(aid)
        course_label = course_map.get(a.get("course_id", ""), "")
        # API v1 returns "title" (already includes the unit) and "points_total".
        name = a.get("title") or a.get("name") or "Assignment"
        title = f"[{course_label}] {name}" if course_label else name
        status = a.get("status", "not-started")
        points = a.get("points_total", a.get("points", 0)) or 0
        description = f"Points: {points}\nStatus: {status}\nType: {a.get('type', 'assignment')}"

        try:
            due_dt = datetime.strptime(due[:10], "%Y-%m-%d")
            due_str = due_dt.strftime("%Y-%m-%d")
        except Exception:
            stats["errors"] += 1
            continue

        event_body = {
            "summary": title,
            "description": description,
            "start": {"date": due_str},
            "end": {"date": (due_dt + timedelta(days=1)).strftime("%Y-%m-%d")},
            "reminders": {"useDefault": False, "overrides": [
                {"method": "popup", "minutes": 1440},
                {"method": "popup", "minutes": 60},
            ]},
            # API v1 status vocabulary: not-started | in-progress | done
            "colorId": {
                "done": "10", "complete": "10",
                "in-progress": "5", "in_progress": "5",
                "overdue": "11",
            }.get(status, "7"),
        }

        try:
            if aid in sync_map:
                service.events().update(calendarId=cal_id, eventId=sync_map[aid], body=event_body).execute()
                stats["updated"] += 1
            else:
                ev = service.events().insert(calendarId=cal_id, body=event_body).execute()
                sync_map[aid] = ev["id"]
                stats["created"] += 1
        except Exception as e:
            log.warning("Sync error for %s: %s", aid, e)
            if aid in sync_map:
                try:
                    del sync_map[aid]
                    ev = service.events().insert(calendarId=cal_id, body=event_body).execute()
                    sync_map[aid] = ev["id"]
                    stats["created"] += 1
                except Exception:
                    stats["errors"] += 1
            else:
                stats["errors"] += 1

    stale = [aid for aid in sync_map if aid not in seen_ids]
    for aid in stale:
        try:
            service.events().delete(calendarId=cal_id, eventId=sync_map[aid]).execute()
            stats["removed"] += 1
        except Exception:
            pass
        del sync_map[aid]

    _save_sync_map(sync_map)
    return stats


def is_authenticated():
    try:
        if not TOKEN_FILE.exists():
            return False
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        return creds and (creds.valid or (creds.expired and creds.refresh_token))
    except Exception:
        return False

