"""Application configuration: a single dataclass loaded from / saved to config.ini.

The file format is unchanged from v1, so an existing config.ini keeps working.
"""

from __future__ import annotations

import re
from configparser import ConfigParser
from dataclasses import dataclass, field
from pathlib import Path

from .paths import CONFIG_FILE

# All available detector modules, in default display order.
ALL_MODULES = [
    "AudioChannels", "AudioCodec", "Bitrate", "ContentRating", "Country", "Cut",
    "Director", "Duration", "DurationMinutes", "DynamicRange", "FrameRate", "Genre",
    "Language", "Rating", "Release", "Resolution", "ShortFilm", "Size",
    "Source", "SpecialFeatures", "Studio", "VideoCodec", "Writer",
]

DEFAULT_SEPARATOR = " • "


@dataclass
class Config:
    # [server]
    address: str = ""
    token: str = ""
    skip_libraries: set[str] = field(default_factory=set)
    # [modules]
    modules: list[str] = field(default_factory=lambda: ["Cut", "Release"])
    # [language]
    excluded_languages: set[str] = field(default_factory=set)
    skip_multiple_audio_tracks: bool = False
    # [rating]
    rating_source: str = "imdb"
    rotten_tomatoes_type: str = "critic"
    tmdb_api_key: str = ""
    # [performance]
    max_workers: int = 8
    batch_size: int = 25
    metadata_batch_size: int = 50
    # [template]
    template_format: str = "auto"
    separator: str = DEFAULT_SEPARATOR
    max_length: int = 0
    # [webhook]
    webhook_enabled: bool = False
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 5000
    # [appearance]
    primary_color: str = "#6750A4"
    dark_mode: bool = True
    # [scheduler]
    scheduler_enabled: bool = False
    scheduler_cron: str = "0 3 * * *"
    scheduler_last_run: str = ""


def _split_list(raw: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;,；]", raw) if item.strip()]


def load(path: Path = CONFIG_FILE) -> Config:
    parser = ConfigParser()
    parser.read(path, encoding="utf-8")
    cfg = Config()

    cfg.address = parser.get("server", "address", fallback="").strip().rstrip("/")
    cfg.token = parser.get("server", "token", fallback="").strip()
    cfg.skip_libraries = set(_split_list(parser.get("server", "skip_libraries", fallback="")))

    order = _split_list(parser.get("modules", "order", fallback=""))
    if order:
        cfg.modules = order

    cfg.excluded_languages = set(_split_list(parser.get("language", "excluded_languages", fallback="")))
    cfg.skip_multiple_audio_tracks = parser.getboolean("language", "skip_multiple_audio_tracks", fallback=False)

    cfg.rating_source = parser.get("rating", "source", fallback="imdb").strip().lower()
    cfg.rotten_tomatoes_type = parser.get("rating", "rotten_tomatoes_type", fallback="critic").strip().lower()
    cfg.tmdb_api_key = parser.get("rating", "tmdb_api_key", fallback="").strip()

    cfg.max_workers = parser.getint("performance", "max_workers", fallback=8)
    cfg.batch_size = parser.getint("performance", "batch_size", fallback=25)
    cfg.metadata_batch_size = parser.getint("performance", "metadata_batch_size", fallback=50)

    cfg.template_format = parser.get("template", "format", fallback="auto").strip() or "auto"
    separator = parser.get("template", "separator", fallback=DEFAULT_SEPARATOR)
    # ConfigParser strips surrounding whitespace; restore spacing around a bare symbol.
    if not separator.strip():
        separator = DEFAULT_SEPARATOR
    elif separator == separator.strip():
        separator = f" {separator} "
    cfg.separator = separator
    cfg.max_length = parser.getint("template", "max_length", fallback=0)

    cfg.webhook_enabled = parser.getboolean("webhook", "enabled", fallback=False)
    cfg.webhook_host = parser.get("webhook", "host", fallback="0.0.0.0").strip()
    cfg.webhook_port = parser.getint("webhook", "port", fallback=5000)

    cfg.primary_color = parser.get("appearance", "primary_color", fallback="#6750A4").strip()
    cfg.dark_mode = parser.getboolean("appearance", "dark_mode", fallback=True)

    cfg.scheduler_enabled = parser.getboolean("scheduler", "enabled", fallback=False)
    cfg.scheduler_cron = parser.get("scheduler", "cron", fallback="0 3 * * *").strip()
    cfg.scheduler_last_run = parser.get("scheduler", "last_run", fallback="")

    return cfg


def save(cfg: Config, path: Path = CONFIG_FILE) -> None:
    parser = ConfigParser()
    parser["server"] = {
        "address": cfg.address,
        "token": cfg.token,
        "skip_libraries": ";".join(sorted(cfg.skip_libraries)),
    }
    parser["modules"] = {"order": ";".join(cfg.modules)}
    parser["language"] = {
        "excluded_languages": ", ".join(sorted(cfg.excluded_languages)),
        "skip_multiple_audio_tracks": "yes" if cfg.skip_multiple_audio_tracks else "no",
    }
    parser["rating"] = {
        "source": cfg.rating_source,
        "rotten_tomatoes_type": cfg.rotten_tomatoes_type,
        "tmdb_api_key": cfg.tmdb_api_key,
    }
    parser["performance"] = {
        "max_workers": str(cfg.max_workers),
        "batch_size": str(cfg.batch_size),
        "metadata_batch_size": str(cfg.metadata_batch_size),
    }
    parser["template"] = {
        "format": cfg.template_format,
        "separator": cfg.separator.strip() or DEFAULT_SEPARATOR.strip(),
        "max_length": str(cfg.max_length),
    }
    parser["webhook"] = {
        "enabled": "yes" if cfg.webhook_enabled else "no",
        "host": cfg.webhook_host,
        "port": str(cfg.webhook_port),
    }
    parser["appearance"] = {
        "primary_color": cfg.primary_color,
        "dark_mode": "yes" if cfg.dark_mode else "no",
    }
    parser["scheduler"] = {
        "enabled": "yes" if cfg.scheduler_enabled else "no",
        "cron": cfg.scheduler_cron,
        "last_run": cfg.scheduler_last_run,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        parser.write(f)
