"""Movie processing: apply or reset edition titles across the library."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import Config
from .editions import format_title, run_providers
from .plex import PlexClient
from .progress import Progress
from .providers import MovieContext

logger = logging.getLogger(__name__)


def _collect_movies(plex: PlexClient, skip_libraries: set[str]) -> list[dict]:
    movies = []
    for section in plex.movie_sections():
        title = section.get("title")
        if title in skip_libraries:
            continue
        section_movies = plex.section_movies(section["key"])
        logger.info(f"Library: {title}, Movies: {len(section_movies)}")
        movies.extend(section_movies)
    return movies


def _main_file_name(movie: dict) -> str | None:
    """Basename of the largest media part — the file detectors should look at."""
    parts = [part for media in movie.get("Media", []) for part in media.get("Part", [])]
    if not parts:
        return None
    largest = max(parts, key=lambda p: p.get("size", 0))
    return os.path.basename(largest.get("file", "")) or None


def process_single(cfg: Config, plex: PlexClient, movie: dict,
                   prefetched: dict[str, dict] | None = None) -> None:
    """Build and write the edition title for one movie."""
    rating_key = str(movie["ratingKey"])

    detailed = (prefetched or {}).get(rating_key)
    if detailed is None:
        try:
            detailed = plex.metadata(rating_key)
        except Exception as err:
            logger.warning(f"Could not fetch metadata for {movie.get('title', 'Unknown')}: {err}")
    movie_data = detailed or movie

    file_name = _main_file_name(movie_data)
    if not file_name:
        return

    ctx = MovieContext(movie=movie_data, file_name=file_name, config=cfg, plex=plex)
    results = run_providers(ctx)
    title = movie_data.get("title", "Unknown")

    edition = format_title(results, cfg) if results else ""
    plex.set_edition(rating_key, edition)
    logger.info(f"{title}: {edition}" if edition else f"{title}: Cleared edition information")


def process_all(cfg: Config, plex: PlexClient) -> None:
    movies = _collect_movies(plex, cfg.skip_libraries)
    logger.info(f"Total movies found: {len(movies)}")

    progress = Progress()
    progress.set_total(len(movies))
    total_batches = (len(movies) + cfg.batch_size - 1) // cfg.batch_size

    with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
        for i in range(0, len(movies), cfg.batch_size):
            batch = movies[i:i + cfg.batch_size]
            batch_num = i // cfg.batch_size + 1

            keys = [str(m["ratingKey"]) for m in batch]
            logger.info(f"Batch {batch_num}/{total_batches}: prefetching metadata for {len(keys)} movies...")
            prefetched = plex.metadata_batch(keys, cfg.metadata_batch_size)

            futures = [
                executor.submit(_process_safely, cfg, plex, movie, prefetched)
                for movie in batch
            ]
            for _ in as_completed(futures):
                progress.step()
            logger.info(f"Batch {batch_num}/{total_batches}: complete")


def _process_safely(cfg, plex, movie, prefetched):
    try:
        process_single(cfg, plex, movie, prefetched)
    except Exception as err:
        logger.error(f"Error processing {movie.get('title', 'Unknown')}: {err}")


def process_one(cfg: Config, plex: PlexClient, rating_key) -> bool:
    movie = plex.metadata(rating_key)
    if not movie:
        logger.error(f"Movie with ratingKey {rating_key} not found.")
        return False

    logger.info(f"Processing ratingKey={rating_key} ...")
    progress = Progress()
    progress.set_total(1)
    process_single(cfg, plex, movie)
    progress.step()
    return True


def reset_all(cfg: Config, plex: PlexClient) -> None:
    movies = [m for m in _collect_movies(plex, cfg.skip_libraries) if "editionTitle" in m]
    logger.info(f"Total movies to reset: {len(movies)}")

    progress = Progress()
    progress.set_total(len(movies))

    def _reset_one(movie):
        try:
            plex.clear_edition(movie["ratingKey"])
            logger.info(f"Reset: {movie.get('title', 'Unknown')}")
        except Exception as err:
            logger.error(f"Error resetting {movie.get('title', 'Unknown')}: {err}")

    with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
        futures = [executor.submit(_reset_one, m) for m in movies]
        for _ in as_completed(futures):
            progress.step()
