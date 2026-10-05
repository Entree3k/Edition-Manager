"""Main window: dashboard with actions, progress, and a color-coded activity log."""

from __future__ import annotations

import html
import random
import re
import sys
import threading
from collections import deque
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .. import __version__, backups, config, cron
from ..editions import format_title
from ..logutil import mask_sensitive
from ..paths import ASSETS_DIR, BACKUP_DIR, ROOT, UNDO_SNAPSHOT_FILE
from ..plex import PlexClient
from . import theme
from .search_dialog import SearchDialog
from .settings_dialog import SettingsDialog
from .widgets import Card, MODULE_INFO
from .worker import ProcessWorker

APP_TITLE = "Edition Manager"
MAX_LOG_BLOCKS = 1000

_FLAG_LABELS = {
    "--all": "Processing all movies",
    "--reset": "Resetting all movies",
    "--backup": "Backing up editions",
    "--restore": "Restoring editions",
    "--undo": "Undoing last operation",
    "--one-id": "Processing one movie",
    "--restore-file": "Restoring editions from file",
}


def _random_tagline() -> str | None:
    """Pick a fresh message at startup, ignoring blank lines and outer quotes."""
    try:
        lines = [line.strip().strip('"“”')
                 for line in (ASSETS_DIR / "messages.txt").read_text(encoding="utf-8").splitlines()
                 if line.strip().strip('"“”')]
        return random.choice(lines) if lines else None
    except (OSError, UnicodeError):
        return None


class CloseDialog(QtWidgets.QDialog):
    """Themed replacement for the close-window prompt: minimize to tray, quit, or cancel."""

    CANCEL, MINIMIZE, QUIT = range(3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Close Edition Manager")
        self.setFixedWidth(560)
        self._choice = self.CANCEL

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 18)
        layout.setSpacing(16)

        header = QtWidgets.QHBoxLayout()
        header.setSpacing(14)
        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            icon_label = QtWidgets.QLabel()
            pixmap = QtGui.QPixmap(str(icon_path)).scaled(
                44, 44, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            if not pixmap.isNull():
                painter = QtGui.QPainter(pixmap)
                painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), QtGui.QColor(theme.current.text))
                painter.end()
            icon_label.setPixmap(pixmap)
            header.addWidget(icon_label, 0, QtCore.Qt.AlignVCenter)

        text_col = QtWidgets.QVBoxLayout()
        text_col.setSpacing(4)
        title = QtWidgets.QLabel("Close Edition Manager?")
        title.setObjectName("PageTitle")
        title.setWordWrap(True)
        subtitle = QtWidgets.QLabel("Choose whether to keep the app running or exit.")
        subtitle.setObjectName("Hint")
        subtitle.setWordWrap(True)
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        header.addLayout(text_col, 1)
        layout.addLayout(header)

        self.btn_minimize = QtWidgets.QPushButton("Minimize to Tray")
        self.btn_minimize.setObjectName("Primary")
        self.btn_minimize.setDefault(True)
        self.btn_minimize.setToolTip("Hide this window and keep background tasks running.")
        self.btn_quit = QtWidgets.QPushButton("Quit App")
        self.btn_quit.setObjectName("Danger")
        self.btn_quit.setAutoDefault(False)
        self.btn_quit.setToolTip("Exit Edition Manager and stop its background tasks.")

        for heading, description, button in (
            ("Keep running in the background",
             "Scheduled runs and webhooks stay active.\nReopen the window from the system tray.",
             self.btn_minimize),
            ("Quit Edition Manager",
             "Stop background tasks and close the app.\nAny active operation will be stopped.",
             self.btn_quit),
        ):
            card = Card()
            row = QtWidgets.QHBoxLayout(card)
            row.setContentsMargins(16, 16, 16, 16)
            row.setSpacing(16)
            copy = QtWidgets.QVBoxLayout()
            copy.setSpacing(6)
            heading_label = QtWidgets.QLabel(heading)
            heading_label.setObjectName("CardTitle")
            heading_label.setWordWrap(True)
            description_label = QtWidgets.QLabel(description)
            description_label.setObjectName("Hint")
            description_label.setWordWrap(True)
            copy.addWidget(heading_label)
            copy.addWidget(description_label)
            row.addLayout(copy, 1)
            row.addWidget(button, 0, QtCore.Qt.AlignVCenter)
            layout.addWidget(card)

        divider = QtWidgets.QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(8)
        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        self.btn_cancel.setObjectName("Outlined")
        self.btn_cancel.setAutoDefault(False)
        buttons.addStretch(1)
        buttons.addWidget(self.btn_cancel)
        layout.addLayout(buttons)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_quit.clicked.connect(lambda: self._finish(self.QUIT))
        self.btn_minimize.clicked.connect(lambda: self._finish(self.MINIMIZE))

    def _finish(self, choice: int) -> None:
        self._choice = choice
        self.accept()

    def ask(self) -> int:
        """Run modally; returns CANCEL, MINIMIZE, or QUIT (Esc = CANCEL)."""
        self.exec()
        return self._choice


class MainWindow(QtWidgets.QMainWindow):
    _connection_result = QtCore.Signal(bool, str)

    def __init__(self):
        super().__init__()
        self.cfg = config.load()
        self._current_worker: ProcessWorker | None = None
        self._webhook_proc: QtCore.QProcess | None = None
        self._force_quit = False
        self._cancel_requested = False
        self._operation_errors = False
        self._log_entries = deque(maxlen=MAX_LOG_BLOCKS)
        self._connection_generation = 0

        self.setWindowTitle(f"{APP_TITLE} for Plex")
        self.resize(1160, 900)
        self.setMinimumSize(940, 680)
        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))

        self._build_ui()
        self._setup_tray()
        self._connection_result.connect(self._on_connection_result)
        self._check_connection()

        QtCore.QTimer.singleShot(0, self._apply_webhook_state)

        # Scheduler: check every minute whether the cron expression matches.
        self._scheduler_timer = QtCore.QTimer(self)
        self._scheduler_timer.timeout.connect(self._check_scheduler)
        self._scheduler_timer.start(60_000)
        QtCore.QTimer.singleShot(5000, self._check_scheduler)

    # ---- UI construction -------------------------------------------------------

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidget(central)
        scroll.setObjectName("DashboardScroll")
        central.setObjectName("Dashboard")
        self.setCentralWidget(scroll)
        root = QtWidgets.QVBoxLayout(central)
        root.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        root.setContentsMargins(28, 22, 28, 16)
        root.setSpacing(16)

        # Header bar
        bar = QtWidgets.QFrame()
        bar.setObjectName("AppBar")
        bar_layout = QtWidgets.QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 0, 0, 8)
        self.brand_icon = QtWidgets.QLabel()
        self._refresh_brand_icon()
        bar_layout.addWidget(self.brand_icon)
        bar_layout.addSpacing(6)
        title_col = QtWidgets.QVBoxLayout()
        title_col.setSpacing(2)
        title_label = QtWidgets.QLabel(APP_TITLE)
        title_label.setObjectName("AppTitle")
        version_label = QtWidgets.QLabel(_random_tagline() or "Thoughtful edition tags for your Plex library.")
        version_label.setObjectName("AppTagline")
        version_label.setTextFormat(QtCore.Qt.PlainText)
        version_label.setWordWrap(True)
        version_label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        title_col.addWidget(title_label)
        title_col.addWidget(version_label)
        bar_layout.addLayout(title_col, 1)
        bar_layout.addStretch(1)

        self.status_pill = QtWidgets.QLabel("● Connecting…")
        self.status_pill.setObjectName("StatusPill")
        bar_layout.addWidget(self.status_pill)

        self.btn_settings = QtWidgets.QPushButton("Settings")
        self.btn_settings.setObjectName("Outlined")
        self.btn_settings.setShortcut("Ctrl+,")
        self.btn_settings.setToolTip("Settings (Ctrl+,)")
        self.btn_settings.clicked.connect(self.open_settings)
        bar_layout.addWidget(self.btn_settings)
        root.addWidget(bar)

        # A compact overview uses configuration and local backup data only.
        overview = QtWidgets.QHBoxLayout()
        overview.setSpacing(14)
        self.modules_metric, self.modules_detail = self._overview_card(overview, "EDITION MODULES")
        self.backup_metric, self.backup_detail = self._overview_card(overview, "LATEST BACKUP")
        self.automation_metric, self.automation_detail = self._overview_card(overview, "AUTOMATION")
        root.addLayout(overview)

        workspace = QtWidgets.QHBoxLayout()
        workspace.setSpacing(14)
        library_card = Card()
        library_card.setMinimumHeight(220)
        library = QtWidgets.QVBoxLayout(library_card)
        library.setContentsMargins(20, 18, 20, 18)
        library.setSpacing(10)
        library.addWidget(self._label("Manage your library", "CardTitle"))
        library.addWidget(self._label("Apply your edition rules to every movie, or find a single title.", "Hint"))
        library.addWidget(self._label("EDITION PREVIEW · EXAMPLE VALUES", "GroupLabel"))
        self.edition_preview = self._label("", "Preview")
        self.edition_preview.setWordWrap(True)
        self.edition_preview.setMinimumHeight(52)
        library.addWidget(self.edition_preview)
        library.addStretch(1)
        library_buttons = QtWidgets.QHBoxLayout()
        self.btn_all = QtWidgets.QPushButton("Process All Movies")
        self.btn_all.setObjectName("Primary")
        self.btn_all.setToolTip("Apply the enabled modules to all included movie libraries. An undo snapshot is created first.")
        self.btn_one = QtWidgets.QPushButton("Find a Movie…")
        self.btn_one.setObjectName("Outlined")
        self.btn_one.setShortcut("Ctrl+F")
        self.btn_one.setToolTip("Search Plex and process a single movie (Ctrl+F)")
        library_buttons.addWidget(self.btn_all)
        library_buttons.addWidget(self.btn_one)
        library_buttons.addStretch(1)
        library.addLayout(library_buttons)
        workspace.addWidget(library_card, 3)

        safety_card = Card()
        safety_card.setMinimumHeight(220)
        safety = QtWidgets.QVBoxLayout(safety_card)
        safety.setContentsMargins(20, 18, 20, 18)
        safety.setSpacing(10)
        safety.addWidget(self._label("Backup & recovery", "CardTitle"))
        safety.addWidget(self._label("Keep a snapshot before making changes.", "Hint"))
        safety_grid = QtWidgets.QGridLayout()
        safety_grid.setSpacing(8)
        self.btn_backup = QtWidgets.QPushButton("Create Backup")
        self.btn_restore = QtWidgets.QPushButton("Restore Latest")
        self.btn_restore_file = QtWidgets.QPushButton("Restore From File…")
        self.btn_undo = QtWidgets.QPushButton("Undo Last Run")
        for btn in (self.btn_backup, self.btn_restore, self.btn_restore_file, self.btn_undo):
            btn.setObjectName("Outlined")

        for position, btn in enumerate((self.btn_backup, self.btn_restore, self.btn_restore_file, self.btn_undo)):
            safety_grid.addWidget(btn, position // 2, position % 2)
        safety.addLayout(safety_grid)
        safety.addStretch(1)
        self.btn_reset = QtWidgets.QPushButton("Reset All Edition Tags…")
        self.btn_reset.setObjectName("Danger")
        self.btn_reset.setToolTip("Remove all edition tags from included movie libraries. Confirmation required.")
        safety.addWidget(self.btn_reset)
        workspace.addWidget(safety_card, 2)
        root.addLayout(workspace)

        # Progress card
        progress_card = Card()
        progress_layout = QtWidgets.QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(20, 14, 20, 14)
        progress_header = QtWidgets.QHBoxLayout()
        self.operation_label = self._label("Ready when you are", "CardTitle")
        self.progress_detail = self._label("Choose an action above to get started.", "Hint")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        self.btn_cancel.setObjectName("Text")
        self.btn_cancel.setEnabled(False)
        progress_header.addWidget(self.operation_label)
        progress_header.addStretch(1)
        progress_header.addWidget(self.btn_cancel)
        progress_layout.addLayout(progress_header)
        progress_layout.addWidget(self.progress)
        progress_layout.addWidget(self.progress_detail)
        root.addWidget(progress_card)

        # Activity log card
        log_card = Card()
        log_card.setMinimumHeight(240)
        log_layout = QtWidgets.QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 14, 20, 16)
        log_header = QtWidgets.QHBoxLayout()
        log_title = self._label("Activity", "CardTitle")
        self.log_filter = QtWidgets.QLineEdit()
        self.log_filter.setPlaceholderText("Filter activity…")
        self.log_filter.setClearButtonEnabled(True)
        self.log_filter.setMaximumWidth(240)
        self.log_filter.textChanged.connect(self._render_log)
        self.follow_log = QtWidgets.QCheckBox("Auto-scroll")
        self.follow_log.setChecked(True)
        self.btn_export = QtWidgets.QPushButton("Export…")
        self.btn_export.setObjectName("Text")
        self.btn_export.clicked.connect(self._export_log)
        self.btn_clear = QtWidgets.QPushButton("Clear")
        self.btn_clear.setObjectName("Text")
        log_header.addWidget(log_title)
        log_header.addStretch(1)
        log_header.addWidget(self.log_filter)
        log_header.addWidget(self.follow_log)
        log_header.addWidget(self.btn_export)
        log_header.addWidget(self.btn_clear)
        log_layout.addLayout(log_header)

        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        mono = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        mono.setPointSize(10)
        self.log.setFont(mono)
        self.log.setPlaceholderText("Your activity will appear here. Process a movie or create a backup to begin.")
        self.log.document().setMaximumBlockCount(MAX_LOG_BLOCKS)
        self.log.setMinimumHeight(140)
        log_layout.addWidget(self.log, 1)
        root.addWidget(log_card, 1)

        # Footer
        footer = QtWidgets.QHBoxLayout()
        self.webhook_status = self._label("Webhook off", "Hint")
        footer.addWidget(self.webhook_status)
        footer.addStretch(1)
        footer_label = QtWidgets.QLabel(f"Edition Manager v{__version__}  •  Built with ❤️")
        footer_label.setObjectName("Hint")
        footer.addWidget(footer_label)
        root.addLayout(footer)

        # Wiring
        self.btn_all.clicked.connect(lambda: self.run_flag("--all"))
        self.btn_one.clicked.connect(self.open_search)
        self.btn_reset.clicked.connect(self._confirm_reset)
        self.btn_backup.clicked.connect(lambda: self.run_flag("--backup"))
        self.btn_restore.clicked.connect(lambda: self.run_flag("--restore"))
        self.btn_restore_file.clicked.connect(self._restore_from_file)
        self.btn_undo.clicked.connect(self._confirm_undo)
        self.btn_cancel.clicked.connect(self.cancel_current_operation)
        self.btn_clear.clicked.connect(self._clear_log)
        self._refresh_dashboard()

    @staticmethod
    def _label(text: str, name: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        label.setTextFormat(QtCore.Qt.PlainText)
        label.setObjectName(name)
        return label

    def _overview_card(self, layout, title):
        card = Card()
        column = QtWidgets.QVBoxLayout(card)
        column.setContentsMargins(18, 14, 18, 14)
        column.setSpacing(5)
        column.addWidget(self._label(title, "GroupLabel"))
        value = self._label("", "Metric")
        detail = self._label("", "Hint")
        detail.setWordWrap(True)
        column.addWidget(value)
        column.addWidget(detail)
        layout.addWidget(card, 1)
        return value, detail

    def _refresh_dashboard(self) -> None:
        self._refresh_brand_icon()
        cfg = self.cfg
        self.modules_metric.setText(f"{len(cfg.modules)} enabled")
        self.modules_detail.setText("Custom template" if cfg.template_format.lower() != "auto" else "Applied in your selected order")
        examples = {name: MODULE_INFO[name][1] for name in cfg.modules if name in MODULE_INFO}
        self.edition_preview.setText(format_title(examples, cfg) if examples else "Enable edition modules in Settings to build your tags.")
        self.edition_preview.setToolTip("Sample values demonstrate your saved formatting rules; actual tags depend on each movie.")
        files = backups.list_backups()
        if files:
            latest = files[-1]
            modified = datetime.fromtimestamp(latest.stat().st_mtime)
            self.backup_metric.setText(modified.strftime("%b %d, %Y"))
            self.backup_detail.setText(f"{len(files)} saved · Latest at {modified.strftime('%I:%M %p').lstrip('0')}")
            self.backup_metric.setToolTip(latest.name)
        else:
            self.backup_metric.setText("No backups yet")
            self.backup_detail.setText("Create your first recovery snapshot")
        self.automation_metric.setText("Scheduled" if cfg.scheduler_enabled else "Manual")
        if cfg.scheduler_enabled:
            next_run = SettingsDialog._next_cron_run(cfg.scheduler_cron)
            detail = f"Next: {next_run.strftime('%a, %b %d · %I:%M %p')}" if next_run else "Check your schedule in Settings"
        else:
            detail = "Run on demand or set up a schedule"
        self.automation_detail.setText(detail)
        self._set_buttons_enabled(self._current_worker is None)

    def _refresh_brand_icon(self) -> None:
        pixmap = QtGui.QPixmap(str(ASSETS_DIR / "icon.png")).scaled(
            48, 48, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        if not pixmap.isNull():
            painter = QtGui.QPainter(pixmap)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QtGui.QColor(theme.current.text))
            painter.end()
        self.brand_icon.setPixmap(pixmap)

    # ---- Connection status ---------------------------------------------------------

    def _check_connection(self) -> None:
        cfg = self.cfg
        self._connection_generation += 1
        generation = self._connection_generation
        self.status_pill.setText("● Connecting…")
        self._set_connection_style("busy")
        if not cfg.address or not cfg.token:
            self._on_connection_result(False, "")
            return

        def _work():
            try:
                name = PlexClient(cfg.address, cfg.token).server_name()
                if generation == self._connection_generation:
                    self._connection_result.emit(True, name)
            except Exception:
                if generation == self._connection_generation:
                    self._connection_result.emit(False, "")

        threading.Thread(target=_work, daemon=True).start()

    @QtCore.Slot(bool, str)
    def _on_connection_result(self, ok: bool, name: str) -> None:
        if ok:
            self.status_pill.setText("● Connected")
            self.status_pill.setToolTip(f"Connected to {name}")
            self._set_connection_style("success")
        else:
            self.status_pill.setText("● Not connected")
            self.status_pill.setToolTip("Open Settings → Server to check your address and token.")
            self._set_connection_style("error")

    def _set_connection_style(self, state: str) -> None:
        self.status_pill.setProperty("state", state)
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

    # ---- Activity log ----------------------------------------------------------------

    _ERROR_PAT = re.compile(r"\b(error|failed|failure|exception|traceback)\b", re.I)
    _WARN_PAT = re.compile(r"\b(warn|warning|skipped)\b", re.I)
    _OK_PAT = re.compile(r"\b(completed successfully|complete\.|connected to server|backup complete|done\.)\b", re.I)

    @QtCore.Slot(str)
    def append_log(self, text: str) -> None:
        text = mask_sensitive(text)
        self._log_entries.append(text)
        if self._current_worker and self._ERROR_PAT.search(text):
            self._operation_errors = True
        if self.log_filter.text().casefold() in text.casefold():
            self._append_log_line(text)

    def _append_log_line(self, text: str) -> None:
        t = theme.current
        if self._ERROR_PAT.search(text):
            color = t.danger
        elif self._WARN_PAT.search(text):
            color = t.warning
        elif self._OK_PAT.search(text):
            color = t.success
        else:
            color = None

        escaped = html.escape(text)
        scrollbar = self.log.verticalScrollBar()
        position = scrollbar.value()
        self.log.append(f'<span style="color:{color or t.text}">{escaped}</span>')
        scrollbar.setValue(scrollbar.maximum() if self.follow_log.isChecked() else position)

    def _render_log(self) -> None:
        self.log.clear()
        query = self.log_filter.text().casefold()
        for entry in self._log_entries:
            if query in entry.casefold():
                self._append_log_line(entry)

    def _clear_log(self) -> None:
        self._log_entries.clear()
        self.log.clear()

    def _export_log(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export activity", "edition-manager-activity.txt", "Text files (*.txt)")
        if path:
            try:
                Path(path).write_text("\n".join(self._log_entries), encoding="utf-8")
            except OSError as err:
                QtWidgets.QMessageBox.warning(self, "Export failed", str(err))

    # ---- Running operations --------------------------------------------------------------

    def run_flag(self, flag: str) -> None:
        if self._current_worker is not None:
            return
        self._set_buttons_enabled(False)
        self._cancel_requested = False
        self._operation_errors = False
        self.btn_cancel.setEnabled(True)
        self.btn_cancel.setText("Cancel")
        base_flag = flag.split("=")[0]
        self.operation_label.setText(_FLAG_LABELS.get(base_flag, "Working…"))
        self.progress.setValue(0)
        self.progress_detail.setText("Preparing operation…")

        worker = ProcessWorker(flag, self)
        worker.line.connect(self.append_log)
        worker.progress.connect(self._set_progress)
        worker.started.connect(lambda: self.progress.setRange(0, 0))
        worker.finished.connect(self._on_finished)
        self._current_worker = worker
        QtCore.QTimer.singleShot(0, worker.start)

    @QtCore.Slot(int)
    def _set_progress(self, value: int) -> None:
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        self.progress.setValue(max(0, min(100, value)))
        self.progress_detail.setText(f"{self.progress.value()}% complete")

    @QtCore.Slot(int)
    def _on_finished(self, code: int) -> None:
        worker = self._current_worker
        self._current_worker = None
        if worker:
            worker.deleteLater()
        self._refresh_dashboard()
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setText("Cancel")
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        if self._cancel_requested:
            self.progress.setValue(0)
            self.operation_label.setText("Operation cancelled")
            self.progress_detail.setText("Changes already applied remain in Plex. Use undo after a bulk run if needed.")
            self.append_log("Operation cancelled by user.")
        elif code == 0:
            self.progress.setValue(100)
            if self._operation_errors:
                self.operation_label.setText("Finished with errors")
                self.progress_detail.setText("Review the activity log for movies or modules that failed.")
                self.append_log("Warning: operation finished with errors. Review the activity log.")
            else:
                self.operation_label.setText("Operation complete")
                self.progress_detail.setText("All done. You can start another action.")
                self.append_log("Completed successfully.")
        else:
            self.operation_label.setText("Operation failed")
            self.progress_detail.setText("Review the activity log for details before trying again.")
            self.append_log(f"Error: operation exited with code {code}.")

    def cancel_current_operation(self) -> None:
        if self._current_worker:
            self._cancel_requested = True
            self._current_worker.kill()
            self.operation_label.setText("Cancelling operation…")
            self.progress_detail.setText("Waiting for the operation to stop.")
            self.btn_cancel.setText("Cancelling…")
            self.btn_cancel.setEnabled(False)
        else:
            self.append_log("No active operation to cancel.")

    def _set_buttons_enabled(self, enabled: bool) -> None:
        for btn in (self.btn_all, self.btn_one, self.btn_reset, self.btn_backup,
                    self.btn_restore, self.btn_restore_file, self.btn_undo, self.btn_settings):
            btn.setEnabled(enabled)
        self.btn_restore.setEnabled(enabled and bool(backups.latest_backup()))
        self.btn_restore.setToolTip("Restore the newest saved backup." if self.btn_restore.isEnabled() else "Create a backup before restoring the latest snapshot.")
        self.btn_undo.setEnabled(enabled and UNDO_SNAPSHOT_FILE.exists())
        self.btn_undo.setToolTip("Revert the last bulk operation." if self.btn_undo.isEnabled() else "Available after processing or resetting all movies.")

    # ---- Actions -----------------------------------------------------------------------

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            self.cfg = config.load()
            app = QtWidgets.QApplication.instance()
            theme.apply(app, self.cfg.dark_mode, self.cfg.primary_color)
            self._refresh_dashboard()
            self._render_log()
            self._check_connection()
            self._apply_webhook_state()

    def open_search(self) -> None:
        plex = PlexClient(self.cfg.address, self.cfg.token)
        dialog = SearchDialog(plex, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            rating_key = dialog.chosen_rating_key()
            if rating_key:
                self.run_flag(f"--one-id={rating_key}")

    def _confirm_reset(self) -> None:
        reply = QtWidgets.QMessageBox.warning(
            self, "Confirm Reset",
            "This will remove ALL edition tags from your movies.\n\n"
            "You can revert with 'Undo Last' or a backup.\n\n"
            "Are you sure you want to continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.run_flag("--reset")

    def _restore_from_file(self) -> None:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose Edition Manager backup", str(BACKUP_DIR),
            "JSON Backups (*.json);;All Files (*)",
        )
        if path:
            self.run_flag(f"--restore-file={path}")

    def _confirm_undo(self) -> None:
        if not UNDO_SNAPSHOT_FILE.exists():
            QtWidgets.QMessageBox.warning(
                self, "No Undo Available",
                "No undo snapshot available.\n\nAn undo snapshot is created automatically "
                "before each 'Process All' or 'Reset All' operation.")
            return

        created_at, movie_count = "Unknown time", 0
        try:
            import json
            with UNDO_SNAPSHOT_FILE.open("r", encoding="utf-8") as f:
                snapshot = json.load(f)
            created_at = snapshot.get("created_at", created_at)
            movie_count = len(snapshot.get("data", {}))
        except Exception:
            pass

        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Undo",
            f"Undo the last operation?\n\nSnapshot created: {created_at}\n"
            f"Movies to restore: {movie_count}\n\nThis reverts all edition titles to their "
            f"state before the last 'Process All' or 'Reset All'.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.run_flag("--undo")

    # ---- Scheduler ----------------------------------------------------------------------

    @QtCore.Slot()
    def _check_scheduler(self) -> None:
        cfg = config.load()  # re-read so settings changes apply live
        self.cfg = cfg
        self._refresh_dashboard()
        if not cfg.scheduler_enabled or self._current_worker is not None:
            return
        if not cron.matches_now(cfg.scheduler_cron):
            return
        # Avoid double-running within the same minute.
        now = datetime.now()
        if cfg.scheduler_last_run:
            try:
                last = datetime.strptime(cfg.scheduler_last_run, "%Y-%m-%d %H:%M:%S")
                if last.replace(second=0, microsecond=0) == now.replace(second=0, microsecond=0):
                    return
            except ValueError:
                pass

        self.append_log(f"[Scheduler] Starting scheduled processing (cron: {cfg.scheduler_cron})...")
        cfg.scheduler_last_run = now.strftime("%Y-%m-%d %H:%M:%S")
        config.save(cfg)
        self.cfg = cfg
        self.run_flag("--all")

    # ---- Webhook subprocess ----------------------------------------------------------------

    _WEBHOOK_DROP_PATTERNS = [
        re.compile(r"^INFO:", re.I),
        re.compile(r"\bProcessing ratingKey=", re.I),
        re.compile(r"^PROGRESS\b", re.I),
    ]

    def _apply_webhook_state(self) -> None:
        if config.load().webhook_enabled:
            # Rebind the process after saving server, port, or module changes.
            self._stop_webhook()
            self._start_webhook()
        else:
            self._stop_webhook()
        self._refresh_dashboard()

    def _start_webhook(self) -> None:
        if self._webhook_proc and self._webhook_proc.state() != QtCore.QProcess.NotRunning:
            return
        self.append_log("Starting webhook server…")
        self._webhook_recent = deque(maxlen=100)
        self._webhook_buffer = ""
        import codecs
        self._webhook_decoder = codecs.getincrementaldecoder("utf-8")("replace")

        proc = QtCore.QProcess(self)
        proc.setWorkingDirectory(str(ROOT))
        proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        proc.setProcessEnvironment(env)
        if sys.platform.startswith("win"):
            try:
                proc.setCreateProcessArgumentsModifier(
                    lambda args: args.update(creationFlags=0x08000000))
            except Exception:
                pass
        proc.readyReadStandardOutput.connect(self._on_webhook_output)
        proc.started.connect(lambda: self.webhook_status.setText(f"Webhook starting · Port {self.cfg.webhook_port}"))
        proc.errorOccurred.connect(lambda _error: self._on_webhook_error(proc.errorString()))
        proc.finished.connect(self._on_webhook_finished)
        self._webhook_proc = proc
        self.webhook_status.setText("Webhook starting…")
        proc.start(sys.executable, ["-u", str(ROOT / "webhook_server.py")])

    def _on_webhook_error(self, message: str) -> None:
        self.webhook_status.setText("Webhook failed · Check activity")
        self.append_log(f"Error: webhook process: {message}")

    def _on_webhook_finished(self, code: int, _status) -> None:
        self._on_webhook_output()
        self.webhook_status.setText("Webhook stopped")
        self.append_log(f"Webhook server stopped (exit={code}).")

    def _stop_webhook(self) -> None:
        if self._webhook_proc and self._webhook_proc.state() != QtCore.QProcess.NotRunning:
            self._webhook_proc.terminate()
            if not self._webhook_proc.waitForFinished(2000):
                self._webhook_proc.kill()
                self._webhook_proc.waitForFinished(2000)
        if self._webhook_proc:
            self._webhook_proc.deleteLater()
        self._webhook_proc = None
        self.webhook_status.setText("Webhook off")

    @QtCore.Slot()
    def _on_webhook_output(self) -> None:
        if not self._webhook_proc:
            return
        self._webhook_buffer += self._webhook_decoder.decode(bytes(self._webhook_proc.readAllStandardOutput()))
        while "\n" in self._webhook_buffer:
            raw, self._webhook_buffer = self._webhook_buffer.split("\n", 1)
            line = raw.strip()
            if "Webhook server listening on" in line:
                self.webhook_status.setText(f"Webhook running · Port {self.cfg.webhook_port}")
            if not line or any(p.search(line) for p in self._WEBHOOK_DROP_PATTERNS):
                continue
            if line in self._webhook_recent:
                continue
            self._webhook_recent.append(line)
            self.append_log(f"[webhook] {line}")

    # ---- System tray ----------------------------------------------------------------------

    def _setup_tray(self) -> None:
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            return
        self._tray_icon = QtWidgets.QSystemTrayIcon(self)
        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            self._tray_icon.setIcon(QtGui.QIcon(str(icon_path)))
        else:
            self._tray_icon.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self._tray_icon.setToolTip(APP_TITLE)

        menu = QtWidgets.QMenu()
        menu.addAction("Show Window").triggered.connect(self._tray_show)
        menu.addSeparator()
        menu.addAction("Process All Movies").triggered.connect(lambda: self.run_flag("--all"))
        menu.addAction("Backup Editions").triggered.connect(lambda: self.run_flag("--backup"))
        menu.addSeparator()
        menu.addAction("Quit").triggered.connect(self._tray_quit)
        self._tray_icon.setContextMenu(menu)
        self._tray_icon.activated.connect(self._tray_activated)
        self._tray_icon.show()

    @QtCore.Slot(QtWidgets.QSystemTrayIcon.ActivationReason)
    def _tray_activated(self, reason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self._tray_show()

    def _tray_show(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _tray_quit(self) -> None:
        self._force_quit = True
        self.close()

    # ---- Window lifecycle ---------------------------------------------------------------------

    def changeEvent(self, event: QtCore.QEvent) -> None:
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.windowState() & QtCore.Qt.WindowMinimized:
                if self._tray_icon and self._tray_icon.isVisible():
                    QtCore.QTimer.singleShot(0, self.hide)
                    self._tray_icon.showMessage(
                        APP_TITLE, "Minimized to system tray. Scheduler continues running.",
                        QtWidgets.QSystemTrayIcon.Information, 2000)
        super().changeEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self._force_quit or not (self._tray_icon and self._tray_icon.isVisible()):
            self._quit(event)
            return

        choice = CloseDialog(self).ask()
        if choice == CloseDialog.MINIMIZE:
            event.ignore()
            self.hide()
            self._tray_icon.showMessage(
                APP_TITLE,
                "Minimized to system tray.\nScheduler and webhook continue running.\n"
                "Right-click the tray icon to quit.",
                QtWidgets.QSystemTrayIcon.Information, 3000)
        elif choice == CloseDialog.QUIT:
            self._quit(event)
        else:
            event.ignore()

    def _quit(self, event: QtGui.QCloseEvent) -> None:
        try:
            self._connection_generation += 1
            if self._current_worker:
                self._current_worker.kill()
                self._current_worker.proc.waitForFinished(2000)
            self._stop_webhook()
            if self._tray_icon:
                self._tray_icon.hide()
        finally:
            event.accept()
            QtWidgets.QApplication.quit()
