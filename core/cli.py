"""Command-line interface. The GUI drives these same commands as a subprocess."""

from __future__ import annotations

import argparse
import logging
import sys

from . import backups, config, processor
from .logutil import setup_console, setup_logging
from .paths import BACKUP_DIR
from .plex import PlexClient

logger = logging.getLogger(__name__)


def connect(cfg: config.Config) -> PlexClient:
    """Create a client and verify the server is reachable."""
    plex = PlexClient(cfg.address, cfg.token)
    try:
        logger.info(f"Successfully connected to server: {plex.server_name()}")
    except Exception as err:
        logger.error("Server connection failed. Check config.ini server settings or your network.")
        raise SystemExit(err)
    return plex


def _interactive_one(cfg, plex) -> None:
    title = input("Enter movie title to search: ").strip()
    if not title:
        logger.info("No title entered.")
        return
    matches = plex.search_movies(title)
    if not matches:
        logger.info(f"No movies found for '{title}'.")
        return

    print(f"\nFound {len(matches)} match(es):")
    for i, m in enumerate(matches, start=1):
        print(f"{i}. {m.get('title', '?')} ({m.get('year', '?')}) — {m.get('library', '')}")
    selection = input("\nSelect a number (or Enter for 1): ").strip() or "1"
    try:
        idx = int(selection) - 1
        chosen = matches[idx]
        if idx < 0:
            raise IndexError
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    confirm = input(
        f"Process '{chosen['title']}' ({chosen.get('year', '?')}) "
        f"from {chosen.get('library', '')}? [y/N]: "
    ).strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    ok = processor.process_one(cfg, plex, chosen["ratingKey"])
    logger.info("Done." if ok else "Failed.")


def main(argv=None) -> None:
    setup_console()
    setup_logging()

    parser = argparse.ArgumentParser(description="Manage Plex movie edition titles")
    parser.add_argument("--all", action="store_true", help="Add edition info to all movies")
    parser.add_argument("--one", action="store_true", help="Interactively search and process a single movie")
    parser.add_argument("--one-id", dest="one_id", metavar="RATINGKEY",
                        help="Process a single movie by ratingKey (non-interactive; used by GUI)")
    parser.add_argument("--reset", action="store_true", help="Reset edition info for all movies")
    parser.add_argument("--backup", action="store_true", help="Backup edition metadata")
    parser.add_argument("--restore", action="store_true", help="Restore from the latest backup")
    parser.add_argument("--restore-file", dest="restore_file", metavar="PATH",
                        help="Restore from a specific backup file")
    parser.add_argument("--list-backups", action="store_true", help="List available backup files")
    parser.add_argument("--undo", action="store_true", help="Undo the last bulk operation")
    args = parser.parse_args(argv)

    if args.list_backups:
        files = backups.list_backups()
        if not files:
            print("No backups found in", BACKUP_DIR)
        else:
            print("Available backups:")
            for path in files:
                print(" -", path)
        return

    cfg = config.load()
    plex = connect(cfg)

    if args.one_id:
        ok = processor.process_one(cfg, plex, args.one_id)
        logger.info("Done." if ok else "Failed.")
    elif args.one:
        _interactive_one(cfg, plex)
    elif args.backup:
        backups.backup_metadata(plex)
        logger.info("Metadata backup completed.")
    elif args.restore_file:
        backups.restore_metadata(plex, args.restore_file)
        logger.info("Metadata restoration completed.")
    elif args.restore:
        backups.restore_metadata(plex)
        logger.info("Metadata restoration completed.")
    elif args.undo:
        if backups.restore_undo_snapshot(plex):
            logger.info("Undo completed successfully.")
        else:
            logger.error("Undo failed - no snapshot available or restore error.")
            sys.exit(1)
    elif args.all:
        logger.info("Creating undo snapshot before processing...")
        backups.create_undo_snapshot(plex)
        processor.process_all(cfg, plex)
    elif args.reset:
        logger.info("Creating undo snapshot before reset...")
        backups.create_undo_snapshot(plex)
        processor.reset_all(cfg, plex)
    else:
        parser.print_help()
        return

    logger.info("Script execution completed.")


if __name__ == "__main__":
    main()
