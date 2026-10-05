"""Logging helpers: UTF-8 console output and token masking."""

from __future__ import annotations

import io
import logging
import os
import re
import sys

_MASK_PATTERNS = [
    (re.compile(r"X-Plex-Token=[^&\s]+", re.IGNORECASE), "X-Plex-Token=***"),
    (re.compile(r"token=[^&\s]+", re.IGNORECASE), "token=***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_]+"), "Bearer ***"),
    (re.compile(r"api_key=[^&\s]+", re.IGNORECASE), "api_key=***"),
]


def mask_sensitive(text: str) -> str:
    """Mask tokens and API keys in log messages."""
    if not isinstance(text, str):
        return str(text)
    for pattern, replacement in _MASK_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class SecureFormatter(logging.Formatter):
    def format(self, record):
        return mask_sensitive(super().format(record))


def _ensure_utf8(stream):
    try:
        if (getattr(stream, "encoding", "") or "").lower().replace("_", "-") == "utf-8":
            return stream
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="strict")
            return stream
    except Exception:
        pass
    try:
        return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        return stream


def setup_console() -> None:
    """Make stdout/stderr UTF-8 safe (Windows consoles default to legacy code pages)."""
    sys.stdout = _ensure_utf8(sys.stdout)
    sys.stderr = _ensure_utf8(sys.stderr)
    if os.name == "nt" and sys.stdout.isatty():
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass


def setup_logging(level=logging.INFO) -> None:
    """Configure root logging with timestamped, token-masked output on stdout."""
    root = logging.getLogger()
    if root.handlers:  # already configured
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(SecureFormatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    root.addHandler(handler)
    root.setLevel(level)
