import json
import os
from pathlib import Path

from .config import credentials_file, read_json

KEYRING_SERVICE = "canvasdl"
KEYRING_USERNAME = "api_token"


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
    path = credentials_file()
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


def delete_token() -> list:  # called by cli
    # Remove the token from the password store and the file; return where it was removed from.
    removed = []
    kr = _keyring()
    if kr is not None:
        try:
            kr.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            removed.append("the system password store")
        except Exception:
            pass  # nothing saved there
    path = credentials_file()
    if path.exists():
        path.unlink()
        removed.append(str(path))
    return removed

def load_token():  # called by canvas.py
    # Return the saved token, or None if there isn't one.
    kr = _keyring()
    if kr is not None:
        try:
            token = kr.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if token:
                return token
        except Exception:
            pass
    return read_json(credentials_file()).get("api_token")
