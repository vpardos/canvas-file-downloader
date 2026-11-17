import json
import os
import sys
from pathlib import Path

APP_NAME = "canvasdl"


def config_dir() -> Path:
    # Per-user config folder, following each OS's convention
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / APP_NAME


def config_file() -> Path:
    return config_dir() / "config.json"

def credentials_file() -> Path:
    return config_dir() / "credentials.json"

def load_domain():
    path = config_dir() / "config.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("domain")
    return None


def save_domain(domain: str):
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)

    # keep the other settings already in config.json, only change "domain"
    settings = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            settings = json.load(f)

    settings["domain"] = domain.rstrip("/")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
