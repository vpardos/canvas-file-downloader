import json
import os
import sys
from pathlib import Path

APP_NAME = "canvasdl"
KEYRING_SERVICE = "canvasdl"
KEYRING_USERNAME = "api_token"


def config_dir() -> Path:
    # Per-user config folder, following each OS's convention
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / APP_NAME


def _keyring():
    """Return the keyring module if a real password store is usable, else None."""
    try:
        import keyring
        from keyring.backends import fail
    except ImportError:
        return None
    try:
        backend = keyring.get_keyring()
    except Exception:
        return None
    if isinstance(backend, fail.Keyring):  # "no password store available"
        return None
    return keyring


def _write_file_token(token: str) -> Path:
    path = config_dir() / "credentials.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    # create the file readable/writable only by you (0600)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"api_token": token}, f)
    os.chmod(path, 0o600)
    return path


def save_token(token: str) -> str:  # called by cli
    # Save the token; return where it was stored.
    kr = _keyring()
    if kr is not None:
        try:
            kr.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
            return "the system password store"
        except Exception as e:
            pass  # store exists but failed (locked, etc.) -> use the file
    return str(_write_file_token(token))
