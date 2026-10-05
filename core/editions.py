"""Builds an edition title for one movie: run providers, then format the results."""

from __future__ import annotations

import logging

from .config import Config
from .providers import PROVIDERS, TEMPLATE_VARS, MovieContext

logger = logging.getLogger(__name__)


def run_providers(ctx: MovieContext) -> dict[str, str]:
    """Run the configured detector modules; return {module_name: value} for hits."""
    results = {}
    for name in ctx.config.modules:
        fn = PROVIDERS.get(name)
        if fn is None:
            logger.warning(f"Unknown module: {name}")
            continue
        try:
            value = fn(ctx)
            if value:
                results[name] = value
        except Exception as err:
            title = ctx.movie.get("title", "Unknown")
            logger.error(f"Error in module {name} for {title}: {err}")
    return results


def format_title(results: dict[str, str], cfg: Config) -> str:
    """Join provider results into an edition title (auto mode or custom template)."""
    if cfg.template_format.lower() == "auto":
        # Join non-empty results in module order, deduplicated.
        tags = [results[m] for m in cfg.modules if results.get(m)]
        title = cfg.separator.join(dict.fromkeys(tags))
    else:
        title = cfg.template_format
        for module, var in TEMPLATE_VARS.items():
            title = title.replace("{" + var + "}", results.get(module, "") or "")
        # Collapse doubled separators left behind by empty values.
        while "  " in title:
            title = title.replace("  ", " ")
        for sep in (" · ", " - ", " | ", " / ", ", "):
            while sep + sep in title:
                title = title.replace(sep + sep, sep)
            title = title.strip(sep.strip())
        title = title.strip()

    if cfg.max_length > 0 and len(title) > cfg.max_length:
        title = title[:cfg.max_length - 3].rsplit(cfg.separator.strip(), 1)[0] + "..."
    return title
