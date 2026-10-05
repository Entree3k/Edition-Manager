"""Rating detector: TMDb score, Rotten Tomatoes percentage, or Letterboxd stars."""

from __future__ import annotations

import logging
import re
import threading
import time
from urllib.parse import quote

import requests

from . import MovieContext, provider

logger = logging.getLogger(__name__)

_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@provider("Rating", "rating")
def rating(ctx: MovieContext) -> str | None:
    source = ctx.config.rating_source
    if source == "rotten_tomatoes":
        return _rotten_tomatoes(ctx.movie, ctx.config.rotten_tomatoes_type)
    if source == "letterboxd":
        return _letterboxd(ctx.movie)
    # "imdb" (historical name) — actually TMDb vote_average on a 0-10 scale.
    return _tmdb(ctx.movie, ctx.config.tmdb_api_key)


# ---- TMDb ------------------------------------------------------------------

def _tmdb(movie: dict, api_key: str) -> str | None:
    if not api_key:
        logger.error("TMDb API key is missing.")
        return None
    title, year = movie.get("title"), movie.get("year")
    if not title or not year:
        return None
    try:
        resp = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": api_key, "query": title, "year": year},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            score = results[0].get("vote_average")
            if score is not None:
                return f"{float(score):.1f}"
    except Exception as err:
        logger.error(f"Error fetching TMDb rating for {title} ({year}): {err}")
    return None


# ---- Rotten Tomatoes (from Plex's own rating fields) -------------------------

def _format_percent(value) -> str | None:
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    # Plex may report 0-10 (8.4) or 0-100 style values.
    pct = int(round(num * 10)) if num <= 10 else int(round(num))
    return f"{pct}%"


def _rotten_tomatoes(movie: dict, rt_type: str) -> str | None:
    critic = _format_percent(movie.get("rating"))
    audience = _format_percent(movie.get("audienceRating"))
    if rt_type == "audience":
        return audience or critic
    return critic or audience


# ---- Letterboxd (scraped, cached) ---------------------------------------------

# key -> (value, expires_at). Hits cached 24h, misses 1h so transient network
# errors don't permanently skip a movie for the session.
_lb_cache: dict[str, tuple] = {}
_lb_lock = threading.Lock()
_LB_CACHE_MAX = 500
_LB_HIT_TTL = 86_400
_LB_MISS_TTL = 3_600


def _lb_cache_get(key: str):
    """Return (hit, value); hit is True even for a cached miss (value None)."""
    with _lb_lock:
        entry = _lb_cache.get(key)
        if entry is None:
            return False, None
        value, expires_at = entry
        if time.monotonic() >= expires_at:
            del _lb_cache[key]
            return False, None
        return True, value


def _lb_cache_set(key: str, value) -> None:
    ttl = _LB_HIT_TTL if value is not None else _LB_MISS_TTL
    with _lb_lock:
        if len(_lb_cache) >= _LB_CACHE_MAX:
            now = time.monotonic()
            for k in [k for k, (_, exp) in _lb_cache.items() if exp <= now]:
                del _lb_cache[k]
            if len(_lb_cache) >= _LB_CACHE_MAX:  # still full: drop oldest 100
                for k in list(_lb_cache)[:100]:
                    del _lb_cache[k]
        _lb_cache[key] = (value, time.monotonic() + ttl)


def _title_to_slug(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


_LB_RATING_PATTERNS = [
    re.compile(r'"ratingValue"\s*:\s*([\d.]+)', re.IGNORECASE),  # JSON-LD, most reliable
    re.compile(r'<meta\s+name="twitter:data2"\s+content="([\d.]+)\s+out\s+of\s+5"', re.IGNORECASE),
    re.compile(r'class="average-rating"[^>]*>\s*<a[^>]*>([\d.]+)</a>', re.IGNORECASE),
]


def _lb_rating_from_url(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=_BROWSER_HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        for pattern in _LB_RATING_PATTERNS:
            match = pattern.search(resp.text)
            if match:
                value = float(match.group(1))
                if 0 < value <= 5:
                    return f"{value:.1f}/5"
    except Exception:
        pass
    return None


def _lb_search_slug(title: str, year) -> str | None:
    """Fallback search when the locally-built slug doesn't match a film page."""
    query = f"{title} {year}" if year else title
    try:
        resp = requests.get(
            f"https://letterboxd.com/search/films/{quote(query, safe='')}/",
            headers=_BROWSER_HEADERS, timeout=10,
        )
        if resp.status_code == 200:
            match = re.search(r'data-film-slug="([^"]+)"', resp.text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def _letterboxd(movie: dict) -> str | None:
    title, year = movie.get("title"), movie.get("year")
    if not title:
        return None

    cache_key = f"{title}:{year}"
    hit, cached = _lb_cache_get(cache_key)
    if hit:
        return cached

    try:
        slug = _title_to_slug(title)
        urls = [f"https://letterboxd.com/film/{slug}/"]
        if year:  # year-suffixed slug handles remakes/disambiguation
            urls.append(f"https://letterboxd.com/film/{slug}-{year}/")

        for url in urls:
            result = _lb_rating_from_url(url)
            if result:
                _lb_cache_set(cache_key, result)
                return result

        search_slug = _lb_search_slug(title, year)
        if search_slug:
            result = _lb_rating_from_url(f"https://letterboxd.com/film/{search_slug}/")
            if result:
                _lb_cache_set(cache_key, result)
                return result
    except Exception as err:
        logger.error(f"Error fetching Letterboxd rating for {title}: {err}")

    _lb_cache_set(cache_key, None)
    return None
