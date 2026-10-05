"""Runs the CLI as a child process and relays its output to the GUI."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore

CLI_SCRIPT = Path(__file__).resolve().parent.parent.parent / "edition_manager.py"

_WIN_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW


class ProcessWorker(QtCore.QObject):
    """Wraps one `python edition_manager.py <flag>` run.

    Emits `line` for log output, `progress` for PROGRESS markers, and
    `finished(exit_code)` when done.
    """

    started = QtCore.Signal()
    line = QtCore.Signal(str)
    progress = QtCore.Signal(int)
    finished = QtCore.Signal(int)

    def __init__(self, flag: str, parent=None):
        super().__init__(parent)
        self.flag = flag
        self._buffer = ""
        self._finished = False
        self._cancelled = False
        self.proc = QtCore.QProcess(self)
        self.proc.setWorkingDirectory(str(CLI_SCRIPT.parent))
        env = QtCore.QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        self.proc.setProcessEnvironment(env)
        self.proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        if sys.platform.startswith("win"):
            try:
                self.proc.setCreateProcessArgumentsModifier(
                    lambda args: args.update(creationFlags=_WIN_NO_WINDOW)
                )
            except Exception:
                pass
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.finished.connect(lambda code, _status: self._finish(code))
        self.proc.errorOccurred.connect(self._process_error)

    def start(self) -> None:
        if self._cancelled:
            self._finish(1)
            return
        self.started.emit()
        if not CLI_SCRIPT.exists():
            self.line.emit(f"Error: '{CLI_SCRIPT.name}' not found next to the GUI.")
            self._finish(1)
            return
        python = sys.executable or "python3"
        self.proc.start(python, ["-u", str(CLI_SCRIPT), self.flag])

    def is_running(self) -> bool:
        return self.proc.state() == QtCore.QProcess.Running

    def kill(self) -> None:
        self._cancelled = True
        if self.proc.state() != QtCore.QProcess.NotRunning:
            self.proc.kill()

    def _process_error(self, error) -> None:
        if error == QtCore.QProcess.FailedToStart:
            self.line.emit(f"Error: could not start operation: {self.proc.errorString()}")
            self._finish(1)

    def _finish(self, code: int) -> None:
        if self._finished:
            return
        self._finished = True
        self._read()
        if self._buffer:
            self._emit_line(self._buffer)
            self._buffer = ""
        self.finished.emit(code)

    @QtCore.Slot()
    def _read(self) -> None:
        # Buffer bytes as well as lines: a Unicode character may span reads.
        if not hasattr(self, "_decoder"):
            import codecs
            self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        data = bytes(self.proc.readAllStandardOutput())
        self._buffer += self._decoder.decode(data, final=self._finished)
        while "\n" in self._buffer:
            raw, self._buffer = self._buffer.split("\n", 1)
            self._emit_line(raw)

    def _emit_line(self, raw: str) -> None:
        text = raw.rstrip("\r\n")
        if text.startswith("PROGRESS "):
            try:
                self.progress.emit(max(0, min(100, int(text.split()[1]))))
            except (ValueError, IndexError):
                pass
        elif text:
            self.line.emit(text)
