import json
import logging
import threading
import datetime as dt
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from edition_manager import (
    initialize_settings,
    process_movie_by_rating_key,
)

app = Flask(__name__)
log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)

(
    SERVER,
    TOKEN,
    SKIP_LIBRARIES,
    MODULES,
    EXCLUDED_LANGUAGES,
    SKIP_MULTIPLE_AUDIO_TRACKS,
    TMDB_API_KEY,
    MAX_WORKERS,
    BATCH_SIZE,
    METADATA_BATCH_SIZE,
) = initialize_settings()

EXECUTOR = ThreadPoolExecutor(max_workers=2)


class BoundedExpiringSet:
    """A set with maximum size and TTL expiration to prevent memory leaks."""

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 3600):
        self._data = OrderedDict()  # key -> expiration timestamp
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def add(self, key) -> bool:
        """Add key to set. Returns True if newly added, False if already present."""
        now = dt.datetime.now(dt.timezone.utc).timestamp()

        with self._lock:
            # Clean expired entries
            self._cleanup_expired(now)

            # Check if already present and not expired
            if key in self._data:
                if self._data[key] > now:
                    return False  # Already present and not expired
                else:
                    del self._data[key]  # Expired, remove it

            # Evict oldest if at capacity
            while len(self._data) >= self._maxsize:
                self._data.popitem(last=False)

            # Add new entry with expiration
            self._data[key] = now + self._ttl
            return True

    def __contains__(self, key) -> bool:
        now = dt.datetime.now(dt.timezone.utc).timestamp()
        with self._lock:
            if key not in self._data:
                return False
            if self._data[key] <= now:
                del self._data[key]
                return False
            return True

    def _cleanup_expired(self, now: float):
        """Remove expired entries (call while holding lock)."""
        expired = [k for k, exp in self._data.items() if exp <= now]
        for k in expired:
            del self._data[k]


# Bounded set with 1000 max entries and 1 hour TTL
_seen = BoundedExpiringSet(maxsize=1000, ttl_seconds=3600)
_seen_lock = threading.Lock()  # Kept for backwards compatibility but set has internal lock

ADD_WINDOW_MINUTES = 10

def _parse_added_at(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)

    if isinstance(value, str):
        s = value.strip()
        if s.isdigit():
            ts = float(s)
            if ts > 1e12:
                ts /= 1000.0
            return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
        try:
            return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
        except Exception:
            return None

    return None

def _submit_one_movie(rating_key: str):
    (
        SERVER, TOKEN, SKIP_LIBRARIES, MODULES, EXCLUDED_LANGUAGES,
        SKIP_MULTIPLE_AUDIO_TRACKS, TMDB_API_KEY, MAX_WORKERS, BATCH_SIZE,
        METADATA_BATCH_SIZE
    ) = initialize_settings()

    process_movie_by_rating_key(
        SERVER, TOKEN, rating_key, MODULES, EXCLUDED_LANGUAGES,
        SKIP_MULTIPLE_AUDIO_TRACKS, TMDB_API_KEY
    )

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

    event = data.get("event")
    md = data.get("Metadata") or {}
    item_type = md.get("type")
    rating_key = md.get("ratingKey")

    if event != "library.new" or item_type != "movie" or not rating_key:
        return jsonify(ignored=True), 202

    added_at = md.get("addedAt")
    try:
        added_dt = _parse_added_at(added_at)
        if added_dt is None:
            print(f"[WARN] Could not parse addedAt '{added_at}'; proceeding anyway")
        else:
            now = dt.datetime.now(dt.timezone.utc)
            if (now - added_dt) > dt.timedelta(minutes=ADD_WINDOW_MINUTES):
                print(f"[INFO] Ignoring stale item (addedAt={added_at})")
                return jsonify(ignored_stale=True, addedAt=str(added_at)), 202
    except Exception as e:
        print(f"[WARN] Error parsing addedAt '{added_at}': {e}")

    # BoundedExpiringSet.add() returns True if newly added, False if duplicate
    if not _seen.add(rating_key):
        return jsonify(duplicate=True), 202

    EXECUTOR.submit(_submit_one_movie, rating_key)

    return jsonify(queued=True, ratingKey=rating_key), 202

if __name__ == "__main__":

    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)