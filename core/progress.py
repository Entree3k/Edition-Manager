"""Progress reporting over stdout.

The GUI runs the CLI as a subprocess and reads `PROGRESS <pct>` lines to drive
its progress bar; everything else on stdout is shown in the activity log.
"""

from __future__ import annotations

import sys
import threading


class Progress:
    def __init__(self):
        self._lock = threading.Lock()
        self._total = 1
        self._done = 0

    def set_total(self, total: int) -> None:
        with self._lock:
            self._total = max(1, int(total))
            self._done = 0
        self._emit(0)

    def step(self, n: int = 1) -> None:
        with self._lock:
            self._done += n
            pct = int(self._done * 100 / self._total)
        self._emit(pct)

    @staticmethod
    def _emit(pct: int) -> None:
        print(f"PROGRESS {min(100, max(0, pct))}")
        sys.stdout.flush()
