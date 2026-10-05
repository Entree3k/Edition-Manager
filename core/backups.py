"""Backups and the undo snapshot.

Manual backups are timestamped JSON files (the newest few are kept).
The undo snapshot is a single hidden file overwritten before each bulk
operation so the last Process All / Reset All can be reverted.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, UTC
from pathlib import Path

from .paths import BACKUP_DIR, UNDO_SNAPSHOT_FILE
from .plex import PlexClient
from .progress import Progress

logger = logging.getLogger(__name__)

KEEP_BACKUPS = 4
RESTORE_WORKERS = 8


def list_backups() -> list[Path]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(BACKUP_DIR.glob("metadata_backup_*.json"))


def latest_backup() -> Path | None:
    files = list_backups()
    return files[-1] if files else None


def _snapshot_editions(plex: PlexClient) -> dict[str, dict]:
    """Capture {ratingKey: {title, editionTitle}} for every movie on the server."""
    data = {}
    for section in plex.movie_sections():
        try:
            for movie in plex.section_movies(section["key"]):
                data[movie["ratingKey"]] = {
                    "title": movie.get("title", ""),
                    "editionTitle": movie.get("editionTitle", ""),
                }
        except Exception as err:
            logger.warning(f"Error fetching library {section.get('title', '?')}: {err}")
    return data


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    tmp.replace(path)


def backup_metadata(plex: PlexClient, backup_file: Path | None = None) -> Path:
    payload = {
        "version": "1.0",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "data": _snapshot_editions(plex),
    }
    if backup_file is None:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = BACKUP_DIR / f"metadata_backup_{ts}.json"

    _write_json_atomic(backup_file, payload)
    logger.info(f"Backup complete. {len(payload['data'])} movies saved to {backup_file}")
    prune_old_backups()
    return backup_file


def prune_old_backups(keep: int = KEEP_BACKUPS) -> None:
    files = list_backups()
    for path in files[:-keep] if len(files) > keep else []:
        try:
            path.unlink()
        except Exception as err:
            logger.warning(f"Could not delete old backup '{path}': {err}")


def _restore_editions(plex: PlexClient, data: dict) -> None:
    items = list(data.items())
    progress = Progress()
    progress.set_total(len(items))

    def _restore_one(pair):
        rating_key, meta = pair
        try:
            plex.restore_edition(rating_key, meta.get("editionTitle", ""))
        except Exception as err:
            logger.error(f"Failed restore id={rating_key}: {err}")
        finally:
            progress.step()

    with ThreadPoolExecutor(max_workers=RESTORE_WORKERS) as executor:
        futures = [executor.submit(_restore_one, pair) for pair in items]
        for _ in as_completed(futures):
            pass


def restore_metadata(plex: PlexClient, backup_file: Path | str | None = None) -> bool:
    if backup_file is None:
        backup_file = latest_backup()
        if not backup_file:
            logger.error("No backup files found.")
            return False
        logger.info(f"Using latest backup: {backup_file}")

    backup_file = Path(backup_file)
    if not backup_file.exists():
        logger.error(f"Backup file not found: {backup_file}")
        return False

    with backup_file.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    data = payload.get("data", payload)  # tolerate pre-1.0 format

    logger.info(f"Starting restore from {backup_file} for {len(data)} movies")
    _restore_editions(plex, data)
    logger.info("Restore complete.")
    return True


# ---- Undo snapshot -----------------------------------------------------------

def create_undo_snapshot(plex: PlexClient) -> Path | None:
    try:
        data = _snapshot_editions(plex)
    except Exception as err:
        logger.warning(f"Could not create undo snapshot: {err}")
        return None

    payload = {
        "version": "1.0",
        "type": "undo_snapshot",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "data": data,
    }
    try:
        _write_json_atomic(UNDO_SNAPSHOT_FILE, payload)
    except Exception as err:
        logger.warning(f"Could not write undo snapshot: {err}")
        return None
    logger.info(f"Undo snapshot created with {len(data)} movies.")
    return UNDO_SNAPSHOT_FILE


def restore_undo_snapshot(plex: PlexClient) -> bool:
    if not UNDO_SNAPSHOT_FILE.exists():
        logger.error("No undo snapshot available.")
        return False

    try:
        with UNDO_SNAPSHOT_FILE.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as err:
        logger.error(f"Could not read undo snapshot: {err}")
        return False

    data = payload.get("data", {})
    if not data:
        logger.error("Undo snapshot is empty.")
        return False

    logger.info(f"Restoring from undo snapshot ({len(data)} movies)...")
    _restore_editions(plex, data)
    logger.info("Undo restore complete.")
    return True
