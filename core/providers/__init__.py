"""Detector providers.

Each provider is a function `(ctx: MovieContext) -> str | None` registered under
the module name used in config.ini's `[modules] order`. Returning None means the
detector found nothing and contributes nothing to the edition title.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import Config
    from ..plex import PlexClient


@dataclass
class MovieContext:
    movie: dict          # detailed Plex metadata for the movie
    file_name: str       # basename of the largest media part
    config: "Config"
    plex: "PlexClient"


PROVIDERS: dict[str, Callable[[MovieContext], str | None]] = {}

# Module name -> template variable name (for custom format strings).
TEMPLATE_VARS: dict[str, str] = {}


def provider(name: str, template_var: str):
    def decorator(fn):
        PROVIDERS[name] = fn
        TEMPLATE_VARS[name] = template_var
        return fn
    return decorator


# Importing the submodules populates the registry.
from . import audio, video, filename, metadata, rating, extras  # noqa: E402,F401
