import json
import logging
import threading
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from pathlib import Path
from configparser import ConfigParser
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
) = initialize_settings()

_cfg = ConfigParser()
_cfg.read(Path(__file__).parent / "config" / "config.ini")

WEBHOOK_HOST = _cfg.get("webhook", "host", fallback="0.0.0.0")
WEBHOOK_PORT = _cfg.getint("webhook", "port", fallback=5000)

EXECUTOR = ThreadPoolExecutor(max_workers=2)

_seen = set()
_seen_lock = threading.Lock()

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
        SKIP_MULTIPLE_AUDIO_TRACKS, TMDB_API_KEY, MAX_WORKERS, BATCH_SIZE
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

    with _seen_lock:
        if rating_key in _seen:
            return jsonify(duplicate=True), 202
        _seen.add(rating_key)

    EXECUTOR.submit(_submit_one_movie, rating_key)

    return jsonify(queued=True, ratingKey=rating_key), 202

if __name__ == "__main__":
    from waitress import serve

    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info(
        "Starting Edition Manager webhook on %s:%s", WEBHOOK_HOST, WEBHOOK_PORT
    )

    serve(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT)
