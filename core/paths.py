"""Filesystem locations used throughout the app."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "config.ini"
PRESETS_FILE = ROOT / "config" / "module_presets.json"
BACKUP_DIR = ROOT / "metadata_backup"
UNDO_SNAPSHOT_FILE = BACKUP_DIR / ".undo_snapshot.json"
ASSETS_DIR = ROOT / "assets"
