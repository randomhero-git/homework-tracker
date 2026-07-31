import sys
import json
import threading
import logging
from pathlib import Path

import webview
import httpx
from cal_sync import sync_assignments, is_authenticated
import pystray
from PIL import Image, ImageDraw

if getattr(sys, 'frozen', False):
    BASE = Path(sys._MEIPASS)
    _EXE_DIR = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent
    _EXE_DIR = BASE

# Windowed build has no console, so basicConfig alone discards every record.
# Log to a file beside the executable; keep the stream handler for dev runs.
LOG_FILE = _EXE_DIR / "homework-tracker.log"
_handlers = [logging.StreamHandler()]
try:
    _handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))
except Exception:
    pass
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=_handlers,
)
log = logging.getLogger("homework-tracker")

API_BASE_DEFAULT = "http://10.0.0.237:8000"

CONFIG_FILE = _EXE_DIR / "config.json"
TWEAKS_FILE = _EXE_DIR / "tweaks.json"
STATIC_DIR = BASE / "static"

SHAPES = {
    "tall":    (384, 660),
    "compact": (352, 470),
    "wide":    (700, 424),
}

_window = None
_tray = None
_config = {}


def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"api_base": API_BASE_DEFAULT, "on_top": False}


class JsApi:
    def minimize(self):
        if _window:
            _window.minimize()

    def hide_to_tray(self):
        if _window:
            _window.hide()

    def set_shape(self, shape):
        if _window and shape in SHAPES:
            w, h = SHAPES[shape]
            _window.resize(w, h)

    def set_on_top(self, on_top):
        global _config
        _config["on_top"] = bool(on_top)
        try:
            CONFIG_FILE.write_text(json.dumps(_config, indent=2), encoding="utf-8")
        except Exception as e:
            log.warning("Could not save config: %s", e)

    def save_tweaks(self, json_str):
        try:
            TWEAKS_FILE.write_text(json_str, encoding="utf-8")
        except Exception as e:
            log.warning("Could not save tweaks: %s", e)

    def load_tweaks(self):
        try:
            data = json.loads(TWEAKS_FILE.read_text(encoding="utf-8"))
            return data
        except Exception:
            return None


    def sync_calendar(self):
        """Fetch assignments+courses from API, sync to Google Calendar."""
        try:
            api = _config.get("api_base", API_BASE_DEFAULT)
            import httpx as hx
            with hx.Client(base_url=api, timeout=10) as client:
                ar = client.get("/api/v1/assignments")
                ar.raise_for_status()
                assignments = ar.json()
                cr = client.get("/api/v1/courses")
                cr.raise_for_status()
                courses = cr.json()
            log.info("Calendar sync: fetched %d assignments, %d courses from %s",
                     len(assignments), len(courses), api)
            result = sync_assignments(assignments, courses)
            log.info("Calendar sync: %s", result)
            return {"ok": True, "result": result}
        except FileNotFoundError as e:
            log.error("Calendar sync: %s", e)
            return {"ok": False, "error": "Missing credentials.json - run setup first"}
        except Exception as e:
            log.error("Calendar sync error: %s", e)
            return {"ok": False, "error": str(e)}

    def get_cal_status(self):
        return {"authenticated": is_authenticated()}
    def quit_app(self):
        global _tray
        if _tray:
            _tray.stop()
        if _window:
            _window.destroy()


def make_icon():
    icon_path = BASE / "icon" / "app-icon.png"
    if icon_path.exists():
        return Image.open(icon_path).resize((64, 64), Image.LANCZOS)
    img = Image.new("RGB", (64, 64), "#0067C0")
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill="white")
    d.rectangle([22, 22, 42, 42], fill="#0067C0")
    return img


def build_tray(window):
    global _tray

    def on_show(icon, item):
        window.show()

    def on_quit(icon, item):
        icon.stop()
        window.destroy()

    _tray = pystray.Icon(
        "homework-tracker",
        make_icon(),
        "HomeWork Tracker",
        menu=pystray.Menu(
            pystray.MenuItem("Show", on_show),
            pystray.MenuItem("Quit", on_quit),
        ),
    )
    return _tray


def main():
    global _window, _config
    _config = load_config()
    api_base = _config.get("api_base", API_BASE_DEFAULT)
    log.info("Starting HomeWork Tracker; api_base=%s config=%s", api_base, CONFIG_FILE)

    # Template api_base into the HTML before loading
    src = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    runtime_html = src.replace("HWCFG_API_BASE_PLACEHOLDER", api_base)
    runtime_path = STATIC_DIR / "_runtime.html"
    runtime_path.write_text(runtime_html, encoding="utf-8")

    api = JsApi()
    _window = webview.create_window(
        "HomeWork Tracker",
        url=runtime_path.as_uri(),
        width=384,
        height=660,
        frameless=True,
        easy_drag=False,
        shadow=True,
        background_color='#15264a',
        resizable=False,
        on_top=_config.get("on_top", False),
        js_api=api,
    )

    tray = build_tray(_window)
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    webview.start()


if __name__ == "__main__":
    main()




