"""Webhook server: processes movies as Plex announces they were added.

Point a Plex webhook at http://<host>:<port>/edition-manager.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request

from . import config, processor
from .cli import connect
from .logutil import setup_console, setup_logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

EXECUTOR = ThreadPoolExecutor(max_workers=2)
ADD_WINDOW_MINUTES = 10  # ignore "library.new" events older than this


class BoundedExpiringSet:
    """Set with max size and TTL, for deduplicating webhook deliveries."""

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 3600):
        self._data: OrderedDict = OrderedDict()  # key -> expiration timestamp
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def add(self, key) -> bool:
        """Returns True if newly added, False if already present."""
        now = dt.datetime.now(dt.timezone.utc).timestamp()
        with self._lock:
            for k in [k for k, exp in self._data.items() if exp <= now]:
                del self._data[k]
            if key in self._data:
                return False
            while len(self._data) >= self._maxsize:
                self._data.popitem(last=False)
            self._data[key] = now + self._ttl
            return True


_seen = BoundedExpiringSet()


def _parse_added_at(value) -> dt.datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit()):
        ts = float(value)
        if ts > 1e12:  # milliseconds
            ts /= 1000.0
        return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
    if isinstance(value, str):
        try:
            return dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00")).astimezone(dt.timezone.utc)
        except Exception:
            return None
    return None


def _process_movie(rating_key: str) -> None:
    # Reload config each time so settings changes apply without a restart.
    cfg = config.load()
    plex = connect(cfg)
    processor.process_one(cfg, plex, rating_key)


@app.route("/healthz", methods=["GET"])
def health():
    return jsonify(ok=True), 200


@app.route("/edition-manager", methods=["POST"])
def edition_manager():
    payload_text = request.form.get("payload")
    if not payload_text:
        return jsonify(error="missing payload"), 400
    try:
        data = json.loads(payload_text)
    except Exception:
        return jsonify(error="invalid json"), 400

    metadata = data.get("Metadata") or {}
    rating_key = metadata.get("ratingKey")
    if data.get("event") != "library.new" or metadata.get("type") != "movie" or not rating_key:
        return jsonify(ignored=True), 202

    added_at = metadata.get("addedAt")
    added_dt = _parse_added_at(added_at)
    if added_dt is None:
        logger.warning(f"Could not parse addedAt '{added_at}'; proceeding anyway")
    elif dt.datetime.now(dt.timezone.utc) - added_dt > dt.timedelta(minutes=ADD_WINDOW_MINUTES):
        logger.info(f"Ignoring stale item (addedAt={added_at})")
        return jsonify(ignored_stale=True, addedAt=str(added_at)), 202

    if not _seen.add(rating_key):
        return jsonify(duplicate=True), 202

    EXECUTOR.submit(_process_movie, rating_key)
    return jsonify(queued=True, ratingKey=rating_key), 202


def main() -> None:
    setup_console()
    setup_logging()
    cfg = config.load()
    connect(cfg)  # fail fast if the server is unreachable

    from waitress import serve

    logger.info(f"Webhook server listening on {cfg.webhook_host}:{cfg.webhook_port}")
    serve(app, host=cfg.webhook_host, port=cfg.webhook_port)


if __name__ == "__main__":
    main()
