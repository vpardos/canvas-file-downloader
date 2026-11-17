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

def read_json(path) -> dict:  # also used by credentials
    # read a settings file; a damaged file gives a clear message instead of a traceback
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise SystemExit(f"{path} is damaged ({e}).\nFix it or delete it, then run the setup command again.")
    if not isinstance(data, dict):
        raise SystemExit(f"{path} has an unexpected format.\nFix it or delete it, then run the setup command again.")
    return data


def load_domain():
    return read_json(config_file()).get("domain")


def save_domain(domain: str):
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)

    # keep the other settings already in config.json, only change "domain"
    settings = read_json(path)
    settings["domain"] = domain.rstrip("/")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
