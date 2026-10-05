"""Plex HTTP API client. The single place that talks to the Plex server."""

from __future__ import annotations

import logging
import threading

import requests

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30
HTTP_RETRIES = 3


class PlexClient:
    """Thin client around the Plex HTTP API with per-thread connection pooling."""

    def __init__(self, address: str, token: str):
        self.address = address.rstrip("/")
        self.token = token
        self._local = threading.local()

    # ---- plumbing -------------------------------------------------------

    @property
    def _headers(self) -> dict:
        return {"X-Plex-Token": self.token, "Accept": "application/json"}

    def _session(self) -> requests.Session:
        if not hasattr(self._local, "session"):
            self._local.session = requests.Session()
        return self._local.session

    def get_json(self, path: str, timeout: int = HTTP_TIMEOUT) -> dict:
        url = f"{self.address}{path}"
        last_err = None
        for attempt in range(HTTP_RETRIES):
            try:
                resp = self._session().get(url, headers=self._headers, timeout=timeout)
                resp.raise_for_status()
                return resp.json()
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as err:
                last_err = err
        raise last_err

    def put(self, path: str, params: dict) -> None:
        self._session().put(
            f"{self.address}{path}", headers={"X-Plex-Token": self.token},
            params=params, timeout=HTTP_TIMEOUT,
        )

    # ---- server / libraries ---------------------------------------------

    def server_name(self) -> str:
        # friendlyName only appears on the server root, not /library/sections.
        data = self.get_json("/")
        return data["MediaContainer"].get("friendlyName") or self.address

    def movie_sections(self) -> list[dict]:
        data = self.get_json("/library/sections")
        return [d for d in data["MediaContainer"].get("Directory", []) if d.get("type") == "movie"]

    def section_movies(self, section_key: str) -> list[dict]:
        data = self.get_json(f"/library/sections/{section_key}/all")
        return data.get("MediaContainer", {}).get("Metadata", []) or []

    def search_movies(self, title: str) -> list[dict]:
        """Search every movie library for a title. Returns simplified result dicts."""
        results = []
        for section in self.movie_sections():
            try:
                data = self.get_json(
                    f"/library/sections/{section['key']}/all?title={requests.utils.quote(title)}"
                )
            except Exception:
                continue
            for m in data.get("MediaContainer", {}).get("Metadata", []) or []:
                results.append({
                    "ratingKey": m.get("ratingKey"),
                    "title": m.get("title"),
                    "year": m.get("year"),
                    "thumb": m.get("thumb"),
                    "library": section.get("title"),
                })
        return results

    # ---- metadata ---------------------------------------------------------

    def metadata(self, rating_key) -> dict | None:
        data = self.get_json(f"/library/metadata/{rating_key}")
        items = data.get("MediaContainer", {}).get("Metadata") or []
        return items[0] if items else None

    def metadata_batch(self, rating_keys: list, batch_size: int = 50) -> dict[str, dict]:
        """Fetch detailed metadata for many movies in few API calls.

        Plex accepts comma-separated ratingKeys, turning N calls into N/batch_size.
        Falls back to individual fetches if a batch fails.
        """
        result: dict[str, dict] = {}
        for i in range(0, len(rating_keys), batch_size):
            batch = rating_keys[i:i + batch_size]
            try:
                data = self.get_json(f"/library/metadata/{','.join(str(k) for k in batch)}")
                for item in data.get("MediaContainer", {}).get("Metadata", []) or []:
                    result[str(item.get("ratingKey"))] = item
            except Exception as err:
                logger.warning(f"Batch metadata fetch failed ({len(batch)} keys): {err}")
                for key in batch:
                    try:
                        item = self.metadata(key)
                        if item:
                            result[str(key)] = item
                    except Exception as err2:
                        logger.warning(f"Metadata fetch failed for {key}: {err2}")
        return result

    def extras(self, rating_key) -> list[dict]:
        try:
            data = self.get_json(f"/library/metadata/{rating_key}/extras", timeout=8)
        except Exception:
            return []
        return data.get("MediaContainer", {}).get("Metadata", []) or []

    def image_bytes(self, path: str, timeout: int = 10) -> bytes:
        resp = self._session().get(
            f"{self.address}{path}", headers={"X-Plex-Token": self.token}, timeout=timeout
        )
        resp.raise_for_status()
        return resp.content

    # ---- edition titles ----------------------------------------------------

    def set_edition(self, rating_key, edition_title: str) -> None:
        """Clear then set+lock the edition title (clearing first releases the lock)."""
        self.clear_edition(rating_key)
        if edition_title:
            self.put(f"/library/metadata/{rating_key}", {
                "type": 1, "id": rating_key,
                "editionTitle.value": edition_title, "editionTitle.locked": 1,
            })

    def clear_edition(self, rating_key) -> None:
        self.put(f"/library/metadata/{rating_key}", {
            "type": 1, "id": rating_key,
            "editionTitle.value": "", "editionTitle.locked": 0,
        })

    def restore_edition(self, rating_key, edition_title: str) -> None:
        """Set an edition title exactly as stored in a backup (locked only if non-empty)."""
        self.put(f"/library/metadata/{rating_key}", {
            "type": 1, "id": rating_key,
            "editionTitle.value": edition_title,
            "editionTitle.locked": 1 if edition_title else 0,
        })
