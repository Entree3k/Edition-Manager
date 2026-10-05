"""Settings dialog: edits the Config dataclass and saves it back to config.ini."""

from __future__ import annotations

import html
import json
import os
import threading
from dataclasses import replace
from datetime import datetime, timedelta

import requests
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from .. import config, cron
from ..config import ALL_MODULES, Config
from ..editions import format_title
from ..paths import PRESETS_FILE
from . import theme
from .widgets import MODULE_INFO, ModulesList, TimePicker, Toast

BUILTIN_PRESETS = {
    "Default": ["Cut", "Release"],
}


class SettingsDialog(QtWidgets.QDialog):
    # Results from background server probes (test connection / library refresh).
    _test_result = QtCore.Signal(bool, str)
    _libs_result = QtCore.Signal(bool, object)  # ok, list of library names | error text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(960, 760)
        self.setMinimumSize(820, 620)
        self.cfg: Config = config.load()
        self._toast = Toast(self)
        self._test_result.connect(self._on_test_result)
        self._libs_result.connect(self._on_libs_result)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(14)
        title = QtWidgets.QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        layout.addWidget(self._hint("Connect your server and customize how your edition tags are built."))
        body = QtWidgets.QHBoxLayout()
        body.setSpacing(18)
        self.navigation = QtWidgets.QListWidget()
        self.navigation.setObjectName("SettingsNav")
        self.navigation.setFixedWidth(156)
        self.pages = QtWidgets.QStackedWidget()
        sections = [
            ("Server", self._build_server_tab), ("Modules", self._build_modules_tab),
            ("Language", self._build_language_tab), ("Rating", self._build_rating_tab),
            ("Performance", self._build_performance_tab),
            ("Appearance", self._build_appearance_tab), ("Scheduler", self._build_scheduler_tab),
        ]
        for name, build in sections:
            item = QtWidgets.QListWidgetItem(name)
            item.setSizeHint(QtCore.QSize(140, 44))
            self.navigation.addItem(item)
            page = build()
            if name == "Modules":
                self.modules_list.setMinimumHeight(230)
            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.pages.addWidget(scroll)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        body.addWidget(self.navigation)
        body.addWidget(self.pages, 1)
        layout.addLayout(body, 1)

        buttons = QtWidgets.QDialogButtonBox()
        save_btn = buttons.addButton("Save Changes", QtWidgets.QDialogButtonBox.AcceptRole)
        save_btn.setObjectName("Primary")
        save_btn.setDefault(True)
        buttons.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _hint(text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text)
        label.setObjectName("Hint")
        label.setWordWrap(True)
        return label

    # ---- Server tab -----------------------------------------------------------

    @staticmethod
    def _section(title: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(title)
        label.setObjectName("SectionTitle")
        return label

    @staticmethod
    def _divider() -> QtWidgets.QFrame:
        line = QtWidgets.QFrame()
        line.setObjectName("Divider")
        line.setFixedHeight(1)
        return line

    def _build_server_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # -- Plex server ----------------------------------------------------
        layout.addWidget(self._section("PLEX SERVER"))
        form = QtWidgets.QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)

        self.server_address = QtWidgets.QLineEdit(self.cfg.address)
        self.server_address.setPlaceholderText("http://127.0.0.1:32400")
        form.addRow("Server URL", self.server_address)

        token_row = QtWidgets.QHBoxLayout()
        token_row.setSpacing(6)
        self.server_token = QtWidgets.QLineEdit(self.cfg.token)
        self.server_token.setEchoMode(QtWidgets.QLineEdit.Password)
        btn_show = QtWidgets.QPushButton("Show")
        btn_show.setObjectName("Outlined")
        btn_show.setCheckable(True)
        btn_show.setFixedWidth(64)
        btn_show.toggled.connect(lambda on: (
            self.server_token.setEchoMode(
                QtWidgets.QLineEdit.Normal if on else QtWidgets.QLineEdit.Password),
            btn_show.setText("Hide" if on else "Show"),
        ))
        token_row.addWidget(self.server_token, 1)
        token_row.addWidget(btn_show)
        form.addRow("Token", token_row)

        test_row = QtWidgets.QHBoxLayout()
        test_row.setSpacing(10)
        self.btn_test = QtWidgets.QPushButton("Test Connection")
        self.btn_test.setObjectName("Primary")
        self.btn_test.clicked.connect(self._test_connection)
        self.test_status = QtWidgets.QLabel("")
        test_row.addWidget(self.btn_test)
        test_row.addWidget(self.test_status, 1)
        form.addRow("", test_row)
        layout.addLayout(form)

        layout.addSpacing(4)
        layout.addWidget(self._divider())

        # -- Libraries --------------------------------------------------------
        lib_header = QtWidgets.QHBoxLayout()
        lib_header.addWidget(self._section("LIBRARIES"))
        lib_header.addStretch(1)
        self.btn_refresh_libs = QtWidgets.QPushButton("Refresh")
        self.btn_refresh_libs.setObjectName("Outlined")
        self.btn_refresh_libs.clicked.connect(self._refresh_library_list)
        lib_header.addWidget(self.btn_refresh_libs)
        layout.addLayout(lib_header)
        layout.addWidget(self._hint("Checked libraries are skipped when processing."))

        self.skip_list = QtWidgets.QListWidget()
        self.skip_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        layout.addWidget(self.skip_list, 1)
        self.skip_status = self._hint("Click 'Refresh' to load movie libraries from the server.")
        layout.addWidget(self.skip_status)

        layout.addSpacing(4)
        layout.addWidget(self._divider())

        # -- Webhook ------------------------------------------------------------
        layout.addWidget(self._section("WEBHOOK"))
        hook_row = QtWidgets.QHBoxLayout()
        self.webhook_enabled = QtWidgets.QCheckBox("Enable webhook server (starts with the GUI)")
        self.webhook_enabled.setChecked(self.cfg.webhook_enabled)
        self.webhook_port = QtWidgets.QSpinBox()
        self.webhook_port.setRange(1, 65535)
        self.webhook_port.setValue(self.cfg.webhook_port)
        self.webhook_port.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.webhook_port.setFixedWidth(80)
        hook_row.addWidget(self.webhook_enabled)
        hook_row.addStretch(1)
        hook_row.addWidget(QtWidgets.QLabel("Port"))
        hook_row.addWidget(self.webhook_port)
        layout.addLayout(hook_row)
        layout.addWidget(self._hint(
            "Point a Plex webhook at http://<this-machine>:<port>/edition-manager "
            "to tag movies automatically as they are added."))
        return tab

    def _server_base(self) -> str:
        return self.server_address.text().strip().rstrip("/")

    def _plex_headers(self) -> dict:
        return {"X-Plex-Token": self.server_token.text().strip(), "Accept": "application/json"}

    @staticmethod
    def _probe_server(base: str, headers: dict):
        """Check the server and list its movie libraries. Returns (ok, names | error)."""
        try:
            resp = requests.get(base + "/library/sections", headers=headers, timeout=8)
            resp.raise_for_status()
            names = [d.get("title", "") for d in
                     resp.json().get("MediaContainer", {}).get("Directory", [])
                     if d.get("type") == "movie" and d.get("title")]
            return True, names
        except requests.exceptions.Timeout:
            return False, "Connection timed out"
        except requests.exceptions.ConnectionError:
            return False, "Could not connect to server"
        except requests.exceptions.HTTPError as err:
            code = err.response.status_code if err.response is not None else "Unknown"
            if code == 401:
                return False, "Invalid token (401 Unauthorized)"
            return False, f"HTTP error: {code}"
        except Exception as err:
            return False, f"Error: {type(err).__name__}"

    def _set_test_status(self, text: str, color: str | None = None) -> None:
        self.test_status.setText(text)
        self.test_status.setStyleSheet(f"color: {color}; font-weight: 600;" if color else "")

    @QtCore.Slot()
    def _test_connection(self) -> None:
        self.btn_test.setEnabled(False)
        self._set_test_status("Testing…")
        base, headers = self._server_base(), self._plex_headers()

        def _work():
            ok, result = self._probe_server(base, headers)
            try:
                self._test_result.emit(ok, "Connection successful" if ok else result)
            except RuntimeError:
                pass  # dialog closed while the probe was running

        threading.Thread(target=_work, daemon=True).start()

    @QtCore.Slot(bool, str)
    def _on_test_result(self, ok: bool, message: str) -> None:
        self.btn_test.setEnabled(True)
        t = theme.current
        self._set_test_status(("✓ " if ok else "✗ ") + message, t.success if ok else t.danger)

    @QtCore.Slot()
    def _refresh_library_list(self) -> None:
        self.btn_refresh_libs.setEnabled(False)
        self.skip_list.clear()
        self.skip_status.setText("Connecting to server…")
        base, headers = self._server_base(), self._plex_headers()

        def _work():
            ok, result = self._probe_server(base, headers)
            try:
                self._libs_result.emit(ok, result)
            except RuntimeError:
                pass

        threading.Thread(target=_work, daemon=True).start()

    @QtCore.Slot(bool, object)
    def _on_libs_result(self, ok: bool, result) -> None:
        self.btn_refresh_libs.setEnabled(True)
        if not ok:
            self.skip_status.setText(result)
            return
        if not result:
            self.skip_status.setText("No movie libraries found on server.")
            return
        for title in result:
            item = QtWidgets.QListWidgetItem(title)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if title in self.cfg.skip_libraries else Qt.Unchecked)
            self.skip_list.addItem(item)
        n = len(result)
        self.skip_status.setText(f"Found {n} movie librar{'y' if n == 1 else 'ies'}.")

    # ---- Modules tab -----------------------------------------------------------

    def _build_modules_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        preset_row = QtWidgets.QHBoxLayout()
        preset_row.addWidget(QtWidgets.QLabel("Preset:"))
        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.setMinimumWidth(200)
        preset_row.addWidget(self.preset_combo, 1)
        self.btn_load_preset = QtWidgets.QPushButton("Load")
        self.btn_load_preset.setObjectName("Primary")
        self.btn_load_preset.clicked.connect(self._load_selected_preset)
        preset_row.addWidget(self.btn_load_preset)
        self.btn_delete_preset = QtWidgets.QPushButton("Delete")
        self.btn_delete_preset.setObjectName("Outlined")
        self.btn_delete_preset.clicked.connect(self._delete_selected_preset)
        preset_row.addWidget(self.btn_delete_preset)
        self.preset_combo.currentIndexChanged.connect(self._update_preset_actions)
        self._load_presets()
        layout.addLayout(preset_row)

        layout.addWidget(self._hint(
            "Checked modules build the edition title in order - #1 comes first, "
            "then #2, and so on. Drag a row or use the arrows to reorder."))

        list_row = QtWidgets.QHBoxLayout()
        list_row.setSpacing(8)
        self.modules_list = ModulesList(ALL_MODULES, self.cfg.modules)
        list_row.addWidget(self.modules_list, 1)

        move_col = QtWidgets.QVBoxLayout()
        move_col.setSpacing(6)
        btn_up = QtWidgets.QPushButton("▲")
        btn_down = QtWidgets.QPushButton("▼")
        for btn, tip, delta in ((btn_up, "Move selected module up", -1),
                                (btn_down, "Move selected module down", 1)):
            btn.setObjectName("Outlined")
            btn.setFixedWidth(40)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _checked=False, d=delta: self.modules_list.move_current(d))
            move_col.addWidget(btn)
        move_col.addStretch(1)
        list_row.addLayout(move_col)
        layout.addLayout(list_row, 1)

        # Live preview of the edition title built from the current selection.
        self.title_preview = QtWidgets.QLabel()
        self.title_preview.setWordWrap(True)
        self.title_preview.setTextFormat(Qt.RichText)
        layout.addWidget(self.title_preview)

        save_row = QtWidgets.QHBoxLayout()
        save_row.addWidget(QtWidgets.QLabel("Save selection as preset:"))
        self.preset_name = QtWidgets.QLineEdit()
        self.preset_name.setPlaceholderText("Enter preset name…")
        save_row.addWidget(self.preset_name, 1)
        btn_save = QtWidgets.QPushButton("Save Preset")
        btn_save.setObjectName("Primary")
        btn_save.clicked.connect(self._save_preset)
        save_row.addWidget(btn_save)
        layout.addLayout(save_row)

        # Edition title format
        fmt_group = QtWidgets.QGroupBox("Edition Title Format")
        fmt_form = QtWidgets.QFormLayout(fmt_group)
        self.template_separator = QtWidgets.QLineEdit(self.cfg.separator.strip())
        self.template_separator.setMaximumWidth(80)
        self.template_max_length = QtWidgets.QSpinBox()
        self.template_max_length.setRange(0, 500)
        self.template_max_length.setValue(self.cfg.max_length)
        self.template_max_length.setSpecialValueText("Unlimited")
        fmt_form.addRow("Separator", self.template_separator)
        fmt_form.addRow("Max Length", self.template_max_length)
        layout.addWidget(fmt_group)

        self.modules_list.changed.connect(self._update_title_preview)
        self.template_separator.textChanged.connect(self._update_title_preview)
        self.template_max_length.valueChanged.connect(self._update_title_preview)
        self._update_title_preview()
        return tab

    def _update_title_preview(self) -> None:
        t = theme.current
        separator = f" {self.template_separator.text().strip() or '•'} "
        modules = self.modules_list.enabled_modules_in_order()
        examples = {
            m: MODULE_INFO[m][1] for m in modules
            if m in MODULE_INFO
        }
        preview_cfg = replace(self.cfg, modules=modules, separator=separator,
                              max_length=self.template_max_length.value())
        if examples:
            body = html.escape(format_title(examples, preview_cfg))
        else:
            body = "<i>(no modules enabled)</i>"
        self.title_preview.setText(
            f'<span style="color:{t.accent}; font-weight:600;">Preview&nbsp;&nbsp;</span>'
            f"{body}")

    def _read_user_presets(self) -> dict:
        if PRESETS_FILE.exists():
            try:
                with PRESETS_FILE.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _write_user_presets(self, presets: dict) -> None:
        PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PRESETS_FILE.open("w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)

    def _load_presets(self) -> None:
        self.preset_combo.clear()
        self.preset_combo.addItem("-- Select a preset --", userData=None)
        for name, modules in BUILTIN_PRESETS.items():
            self.preset_combo.addItem(f"{name} (Built-in)",
                                      userData={"name": name, "modules": modules, "builtin": True})
        for name, modules in self._read_user_presets().items():
            self.preset_combo.addItem(name,
                                      userData={"name": name, "modules": modules, "builtin": False})
        self._update_preset_actions()

    def _update_preset_actions(self) -> None:
        data = self.preset_combo.currentData()
        self.btn_load_preset.setEnabled(bool(data))
        self.btn_delete_preset.setEnabled(bool(data) and not data.get("builtin", False))
        if data and data.get("builtin"):
            self.btn_delete_preset.setToolTip("Built-in presets cannot be deleted.")
        elif data:
            self.btn_delete_preset.setToolTip("Delete this custom preset.")
        else:
            self.btn_delete_preset.setToolTip("Select a custom preset to delete it.")

    def _load_selected_preset(self) -> None:
        data = self.preset_combo.currentData()
        if not data or not data.get("modules"):
            return
        self.modules_list.set_enabled_order(data["modules"])
        self._toast.show_message(f"Preset '{data['name']}' loaded")

    def _save_preset(self) -> None:
        name = self.preset_name.text().strip()
        if not name:
            self._toast.show_message("Please enter a preset name", ok=False)
            return
        modules = self.modules_list.enabled_modules_in_order()
        if not modules:
            self._toast.show_message("No modules selected", ok=False)
            return
        try:
            presets = self._read_user_presets()
            presets[name] = modules
            self._write_user_presets(presets)
        except Exception as err:
            self._toast.show_message(f"Failed to save preset: {err}", ok=False)
            return
        self._toast.show_message(f"Preset '{name}' saved")
        self.preset_name.clear()
        self._load_presets()

    def _delete_selected_preset(self) -> None:
        data = self.preset_combo.currentData()
        if not data:
            return
        if data.get("builtin"):
            self._toast.show_message("Cannot delete built-in presets", ok=False)
            return
        try:
            presets = self._read_user_presets()
            presets.pop(data["name"], None)
            self._write_user_presets(presets)
        except Exception as err:
            self._toast.show_message(f"Failed to delete preset: {err}", ok=False)
            return
        self._toast.show_message(f"Preset '{data['name']}' deleted")
        self._load_presets()

    # ---- Language tab ------------------------------------------------------------

    def _build_language_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        self.excluded_languages = QtWidgets.QLineEdit(", ".join(sorted(self.cfg.excluded_languages)))
        form.addRow("Excluded Languages", self.excluded_languages)
        form.addRow(self._hint("Use commas to separate languages, e.g. English, French."))
        self.skip_multiple = QtWidgets.QCheckBox("Skip movies with multiple audio tracks")
        self.skip_multiple.setChecked(self.cfg.skip_multiple_audio_tracks)
        form.addRow("", self.skip_multiple)
        return tab

    # ---- Rating tab ----------------------------------------------------------------

    def _build_rating_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        src_box = QtWidgets.QWidget()
        src_layout = QtWidgets.QHBoxLayout(src_box)
        src_layout.setContentsMargins(0, 0, 0, 0)
        src_layout.setSpacing(12)
        self.src_tmdb = QtWidgets.QRadioButton("TMDb")
        self.src_rt = QtWidgets.QRadioButton("Rotten Tomatoes")
        self.src_letterboxd = QtWidgets.QRadioButton("Letterboxd")
        for radio in (self.src_tmdb, self.src_rt, self.src_letterboxd):
            src_layout.addWidget(radio)
        src_layout.addStretch(1)
        {"letterboxd": self.src_letterboxd,
         "rotten_tomatoes": self.src_rt}.get(self.cfg.rating_source, self.src_tmdb).setChecked(True)
        form.addRow("Rating Source", src_box)

        rt_box = QtWidgets.QWidget()
        rt_layout = QtWidgets.QHBoxLayout(rt_box)
        rt_layout.setContentsMargins(0, 0, 0, 0)
        rt_layout.setSpacing(12)
        self.rt_critics = QtWidgets.QRadioButton("Critics")
        self.rt_audience = QtWidgets.QRadioButton("Audiences")
        rt_layout.addWidget(self.rt_critics)
        rt_layout.addWidget(self.rt_audience)
        rt_layout.addStretch(1)
        (self.rt_critics if self.cfg.rotten_tomatoes_type == "critic" else self.rt_audience).setChecked(True)
        form.addRow("Rotten Tomatoes Type", rt_box)

        form.addRow(self._hint(
            "Rotten Tomatoes type only applies when the source is Rotten Tomatoes.\n"
            "Letterboxd ratings display as 'X.X/5'. TMDb requires an API key below."))

        self.tmdb_key = QtWidgets.QLineEdit(self.cfg.tmdb_api_key)
        self.tmdb_key.setEchoMode(QtWidgets.QLineEdit.Password)
        form.addRow("TMDb API Key", self.tmdb_key)
        return tab

    # ---- Performance tab ----------------------------------------------------------

    def _build_performance_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)

        self._cpu_threads = os.cpu_count() or 4
        form.addRow("Hardware", QtWidgets.QLabel(f"Detected CPU Threads: {self._cpu_threads}"))

        self.size_combo = QtWidgets.QComboBox()
        self.size_combo.addItem("Small (≤ 500 movies)", userData="small")
        self.size_combo.addItem("Medium (500–2,000 movies)", userData="medium")
        self.size_combo.addItem("Large (2,000+ movies)", userData="large")
        form.addRow("Library Size", self.size_combo)

        btn_recommend = QtWidgets.QPushButton("Apply Recommendation")
        btn_recommend.setObjectName("Primary")
        btn_recommend.clicked.connect(self._apply_recommendation)
        form.addRow("", btn_recommend)

        self.max_workers = QtWidgets.QSpinBox()
        self.max_workers.setRange(1, 256)
        self.max_workers.setValue(self.cfg.max_workers)
        self.batch_size = QtWidgets.QSpinBox()
        self.batch_size.setRange(1, 5000)
        self.batch_size.setValue(self.cfg.batch_size)
        form.addRow("Max Workers", self.max_workers)
        form.addRow("Batch Size", self.batch_size)
        form.addRow(self._hint("Max Workers = how many movies at once. Batch Size = how many per round."))
        return tab

    @QtCore.Slot()
    def _apply_recommendation(self) -> None:
        threads = self._cpu_threads
        size_key = self.size_combo.currentData()
        if size_key == "small":
            workers, batch = min(8, threads), 25
        elif size_key == "medium":
            workers, batch = min(16, threads), 50
        else:  # large
            workers = 24 if threads >= 16 else 16 if threads >= 8 else 8
            batch = 100
        workers = max(4, min(24, workers))
        self.max_workers.setValue(workers)
        self.batch_size.setValue(batch)
        self._toast.show_message(f"Applied {workers} workers / batch {batch} (CPU threads: {threads})")

    # ---- Appearance tab --------------------------------------------------------------

    def _build_appearance_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(tab)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)

        self._accent_color = self.cfg.primary_color
        btn_color = QtWidgets.QPushButton("Select Accent Color…")
        btn_color.setObjectName("Outlined")
        btn_color.clicked.connect(self._choose_color)
        self.color_swatch = QtWidgets.QLabel(self._accent_color)
        self.color_swatch.setMinimumWidth(90)
        self.color_swatch.setAlignment(Qt.AlignCenter)
        self._update_swatch()
        form.addRow("Accent Color", btn_color)
        form.addRow("Current Color", self.color_swatch)

        self.dark_mode = QtWidgets.QCheckBox("Enable dark mode")
        self.dark_mode.setChecked(self.cfg.dark_mode)
        form.addRow("", self.dark_mode)
        return tab

    def _update_swatch(self) -> None:
        self.color_swatch.setText(self._accent_color)
        self.color_swatch.setStyleSheet(
            f"background-color: {self._accent_color}; color: white;"
            f"border-radius: 6px; padding: 6px; font-weight: 600;")

    def _choose_color(self) -> None:
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self._accent_color), self, "Select Accent Color")
        if color.isValid():
            self._accent_color = color.name()
            self._update_swatch()

    # ---- Scheduler tab ---------------------------------------------------------------

    _WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    def _build_scheduler_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.scheduler_enabled = QtWidgets.QCheckBox("Enable scheduled processing")
        self.scheduler_enabled.setChecked(self.cfg.scheduler_enabled)
        layout.addWidget(self.scheduler_enabled)
        layout.addWidget(self._hint(
            "Processes all movies automatically while the app is running "
            "(including minimized to tray)."))
        layout.addSpacing(4)
        layout.addWidget(self._divider())

        layout.addWidget(self._section("SCHEDULE"))
        self._sched_container = QtWidgets.QWidget()
        sched_layout = QtWidgets.QVBoxLayout(self._sched_container)
        sched_layout.setContentsMargins(0, 0, 0, 0)
        sched_layout.setSpacing(8)

        form = QtWidgets.QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        self.sched_freq = QtWidgets.QComboBox()
        self.sched_freq.addItem("Every day", userData="daily")
        self.sched_freq.addItem("Once a week", userData="weekly")
        self.sched_freq.addItem("Every few hours", userData="interval")
        self.sched_freq.addItem("Custom (cron expression)", userData="custom")
        form.addRow("Run", self.sched_freq)
        sched_layout.addLayout(form)

        self.sched_stack = QtWidgets.QStackedWidget()
        sched_layout.addWidget(self.sched_stack)

        def _page(rows: list[tuple[str, QtWidgets.QWidget]], hint: str = "") -> QtWidgets.QWidget:
            page = QtWidgets.QWidget()
            page_form = QtWidgets.QFormLayout(page)
            page_form.setContentsMargins(0, 0, 0, 0)
            page_form.setHorizontalSpacing(14)
            page_form.setVerticalSpacing(8)
            for label, widget in rows:
                page_form.addRow(label, widget)
            if hint:
                page_form.addRow(self._hint(hint))
            return page

        # Daily
        self.daily_time = TimePicker(QtCore.QTime(3, 0))
        self.sched_stack.addWidget(_page([("At", self.daily_time)]))

        # Weekly
        self.weekly_day = QtWidgets.QComboBox()
        self.weekly_day.addItems(self._WEEKDAYS)
        self.weekly_time = TimePicker(QtCore.QTime(3, 0))
        self.sched_stack.addWidget(_page([("On", self.weekly_day), ("At", self.weekly_time)]))

        # Interval
        self.interval_hours = QtWidgets.QSpinBox()
        self.interval_hours.setRange(1, 23)
        self.interval_hours.setValue(6)
        self.interval_hours.setSuffix(" hours")
        self.sched_stack.addWidget(_page(
            [("Every", self.interval_hours)], "Runs on the hour, e.g. every 6 hours = midnight, 6 AM, noon, 6 PM."))

        # Custom cron
        self.custom_cron = QtWidgets.QLineEdit()
        self.custom_cron.setPlaceholderText("0 3 * * *")
        self.sched_stack.addWidget(_page(
            [("Cron", self.custom_cron)],
            "Format: minute hour day month weekday - e.g. 30 2 * * 1-5 = weekdays at 2:30 AM."))

        # Plain-English summary + computed next run.
        self.sched_summary = QtWidgets.QLabel()
        self.sched_summary.setWordWrap(True)
        self.sched_summary.setTextFormat(Qt.RichText)
        sched_layout.addWidget(self.sched_summary)
        layout.addWidget(self._sched_container)

        layout.addSpacing(4)
        layout.addWidget(self._divider())
        last_run_row = QtWidgets.QHBoxLayout()
        last_run_row.addWidget(self._section("LAST RUN"))
        last_run_row.addWidget(QtWidgets.QLabel(self.cfg.scheduler_last_run or "Never"))
        last_run_row.addStretch(1)
        layout.addLayout(last_run_row)
        layout.addStretch(1)

        self._apply_cron_to_ui(self.cfg.scheduler_cron)

        self.scheduler_enabled.toggled.connect(self._sched_container.setEnabled)
        self._sched_container.setEnabled(self.scheduler_enabled.isChecked())
        for signal in (self.scheduler_enabled.toggled, self.sched_freq.currentIndexChanged,
                       self.daily_time.timeChanged, self.weekly_day.currentIndexChanged,
                       self.weekly_time.timeChanged, self.interval_hours.valueChanged,
                       self.custom_cron.textChanged):
            signal.connect(self._update_sched_summary)
        self.sched_freq.currentIndexChanged.connect(self.sched_stack.setCurrentIndex)
        self.sched_stack.setCurrentIndex(self.sched_freq.currentIndex())
        self._update_sched_summary()
        return tab

    def _apply_cron_to_ui(self, expr: str) -> None:
        """Populate the schedule builder from a cron expression, falling back to Custom."""
        self.custom_cron.setText(expr)
        parts = expr.split()
        if len(parts) == 5:
            minute, hour, day, month, weekday = parts
            if minute.isdigit() and hour.isdigit() and day == "*" and month == "*":
                time = QtCore.QTime(int(hour) % 24, int(minute) % 60)
                if weekday == "*":
                    self.sched_freq.setCurrentIndex(0)
                    self.daily_time.setTime(time)
                    return
                if weekday.isdigit() and 0 <= int(weekday) <= 6:
                    self.sched_freq.setCurrentIndex(1)
                    self.weekly_day.setCurrentIndex(int(weekday))
                    self.weekly_time.setTime(time)
                    return
            if (minute == "0" and hour.startswith("*/") and hour[2:].isdigit()
                    and day == "*" and month == "*" and weekday == "*"):
                self.sched_freq.setCurrentIndex(2)
                self.interval_hours.setValue(max(1, min(23, int(hour[2:]))))
                return
        self.sched_freq.setCurrentIndex(3)

    def _cron_from_ui(self) -> str:
        kind = self.sched_freq.currentData()
        if kind == "daily":
            t = self.daily_time.time()
            return f"{t.minute()} {t.hour()} * * *"
        if kind == "weekly":
            t = self.weekly_time.time()
            return f"{t.minute()} {t.hour()} * * {self.weekly_day.currentIndex()}"
        if kind == "interval":
            return f"0 */{self.interval_hours.value()} * * *"
        return self.custom_cron.text().strip()

    @staticmethod
    def _next_cron_run(expr: str) -> datetime | None:
        """Earliest future minute matching the expression (scans up to 60 days)."""
        candidate = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)
        for _ in range(60 * 24 * 60):
            if cron.matches_now(expr, candidate):
                return candidate
            candidate += timedelta(minutes=1)
        return None

    def _update_sched_summary(self, *_args) -> None:
        t = theme.current
        if not self.scheduler_enabled.isChecked():
            self.sched_summary.setText("Scheduling is disabled.")
            return

        kind = self.sched_freq.currentData()
        expr = self._cron_from_ui()
        if len(expr.split()) != 5:
            self.sched_summary.setText(
                f'<span style="color:{t.danger}; font-weight:600;">Invalid cron expression</span> '
                "- expected 5 fields: minute hour day month weekday.")
            return

        if kind == "daily":
            desc = f"every day at {self.daily_time.time().toString('h:mm AP')}"
        elif kind == "weekly":
            desc = (f"every {self.weekly_day.currentText()} at "
                    f"{self.weekly_time.time().toString('h:mm AP')}")
        elif kind == "interval":
            n = self.interval_hours.value()
            desc = "every hour" if n == 1 else f"every {n} hours"
        else:
            desc = "on the cron schedule"

        next_run = self._next_cron_run(expr)
        next_text = next_run.strftime("%A %b %d at %I:%M %p").replace(" 0", " ") if next_run else "never"
        self.sched_summary.setText(
            f'<span style="color:{t.accent}; font-weight:600;">Runs {html.escape(desc)}</span>'
            f' &nbsp;(cron: <code>{html.escape(expr)}</code>)<br>'
            f"Next run: {next_text}")

    # ---- Save -------------------------------------------------------------------------

    def on_save(self) -> None:
        cfg = self.cfg
        cfg.address = self._server_base()
        cfg.token = self.server_token.text().strip()
        if self.skip_list.count() > 0:  # only replace if the list was loaded
            cfg.skip_libraries = {
                self.skip_list.item(i).text() for i in range(self.skip_list.count())
                if self.skip_list.item(i).checkState() == Qt.Checked
            }
        cfg.modules = self.modules_list.enabled_modules_in_order()
        cfg.excluded_languages = {
            lang.strip() for lang in self.excluded_languages.text().split(",") if lang.strip()
        }
        cfg.skip_multiple_audio_tracks = self.skip_multiple.isChecked()
        if self.src_letterboxd.isChecked():
            cfg.rating_source = "letterboxd"
        elif self.src_rt.isChecked():
            cfg.rating_source = "rotten_tomatoes"
        else:
            cfg.rating_source = "imdb"  # historical key for the TMDb source
        cfg.rotten_tomatoes_type = "critic" if self.rt_critics.isChecked() else "audience"
        cfg.tmdb_api_key = self.tmdb_key.text().strip()
        cfg.max_workers = self.max_workers.value()
        cfg.batch_size = self.batch_size.value()
        cfg.separator = f" {self.template_separator.text().strip() or '•'} "
        cfg.max_length = self.template_max_length.value()
        cfg.webhook_enabled = self.webhook_enabled.isChecked()
        cfg.webhook_port = self.webhook_port.value()
        cfg.primary_color = self._accent_color
        cfg.dark_mode = self.dark_mode.isChecked()
        cfg.scheduler_enabled = self.scheduler_enabled.isChecked()
        expr = self._cron_from_ui()
        cfg.scheduler_cron = expr if len(expr.split()) == 5 else "0 3 * * *"

        config.save(cfg)
        self.accept()
