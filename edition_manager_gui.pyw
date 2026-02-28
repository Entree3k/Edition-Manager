import os
import sys
import re
import json
import configparser
import random
import requests
from datetime import datetime
from pathlib import Path
from collections import deque
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QProcess

APP_TITLE = "🎬 Edition Manager"

_version = "v1.9.0"
_msg_file = Path(__file__).parent / "assets" / "messages.txt"

_tagline = None
if _msg_file.exists():
    try:
        lines = [
            ln.strip().strip('"').strip("“”")
            for ln in _msg_file.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        if lines:
            _tagline = random.choice(lines)
    except Exception:
        _tagline = None

APP_VERSION = f"{_version} - {_tagline}" if _tagline else _version
PRIMARY_SCRIPT = "edition_manager.py"
CONFIG_FILE = str(Path(__file__).parent / "config" / "config.ini")

DEFAULT_MODULES = [
    "AudioChannels", "AudioCodec", "Bitrate", "ContentRating", "Country", "Cut",
    "Director", "Duration", "DynamicRange", "FrameRate", "Genre",
    "Language", "Rating", "Release", "Resolution", "ShortFilm", "Size",
    "Source", "SpecialFeatures", "Studio", "VideoCodec", "Writer",
]

def apply_light_palette(app: QtWidgets.QApplication, primary_color: str = "#6750A4") -> None:
    app.setStyle("Fusion")
    pal = QtGui.QPalette()
    pal.setColor(QtGui.QPalette.Window,        QtGui.QColor("#F6F6FA"))
    pal.setColor(QtGui.QPalette.WindowText,    QtGui.QColor(20, 18, 26))
    pal.setColor(QtGui.QPalette.Base,          QtGui.QColor("#FFFFFF"))
    pal.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#F4F4F8"))
    pal.setColor(QtGui.QPalette.ToolTipBase,   QtGui.QColor("#FFFFFF"))
    pal.setColor(QtGui.QPalette.ToolTipText,   QtGui.QColor(20, 18, 26))
    pal.setColor(QtGui.QPalette.Text,          QtGui.QColor(20, 18, 26))
    pal.setColor(QtGui.QPalette.Button,        QtGui.QColor("#FFFFFF"))
    pal.setColor(QtGui.QPalette.ButtonText,    QtGui.QColor(20, 18, 26))
    pal.setColor(QtGui.QPalette.BrightText,    QtCore.Qt.red)
    pal.setColor(QtGui.QPalette.Highlight,     QtGui.QColor(primary_color))
    pal.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#FFFFFF"))
    app.setPalette(pal)

def apply_dark_palette(app: QtWidgets.QApplication, primary_color: str = "#6750A4") -> None:
    app.setStyle("Fusion")
    pal = QtGui.QPalette()

    bg      = QtGui.QColor("#121212")
    card    = QtGui.QColor("#1E1E1E")
    text    = QtGui.QColor("#FFFFFF")
    subtext = QtGui.QColor(255, 255, 255, 200)
    base    = QtGui.QColor("#151515")

    pal.setColor(QtGui.QPalette.Window,              bg)
    pal.setColor(QtGui.QPalette.WindowText,          text)
    pal.setColor(QtGui.QPalette.Base,                base)
    pal.setColor(QtGui.QPalette.AlternateBase,       card)
    pal.setColor(QtGui.QPalette.ToolTipBase,         card)
    pal.setColor(QtGui.QPalette.ToolTipText,         text)
    pal.setColor(QtGui.QPalette.Text,                text)
    pal.setColor(QtGui.QPalette.Button,              card)
    pal.setColor(QtGui.QPalette.ButtonText,          text)
    pal.setColor(QtGui.QPalette.BrightText,          QtCore.Qt.red)
    pal.setColor(QtGui.QPalette.Highlight,           QtGui.QColor(primary_color))
    pal.setColor(QtGui.QPalette.HighlightedText,     QtGui.QColor("#FFFFFF"))
    pal.setColor(QtGui.QPalette.PlaceholderText,     subtext)

    app.setPalette(pal)

class ProcessWorker(QtCore.QObject):
    started = QtCore.Signal()
    line = QtCore.Signal(str)
    progress = QtCore.Signal(int)
    finished = QtCore.Signal(int)

    def __init__(self, flag: str, parent=None):
        super().__init__(parent)
        self.flag = flag
        self.proc = QtCore.QProcess(self)
        self.proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        if sys.platform.startswith("win"):
            def _no_console(args):
                args["creationFlags"] = 0x08000000
            try:
                self.proc.setCreateProcessArgumentsModifier(_no_console)
            except Exception:
                pass
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.finished.connect(self._done)

    def _detect_cpu_threads(self):
        threads = os.cpu_count()
        if threads is None:
            threads = 4  # fallback
        return threads

    def start(self):
        self.started.emit()
        python = sys.executable or "python3"
        script_path = str(Path(__file__).parent / PRIMARY_SCRIPT)
        if not os.path.exists(script_path):
            self.line.emit(f"Error: '{PRIMARY_SCRIPT}' not found next to GUI.")
            self.finished.emit(1)
            return
        args = [script_path, self.flag]
        self.line.emit("Running: {} {}".format(python, " ".join(args)))
        self.proc.start(python, args)

    @QtCore.Slot()
    def _read(self):
        data = self.proc.readAllStandardOutput().data().decode(errors="replace")
        for raw in data.splitlines():
            s = raw.rstrip("\n")

            if s.startswith("PROGRESS "):
                try:
                    pct = int(s.split()[1])
                    pct = max(0, min(100, pct))
                    self.progress.emit(pct)
                except Exception:
                    pass
                continue

            self.line.emit(s)

    @QtCore.Slot(int, QtCore.QProcess.ExitStatus)
    def _done(self, code: int, _status):
        self.finished.emit(code)

class ModulesList(QtWidgets.QListWidget):
    def __init__(self, modules: list[str], enabled_order: list[str], parent=None):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setAlternatingRowColors(True)
        enabled = [m for m in enabled_order if m in modules]
        disabled = [m for m in modules if m not in enabled]
        for m in enabled + disabled:
            it = QtWidgets.QListWidgetItem(m, self)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            it.setCheckState(Qt.Checked if m in enabled else Qt.Unchecked)

    def enabled_modules_in_order(self) -> list[str]:
        out = []
        for i in range(self.count()):
            it = self.item(i)
            if it.checkState() == Qt.Checked:
                out.append(it.text())
        return out

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(720, 560)
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setContentsMargins(12, 12, 12, 12)
        
        # Header / App Bar
        header = QtWidgets.QLabel("Settings")
        header.setObjectName("SectionHeaderBig")
        vbox.addWidget(header)

        tabs = QtWidgets.QTabWidget()
        vbox.addWidget(tabs, 1)

        # Prepare config
        self.cfg = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            self.cfg.read(CONFIG_FILE, encoding="utf-8")
        for sec in ("server","modules","language","rating","performance","appearance","webhook","scheduler"):
            if not self.cfg.has_section(sec):
                self.cfg.add_section(sec)
        if not self.cfg.has_option("webhook","enabled"):
            self.cfg.set("webhook","enabled","no")
        if not self.cfg.has_option("scheduler","enabled"):
            self.cfg.set("scheduler","enabled","no")

        # --- Server tab ---
        server = QtWidgets.QWidget(); tabs.addTab(server, "Server")
        form = QtWidgets.QFormLayout(server)
        form.setHorizontalSpacing(14); form.setVerticalSpacing(8)
        self.server_address = QtWidgets.QLineEdit(self.cfg.get("server","address", fallback=""))
        self.server_token = QtWidgets.QLineEdit(self.cfg.get("server","token", fallback=""))
        self.server_token.setEchoMode(QtWidgets.QLineEdit.Password)
        # Store skip libraries value for later use (hidden field)
        self._skip_libraries_value = self.cfg.get("server", "skip_libraries", fallback="")
        form.addRow("Server URL", self.server_address)
        form.addRow(QtWidgets.QLabel("e.g., http://127.0.0.1:32400"))
        form.addRow("Token", self.server_token)

        # Test connection button
        self.btn_test = QtWidgets.QPushButton("Test Connection")
        self.btn_test.setObjectName("Primary")
        self.btn_test.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))
        self.btn_test.clicked.connect(self._test_connection)
        form.addRow("", self.btn_test)

        # --- Skip Libraries section ---
        skip_group = QtWidgets.QGroupBox("Skip Libraries")
        skip_layout = QtWidgets.QVBoxLayout(skip_group)
        skip_layout.setContentsMargins(8, 8, 8, 8)
        skip_layout.setSpacing(6)

        skip_header = QtWidgets.QHBoxLayout()
        skip_header.addWidget(QtWidgets.QLabel("Check movie libraries to SKIP during processing:"))
        skip_header.addStretch(1)
        self.btn_refresh_libs = QtWidgets.QPushButton("Refresh")
        self.btn_refresh_libs.setObjectName("Outlined")
        self.btn_refresh_libs.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        self.btn_refresh_libs.clicked.connect(self._refresh_library_list)
        skip_header.addWidget(self.btn_refresh_libs)
        skip_layout.addLayout(skip_header)

        self.skip_libraries_list = QtWidgets.QListWidget()
        self.skip_libraries_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.skip_libraries_list.setMaximumHeight(120)
        self.skip_libraries_list.setAlternatingRowColors(True)
        skip_layout.addWidget(self.skip_libraries_list)

        self.skip_libs_status = QtWidgets.QLabel("Click 'Refresh' to load movie libraries from server")
        self.skip_libs_status.setStyleSheet("color: gray; font-size: 9pt;")
        skip_layout.addWidget(self.skip_libs_status)

        form.addRow(skip_group)

        # --- Webhook enable ---
        hook_group = QtWidgets.QGroupBox("Webhook")
        hook_layout = QtWidgets.QHBoxLayout(hook_group)
        self.webhook_enabled = QtWidgets.QCheckBox("Enable webhook server (start with GUI)")
        self.webhook_enabled.setChecked(self.cfg.get("webhook","enabled",fallback="no").lower() in ("1","true","yes","on"))
        hook_layout.addWidget(self.webhook_enabled)
        form.addRow(hook_group)
        self._webhook_proc = None

        # --- Modules tab ---
        modules_tab = QtWidgets.QWidget(); tabs.addTab(modules_tab, "Modules")
        m_v = QtWidgets.QVBoxLayout(modules_tab)
        m_v.setContentsMargins(8, 8, 8, 8)

        # Template selector row
        template_row = QtWidgets.QHBoxLayout()
        template_row.addWidget(QtWidgets.QLabel("Load Preset:"))
        self.template_combo = QtWidgets.QComboBox()
        self.template_combo.setMinimumWidth(200)
        self._load_module_templates()
        template_row.addWidget(self.template_combo, 1)
        self.btn_load_template = QtWidgets.QPushButton("Load")
        self.btn_load_template.setObjectName("Primary")
        self.btn_load_template.clicked.connect(self._load_selected_template)
        template_row.addWidget(self.btn_load_template)
        self.btn_delete_template = QtWidgets.QPushButton("Delete")
        self.btn_delete_template.setObjectName("Outlined")
        self.btn_delete_template.clicked.connect(self._delete_selected_template)
        template_row.addWidget(self.btn_delete_template)
        m_v.addLayout(template_row)

        m_v.addSpacing(8)
        m_v.addWidget(QtWidgets.QLabel("Drag to reorder. Check to enable. Enabled modules run top-to-bottom."))
        current_order = [m for m in re.split(r"[;]", self.cfg.get("modules","order", fallback="")) if m]
        self.modules_list = ModulesList(DEFAULT_MODULES, current_order)
        m_v.addWidget(self.modules_list, 1)

        # Save template row
        save_row = QtWidgets.QHBoxLayout()
        save_row.addWidget(QtWidgets.QLabel("Save current selection as preset:"))
        self.template_name_edit = QtWidgets.QLineEdit()
        self.template_name_edit.setPlaceholderText("Enter preset name...")
        save_row.addWidget(self.template_name_edit, 1)
        self.btn_save_template = QtWidgets.QPushButton("Save Preset")
        self.btn_save_template.setObjectName("Primary")
        self.btn_save_template.clicked.connect(self._save_module_template)
        save_row.addWidget(self.btn_save_template)
        m_v.addLayout(save_row)

        # --- Language tab ---
        lang_tab = QtWidgets.QWidget(); tabs.addTab(lang_tab, "Language")
        lf = QtWidgets.QFormLayout(lang_tab)
        lf.setHorizontalSpacing(14); lf.setVerticalSpacing(8)
        self.excluded_languages = QtWidgets.QLineEdit(self.cfg.get("language","excluded_languages", fallback=""))
        self.skip_multiple = QtWidgets.QCheckBox("Skip Multiple Audio Tracks")
        self.skip_multiple.setChecked(self.cfg.getboolean("language","skip_multiple_audio_tracks", fallback=False))
        lf.addRow("Excluded Languages", self.excluded_languages)
        lf.addRow(QtWidgets.QLabel("Use commas to separate languages"))
        lf.addRow("", self.skip_multiple)

        # --- Rating tab ---
        rating_tab = QtWidgets.QWidget(); tabs.addTab(rating_tab, "Rating")
        rf = QtWidgets.QFormLayout(rating_tab)
        rf.setHorizontalSpacing(14); rf.setVerticalSpacing(10)

        src_box = QtWidgets.QWidget(); src_layout = QtWidgets.QHBoxLayout(src_box)
        src_layout.setContentsMargins(0,0,0,0); src_layout.setSpacing(12)
        self.src_imdb = QtWidgets.QRadioButton("IMDB")
        self.src_rt   = QtWidgets.QRadioButton("Rotten Tomatoes")
        self.src_letterboxd = QtWidgets.QRadioButton("Letterboxd")
        src_layout.addWidget(self.src_imdb)
        src_layout.addWidget(self.src_rt)
        src_layout.addWidget(self.src_letterboxd)
        src_layout.addStretch(1)
        _src_val = self.cfg.get("rating","source", fallback="imdb").strip().lower()
        if _src_val == "letterboxd":
            self.src_letterboxd.setChecked(True)
        elif _src_val == "rotten_tomatoes":
            self.src_rt.setChecked(True)
        else:
            self.src_imdb.setChecked(True)
        rf.addRow("Rating Source", src_box)

        rt_box = QtWidgets.QWidget(); rt_layout = QtWidgets.QHBoxLayout(rt_box)
        rt_layout.setContentsMargins(0,0,0,0); rt_layout.setSpacing(12)
        self.rt_critics  = QtWidgets.QRadioButton("Critics")
        self.rt_audience = QtWidgets.QRadioButton("Audiences")
        rt_layout.addWidget(self.rt_critics)
        rt_layout.addWidget(self.rt_audience)
        rt_layout.addStretch(1)
        _rt_val = self.cfg.get("rating","rotten_tomatoes_type", fallback="critic").strip().lower()
        (self.rt_critics if _rt_val == "critic" else self.rt_audience).setChecked(True)
        rf.addRow("Rotten Tomatoes Type", rt_box)
        rf.addRow(QtWidgets.QLabel("Rotten Tomatoes type is used only when the source is Rotten Tomatoes.\n"
                                    "Letterboxd ratings are displayed as 'X.X/5' (out of 5 stars)."))

        # TMDb API Key
        self.tmdb_key = QtWidgets.QLineEdit(self.cfg.get("rating", "tmdb_api_key", fallback=""))
        self.tmdb_key.setEchoMode(QtWidgets.QLineEdit.Password)
        rf.addRow("TMDb API Key", self.tmdb_key)

        # --- Performance tab ---
        perf_tab = QtWidgets.QWidget(); tabs.addTab(perf_tab, "Performance")
        pf = QtWidgets.QFormLayout(perf_tab)
        pf.setHorizontalSpacing(14); pf.setVerticalSpacing(8)

        # detect CPU threads
        self._detected_threads = os.cpu_count() or 4

        # Row: detected hardware
        self.hw_label = QtWidgets.QLabel(
            f"Detected CPU Threads: {self._detected_threads}"
        )
        pf.addRow("Hardware", self.hw_label)

        # Row: library size selector
        self.size_combo = QtWidgets.QComboBox()
        self.size_combo.addItem("Small (≤ 500 movies)",        userData="small")
        self.size_combo.addItem("Medium (500–2,000 movies)",   userData="medium")
        self.size_combo.addItem("Large (2,000+ movies)", userData="large")
        pf.addRow("Library Size", self.size_combo)

        # Row: recommendation button
        self.rec_btn = QtWidgets.QPushButton("Apply Recommendation")
        self.rec_btn.setObjectName("Primary")
        self.rec_btn.clicked.connect(self._apply_recommendation)
        pf.addRow("", self.rec_btn)

        self.max_workers = QtWidgets.QSpinBox(); self.max_workers.setRange(1, 256)
        self.max_workers.setValue(int(self.cfg.get("performance","max_workers", fallback="10")))
        self.batch_size = QtWidgets.QSpinBox(); self.batch_size.setRange(1, 5000)
        self.batch_size.setValue(int(self.cfg.get("performance","batch_size", fallback="25")))
        pf.addRow("Max Workers", self.max_workers)
        pf.addRow("Batch Size", self.batch_size)

        # hint label
        pf.addRow(QtWidgets.QLabel(
            "Tip: Max Workers = how many movies at once.\n"
            "Batch Size = how many per round."
        ))

        # --- Appearance tab ---
        appearance_tab = QtWidgets.QWidget(); tabs.addTab(appearance_tab, "Appearance")
        af = QtWidgets.QFormLayout(appearance_tab)
        af.setHorizontalSpacing(14); af.setVerticalSpacing(8)
        current_color = self.cfg.get("appearance", "primary_color", fallback="#6750A4")
        self.primary_color_btn = QtWidgets.QPushButton("Select Primary Color…")
        self.primary_color_display = QtWidgets.QLabel(current_color)
        self.primary_color_display.setMinimumWidth(90)
        self.primary_color_display.setAlignment(Qt.AlignCenter)
        self.primary_color_display.setStyleSheet(
            f"background-color: {current_color}; border: 1px solid #CAC4D0; border-radius: 6px; padding: 6px;")
        self.primary_color_btn.clicked.connect(self.choose_primary_color)
        af.addRow("Primary Highlight Color", self.primary_color_btn)
        af.addRow("Current Color", self.primary_color_display)
        self.dark_mode_chk = QtWidgets.QCheckBox("Enable dark mode")
        self.dark_mode_chk.setChecked(self.cfg.getboolean("appearance", "dark_mode", fallback=False))
        af.addRow("", self.dark_mode_chk)
        self.cfg.set("appearance", "primary_color", self.primary_color_display.text().strip())
        self.cfg.set("appearance", "dark_mode", "yes" if self.dark_mode_chk.isChecked() else "no")

        # --- Scheduler tab ---
        scheduler_tab = QtWidgets.QWidget(); tabs.addTab(scheduler_tab, "Scheduler")
        sf = QtWidgets.QFormLayout(scheduler_tab)
        sf.setHorizontalSpacing(14); sf.setVerticalSpacing(10)

        self.scheduler_enabled = QtWidgets.QCheckBox("Enable scheduled processing")
        self.scheduler_enabled.setChecked(self.cfg.get("scheduler","enabled",fallback="no").lower() in ("1","true","yes","on"))
        sf.addRow("", self.scheduler_enabled)

        # Cron expression input
        self.scheduler_cron = QtWidgets.QLineEdit(self.cfg.get("scheduler","cron", fallback="0 3 * * *"))
        self.scheduler_cron.setPlaceholderText("0 3 * * *")
        sf.addRow("Cron Schedule", self.scheduler_cron)

        # Cron help label
        cron_help = QtWidgets.QLabel(
            "Format: minute hour day month weekday\n"
            "Examples:\n"
            "  0 3 * * *    = Daily at 3:00 AM\n"
            "  0 */6 * * *  = Every 6 hours\n"
            "  0 0 * * 0    = Weekly on Sunday at midnight\n"
            "  30 2 * * 1-5 = Weekdays at 2:30 AM"
        )
        cron_help.setStyleSheet("color: gray; font-size: 9pt;")
        sf.addRow("", cron_help)

        last_run = self.cfg.get("scheduler","last_run", fallback="")
        self.scheduler_last_run = QtWidgets.QLabel(last_run if last_run else "Never")
        sf.addRow("Last run", self.scheduler_last_run)

        sf.addRow(QtWidgets.QLabel(
            "When enabled, Edition Manager will automatically process\n"
            "all movies at the specified schedule while the GUI is open."
        ))

        # Hidden fields to maintain config compatibility (no longer in UI)
        self.template_format = QtWidgets.QLineEdit("auto")
        self.template_separator = QtWidgets.QLineEdit(self.cfg.get("template","separator", fallback=" · "))
        self.template_max_length = QtWidgets.QSpinBox()
        self.template_max_length.setValue(int(self.cfg.get("template","max_length", fallback="0")))

        # Footer buttons
        btn_box = QtWidgets.QDialogButtonBox()
        self.btn_save = btn_box.addButton("Save", QtWidgets.QDialogButtonBox.AcceptRole)
        btn_box.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)
        vbox.addWidget(btn_box)
        btn_box.accepted.connect(self.on_save)
        btn_box.rejected.connect(self.reject)

    def _recommend_performance(self, cpu_threads: int, size_key: str):

        def cap_workers(n):
            # never below 4, never above 24
            if n < 4:
                n = 4
            if n > 24:
                n = 24
            return n

        if size_key == "small":
            # ≤ 500 movies
            return {
                "max_workers": cap_workers(min(8, cpu_threads)),
                "batch_size": 25
            }

        if size_key == "medium":
            # 500–2,000 movies
            return {
                "max_workers": cap_workers(min(16, cpu_threads)),
                "batch_size": 50
            }

        if size_key == "large":
            # 2,000–5,000 movies
            if cpu_threads >= 16:
                workers = 24
            elif cpu_threads >= 8:
                workers = 16
            else:
                workers = 8
            return {
                "max_workers": workers,
                "batch_size": 100
            }

        # fallback default
        return {
            "max_workers": 8,
            "batch_size": 25
        }

    @QtCore.Slot()
    def _apply_recommendation(self):
        cpu_threads = self._detected_threads

        # which size did the user pick
        size_key = self.size_combo.currentData()

        rec = self._recommend_performance(cpu_threads, size_key)

        # fill the spinboxes in the UI
        self.max_workers.setValue(rec["max_workers"])
        self.batch_size.setValue(rec["batch_size"])

        # little toast/snackbar at the top of the dialog
        human_msg = (
            f"Applied {rec['max_workers']} workers / batch {rec['batch_size']} "
            f"(CPU threads: {cpu_threads})"
        )
        self._show_banner(human_msg, ok=True)

    # ---- Server helpers ----
    def _plex_headers(self):
        return {"X-Plex-Token": self.server_token.text().strip(), "Accept": "application/json"}

    def _server_base(self):
        return self.server_address.text().strip().rstrip("/")

    # ---- Banner helper ----
    def _show_banner(self, message: str, ok: bool = True):
        # Create once and reuse
        if not hasattr(self, "_banner"):
            self._banner = QtWidgets.QFrame(self)
            self._banner.setObjectName("Banner")
            self._banner.setStyleSheet("QFrame#Banner { border-radius: 8px; padding: 10px 16px; }")
            self._banner_lab = QtWidgets.QLabel(self._banner)
            h = QtWidgets.QHBoxLayout(self._banner); h.setContentsMargins(12,8,12,8); h.addWidget(self._banner_lab)
            self._banner.hide()

        # Color + text
        bg = "#1E8E3E" if ok else "#D93025"
        self._banner.setStyleSheet(f"QFrame#Banner {{ background: {bg}; color: #FFFFFF; }}")
        self._banner_lab.setText(message)

        # Position top-center inside dialog
        geo = self.geometry()
        self._banner.adjustSize()
        w, h = self._banner.sizeHint().width(), self._banner.sizeHint().height()
        x = geo.width()//2 - w//2
        y = 10
        self._banner.setGeometry(x, y, w, h)
        self._banner.show()

        # Auto-hide
        QtCore.QTimer.singleShot(2200, self._banner.hide)

    def _get_templates_file(self):
        return Path(CONFIG_FILE).parent / "module_presets.json"

    def _load_module_templates(self):
        """Load saved module presets into the combo box."""
        self.template_combo.clear()
        self.template_combo.addItem("-- Select a preset --", userData=None)

        # Add built-in presets
        builtin_presets = {
            "Default": ["Cut", "Release"],
        }
        for name, modules in builtin_presets.items():
            self.template_combo.addItem(f"{name} (Built-in)", userData={"name": name, "modules": modules, "builtin": True})

        # Load user presets from file
        templates_file = self._get_templates_file()
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    user_presets = json.load(f)
                for name, modules in user_presets.items():
                    self.template_combo.addItem(name, userData={"name": name, "modules": modules, "builtin": False})
            except Exception:
                pass

    def _save_module_template(self):
        """Save current module selection as a new preset."""
        name = self.template_name_edit.text().strip()
        if not name:
            self._show_banner("Please enter a preset name", ok=False)
            return

        # Get current module selection
        modules = self.modules_list.enabled_modules_in_order()
        if not modules:
            self._show_banner("No modules selected", ok=False)
            return

        # Load existing presets
        templates_file = self._get_templates_file()
        user_presets = {}
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    user_presets = json.load(f)
            except Exception:
                pass

        # Add/update preset
        user_presets[name] = modules

        # Save to file
        try:
            templates_file.parent.mkdir(parents=True, exist_ok=True)
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump(user_presets, f, indent=2)
            self._show_banner(f"Preset '{name}' saved", ok=True)
            self.template_name_edit.clear()
            self._load_module_templates()  # Refresh combo box
        except Exception as e:
            self._show_banner(f"Failed to save preset: {e}", ok=False)

    def _load_selected_template(self):
        """Load the selected preset into the modules list."""
        data = self.template_combo.currentData()
        if not data:
            return

        modules = data.get("modules", [])
        if not modules:
            return

        # Update the modules list
        for i in range(self.modules_list.count()):
            item = self.modules_list.item(i)
            if item.text() in modules:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

        # Reorder to match template order
        # First, collect all items
        items_data = []
        for i in range(self.modules_list.count()):
            item = self.modules_list.item(i)
            items_data.append((item.text(), item.checkState()))

        # Sort: enabled modules in template order first, then disabled
        def sort_key(item_tuple):
            name, state = item_tuple
            if name in modules:
                return (0, modules.index(name))
            else:
                return (1, DEFAULT_MODULES.index(name) if name in DEFAULT_MODULES else 999)

        items_data.sort(key=sort_key)

        # Rebuild the list
        self.modules_list.clear()
        for name, state in items_data:
            it = QtWidgets.QListWidgetItem(name, self.modules_list)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            it.setCheckState(state)

        self._show_banner(f"Preset '{data.get('name')}' loaded", ok=True)

    def _delete_selected_template(self):
        """Delete the selected user preset."""
        data = self.template_combo.currentData()
        if not data:
            return

        if data.get("builtin", False):
            self._show_banner("Cannot delete built-in presets", ok=False)
            return

        name = data.get("name")

        # Load existing presets
        templates_file = self._get_templates_file()
        if not templates_file.exists():
            return

        try:
            with open(templates_file, 'r', encoding='utf-8') as f:
                user_presets = json.load(f)

            if name in user_presets:
                del user_presets[name]
                with open(templates_file, 'w', encoding='utf-8') as f:
                    json.dump(user_presets, f, indent=2)
                self._show_banner(f"Preset '{name}' deleted", ok=True)
                self._load_module_templates()  # Refresh combo box
        except Exception as e:
            self._show_banner(f"Failed to delete preset: {e}", ok=False)

    @QtCore.Slot()
    def _test_connection(self):
        try:
            r = requests.get(self._server_base() + "/library/sections", headers=self._plex_headers(), timeout=8)
            r.raise_for_status()
            self._show_banner("Connection successful!", ok=True)
        except requests.exceptions.Timeout:
            self._show_banner("Connection timed out", ok=False)
        except requests.exceptions.ConnectionError:
            self._show_banner("Could not connect to server", ok=False)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                self._show_banner("Invalid token (401 Unauthorized)", ok=False)
            else:
                self._show_banner(f"HTTP error: {e.response.status_code if e.response else 'Unknown'}", ok=False)
        except Exception as e:
            self._show_banner(f"Error: {type(e).__name__}", ok=False)

    @QtCore.Slot()
    def _refresh_library_list(self):
        """Fetch movie libraries from server and populate the skip list."""
        self.skip_libraries_list.clear()
        self.skip_libs_status.setText("Connecting to server...")
        self.skip_libs_status.setStyleSheet("color: gray; font-size: 9pt;")
        QtWidgets.QApplication.processEvents()

        try:
            r = requests.get(
                self._server_base() + "/library/sections",
                headers=self._plex_headers(),
                timeout=8
            )
            r.raise_for_status()
            dirs = [
                d for d in r.json().get("MediaContainer", {}).get("Directory", [])
                if d.get("type") == "movie"
            ]
        except requests.exceptions.Timeout:
            self.skip_libs_status.setText("Connection timed out")
            self.skip_libs_status.setStyleSheet("color: #D93025; font-size: 9pt;")
            return
        except requests.exceptions.ConnectionError:
            self.skip_libs_status.setText("Could not connect to server")
            self.skip_libs_status.setStyleSheet("color: #D93025; font-size: 9pt;")
            return
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                self.skip_libs_status.setText("Invalid token (401 Unauthorized)")
            else:
                self.skip_libs_status.setText(f"HTTP error: {e.response.status_code if e.response else 'Unknown'}")
            self.skip_libs_status.setStyleSheet("color: #D93025; font-size: 9pt;")
            return
        except Exception as e:
            self.skip_libs_status.setText(f"Error: {type(e).__name__}")
            self.skip_libs_status.setStyleSheet("color: #D93025; font-size: 9pt;")
            return

        if not dirs:
            self.skip_libs_status.setText("No movie libraries found on server")
            self.skip_libs_status.setStyleSheet("color: gray; font-size: 9pt;")
            return

        # Get currently skipped libraries
        skip_now = {s.strip() for s in self._skip_libraries_value.split(";") if s.strip()}

        for d in dirs:
            title = d.get("title", "")
            if not title:
                continue
            it = QtWidgets.QListWidgetItem(title)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if title in skip_now else Qt.Unchecked)
            self.skip_libraries_list.addItem(it)

        lib_count = len(dirs)
        self.skip_libs_status.setText(f"Found {lib_count} movie librar{'y' if lib_count == 1 else 'ies'}")
        self.skip_libs_status.setStyleSheet("color: #1E8E3E; font-size: 9pt;")

    def _get_skip_libraries_from_list(self) -> str:
        """Get semicolon-separated list of checked (skipped) libraries."""
        skipped = []
        for i in range(self.skip_libraries_list.count()):
            it = self.skip_libraries_list.item(i)
            if it.checkState() == Qt.Checked:
                skipped.append(it.text())
        return ";".join(skipped)

    def choose_primary_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.primary_color_display.text()), self, "Select Primary Color")
        if color.isValid():
            hex_color = color.name()
            self.primary_color_display.setText(hex_color)
            self.primary_color_display.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #CAC4D0; border-radius: 6px; padding: 6px;")

    def on_save(self):
        for sec in ("server","modules","language","rating","performance","appearance","scheduler","template"):
            if not self.cfg.has_section(sec):
                self.cfg.add_section(sec)
        # server
        self.cfg.set("server", "address", self.server_address.text().strip())
        self.cfg.set("server", "token", self.server_token.text().strip())
        # Get skip libraries from list if populated, otherwise keep existing value
        if self.skip_libraries_list.count() > 0:
            skip_libs = self._get_skip_libraries_from_list()
        else:
            skip_libs = self._skip_libraries_value
        self.cfg.set("server", "skip_libraries", skip_libs)
        # modules
        self.cfg.set("modules", "order", ";".join(self.modules_list.enabled_modules_in_order()))
        # language
        self.cfg.set("language", "excluded_languages", self.excluded_languages.text().strip())
        self.cfg.set("language", "skip_multiple_audio_tracks", "yes" if self.skip_multiple.isChecked() else "no")
        # rating
        if self.src_letterboxd.isChecked():
            src_val = "letterboxd"
        elif self.src_rt.isChecked():
            src_val = "rotten_tomatoes"
        else:
            src_val = "imdb"
        rt_val = "critic" if self.rt_critics.isChecked() else "audience"
        self.cfg.set("rating", "source", src_val)
        self.cfg.set("rating", "rotten_tomatoes_type", rt_val)
        self.cfg.set("rating", "tmdb_api_key", self.tmdb_key.text().strip())
        # performance
        self.cfg.set("performance", "max_workers", str(self.max_workers.value()))
        self.cfg.set("performance", "batch_size", str(self.batch_size.value()))
        # appearance
        self.cfg.set("appearance", "primary_color", self.primary_color_display.text().strip())
        self.cfg.set("appearance", "dark_mode", "yes" if self.dark_mode_chk.isChecked() else "no")
        # scheduler (now with cron)
        self.cfg.set("scheduler", "enabled", "yes" if self.scheduler_enabled.isChecked() else "no")
        self.cfg.set("scheduler", "cron", self.scheduler_cron.text().strip() or "0 3 * * *")
        # template
        self.cfg.set("template", "format", self.template_format.text().strip() or "auto")
        self.cfg.set("template", "separator", self.template_separator.text() or " · ")
        self.cfg.set("template", "max_length", str(self.template_max_length.value()))

        cfg_dir = Path(CONFIG_FILE).parent
        cfg_dir.mkdir(parents=True, exist_ok=True)
        self.cfg.set("webhook","enabled", "yes" if self.webhook_enabled.isChecked() else "no")

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            self.cfg.write(f)
        self.accept()

class SearchDialog(QtWidgets.QDialog):
    def __init__(self, server_base: str, token: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search Movie in Plex")
        self.resize(720, 560)
        self._server = server_base
        self._token = token
        self._chosen_rating_key = None

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(12,12,12,12); v.setSpacing(8)

        row = QtWidgets.QHBoxLayout(); v.addLayout(row)
        self.edit = QtWidgets.QLineEdit(); self.edit.setPlaceholderText("Type a movie title…")
        self.btn = QtWidgets.QPushButton("Search")
        row.addWidget(self.edit, 1); row.addWidget(self.btn)
        self.btn.clicked.connect(self.search_now)
        self.edit.returnPressed.connect(self.search_now)

        self.listw = QtWidgets.QListWidget()
        self.listw.setViewMode(QtWidgets.QListView.IconMode)
        self.listw.setIconSize(QtCore.QSize(120, 180))
        self.listw.setResizeMode(QtWidgets.QListView.Adjust)
        self.listw.setMovement(QtWidgets.QListView.Static)
        self.listw.setSpacing(10)
        self.listw.itemDoubleClicked.connect(self.accept_selection)
        v.addWidget(self.listw, 1)

        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.button(QtWidgets.QDialogButtonBox.Ok).setText("Process Selected")
        bb.accepted.connect(self.accept_selection)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def chosen_rating_key(self):
        return self._chosen_rating_key

    def _get_json(self, url):
        r = requests.get(url, headers={"X-Plex-Token": self._token, "Accept": "application/json"}, timeout=10)
        r.raise_for_status()
        return r.json()

    def _libraries(self):
        data = self._get_json(self._server + "/library/sections")
        return [d for d in data.get('MediaContainer',{}).get('Directory',[]) if d.get('type') == 'movie']

    def search_now(self):
        q = self.edit.text().strip()
        if not q:
            return
        self.listw.clear()
        try:
            libs = self._libraries()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Could not fetch libraries:\n{e}")
            return

        results = []
        for lib in libs:
            key = lib.get('key')
            lib_title = lib.get('title')
            try:
                data = self._get_json(self._server + f"/library/sections/{key}/all?title={requests.utils.quote(q)}")
            except Exception:
                continue
            for m in data.get('MediaContainer',{}).get('Metadata',[]) or []:
                results.append((lib_title, m))

        for lib_title, m in results:
            title = m.get('title', 'Unknown')
            year  = m.get('year',  '')
            rk    = m.get('ratingKey')
            thumb = m.get('thumb')  # e.g. "/library/metadata/12345/thumb/..."
            # Try direct thumb path
            icon = QtGui.QIcon()
            if thumb:
                try:
                    url = f"{self._server}{thumb}"
                    # Use headers for token authentication instead of URL parameter
                    headers = {"X-Plex-Token": self._token}
                    img = requests.get(url, headers=headers, timeout=10).content
                    pm = QtGui.QPixmap()
                    pm.loadFromData(img)
                    icon = QtGui.QIcon(pm)
                except Exception:
                    pass

            it = QtWidgets.QListWidgetItem(icon, f"{title} ({year})\n{lib_title}")
            it.setData(QtCore.Qt.UserRole, rk)
            self.listw.addItem(it)

    def accept_selection(self):
        it = self.listw.currentItem()
        if not it:
            return
        self._chosen_rating_key = it.data(QtCore.Qt.UserRole)
        if not self._chosen_rating_key:
            return
        self.accept()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            self.cfg.read(CONFIG_FILE, encoding="utf-8")
        self.primary_color = self.cfg.get("appearance", "primary_color", fallback="#6750A4")
        self.dark_mode = self.cfg.getboolean("appearance", "dark_mode", fallback=False)

        self.setWindowTitle(f"{APP_TITLE} for Plex")
        self.resize(980, 720)

        self._webhook_proc = None
        QtCore.QTimer.singleShot(0, self._apply_webhook_state)

        # Set window icon (top-left & taskbar)
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))

        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ---- App Bar ----
        bar = QtWidgets.QFrame()
        bar.setObjectName("AppBar")
        bar_layout = QtWidgets.QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)
        title_lab = QtWidgets.QLabel(APP_TITLE); title_lab.setObjectName("AppTitle")
        ver_lab = QtWidgets.QLabel(APP_VERSION); ver_lab.setObjectName("AppVersion")
        bar_layout.addWidget(title_lab); bar_layout.addSpacing(8); bar_layout.addWidget(ver_lab); bar_layout.addStretch(1)
        root.addWidget(bar)

        # ---- Section: Actions ----
        actions_header = QtWidgets.QLabel("Actions"); actions_header.setObjectName("SectionTitle")
        root.addWidget(actions_header)
        actions_group = QtWidgets.QGroupBox(); actions_group.setObjectName("Card"); actions_group.setTitle("")
        ag = QtWidgets.QGridLayout(actions_group)
        ag.setContentsMargins(16, 16, 16, 16)
        ag.setHorizontalSpacing(10)

        self.btn_all = QtWidgets.QPushButton("Process All Movies"); self.btn_all.setObjectName("Primary")
        self.btn_one = QtWidgets.QPushButton("Process One Movie"); self.btn_one.setObjectName("Primary")
        self.btn_reset = QtWidgets.QPushButton("Reset All Movies"); self.btn_reset.setObjectName("Outlined")
        self.btn_backup = QtWidgets.QPushButton("Backup Editions"); self.btn_backup.setObjectName("Outlined")
        self.btn_restore = QtWidgets.QPushButton("Restore Editions"); self.btn_restore.setObjectName("Outlined")
        self.btn_restore_file = QtWidgets.QPushButton("Restore from file…"); self.btn_restore_file.setObjectName("Outlined")
        self.btn_undo = QtWidgets.QPushButton("Undo Last"); self.btn_undo.setObjectName("Outlined")
        self.btn_settings = QtWidgets.QPushButton("Settings"); self.btn_settings.setObjectName("Outlined")

        ag.addWidget(self.btn_all,    0, 0)
        ag.addWidget(self.btn_one,    0, 1)
        ag.addWidget(self.btn_backup, 0, 2)
        ag.addWidget(self.btn_settings, 0, 3)
        ag.addWidget(self.btn_reset,  1, 0)
        ag.addWidget(self.btn_restore_file, 1, 1)
        ag.addWidget(self.btn_restore, 1, 2)
        ag.addWidget(self.btn_undo, 1, 3)
        root.addWidget(actions_group)

        # ---- Section: Progress ----
        prog_header = QtWidgets.QLabel("Progress"); prog_header.setObjectName("SectionTitle")
        root.addWidget(prog_header)
        prog_group = QtWidgets.QGroupBox(); prog_group.setObjectName("Card"); prog_group.setTitle("")
        pg = QtWidgets.QGridLayout(prog_group)
        pg.setContentsMargins(16, 16, 16, 16)
        self.progress = QtWidgets.QProgressBar(); self.progress.setRange(0, 100); self.progress.setValue(0)
        pg.addWidget(self.progress, 0, 0, 1, 1)
        root.addWidget(prog_group)

        # ---- Section: Status ----
        status_header = QtWidgets.QLabel("Status"); status_header.setObjectName("SectionTitle")
        root.addWidget(status_header)
        status_group = QtWidgets.QGroupBox(); status_group.setObjectName("Card"); status_group.setTitle("")
        sg = QtWidgets.QGridLayout(status_group)
        sg.setContentsMargins(16, 16, 16, 16)
        self.status = QtWidgets.QPlainTextEdit(); self.status.setReadOnly(True); self.status.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        mono = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont); mono.setPointSize(10)
        self.status.setFont(mono)
        self._status_max_lines = 1000  # Maximum lines to keep in status log
        sg.addWidget(self.status, 0, 0, 1, 1)

        # --- Status buttons row ---
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(6)

        self.btn_cancel = QtWidgets.QPushButton("Cancel"); self.btn_cancel.setObjectName("Text")
        self.btn_clear = QtWidgets.QPushButton("Clear Status"); self.btn_clear.setObjectName("Text")

        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_clear)

        sg.addLayout(btn_row, 1, 0, 1, 1)
  
        root.addWidget(status_group, 1)

        # Footer
        foot = QtWidgets.QHBoxLayout(); root.addLayout(foot)
        foot.addStretch(1)
        pyver = ".".join(map(str, sys.version_info[:3]))
        foot.addWidget(QtWidgets.QLabel(f"{APP_TITLE} • Python {pyver}"))

        # Shadows for cards
        for g in (actions_group, prog_group, status_group):
            self._add_shadow(g)

        # Wiring
        self.btn_clear.clicked.connect(lambda: self.status.setPlainText(""))
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_one.clicked.connect(self.open_search)
        self.btn_all.clicked.connect(lambda: self.run_flag("--all"))
        self.btn_reset.clicked.connect(self._confirm_reset)
        self.btn_backup.clicked.connect(lambda: self.run_flag("--backup"))
        self.btn_restore.clicked.connect(lambda: self.run_flag("--restore"))
        self.btn_restore_file.clicked.connect(self._restore_from_file)
        self.btn_undo.clicked.connect(self._undo_last_operation)
        self.btn_cancel.clicked.connect(self.cancel_current_operation)

        # Timer to update percent label
        self._percent_timer = QtCore.QTimer(self)
        self._percent_timer.timeout.connect(self._update_percent)
        self._percent_timer.start(120)

        self._current_worker = None

        self._apply_styles()
        self._apply_webhook_state()

        # Setup system tray
        self._setup_system_tray()

        # Scheduler timer - checks every minute if it's time to run
        self._scheduler_timer = QtCore.QTimer(self)
        self._scheduler_timer.timeout.connect(self._check_scheduler)
        self._scheduler_timer.start(60000)  # Check every minute
        QtCore.QTimer.singleShot(5000, self._check_scheduler)  # Initial check after 5 seconds

    def cancel_current_operation(self):
        """Cancel the currently running background process."""
        if self._current_worker and self._current_worker.proc.state() == QtCore.QProcess.Running:
            self._current_worker.proc.kill()
            self.append_status("Operation cancelled by user.")
            self._current_worker = None
            self.progress.setRange(0, 100)
            self.set_progress(0)
            self._set_buttons_enabled(True)
        else:
            self.append_status("No active operation to cancel.")

    def _confirm_reset(self):
        """Show confirmation dialog before resetting all movies."""
        reply = QtWidgets.QMessageBox.warning(
            self,
            "Confirm Reset",
            "This will remove ALL edition tags from your movies.\n\n"
            "This action cannot be undone unless you have a backup.\n\n"
            "Are you sure you want to continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.run_flag("--reset")

    def open_search(self):
        dlg = SearchDialog(self._cfg_server_base(), self._cfg_token(), self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            rk = dlg.chosen_rating_key()
            if rk:
                # run the CLI for exactly one movie
                self.run_flag(f"--one-id={rk}")

    def _reload_config(self):
        """Reload config from file. Call this before reading config values."""
        if os.path.exists(CONFIG_FILE):
            self.cfg.read(CONFIG_FILE, encoding="utf-8")

    def _cfg_server_base(self):
        self._reload_config()
        return self.cfg.get("server", "address", fallback="").strip().rstrip("/")

    def _cfg_token(self):
        self._reload_config()
        return self.cfg.get("server", "token", fallback="").strip()

    def _plex_headers(self):
        return {"X-Plex-Token": self._cfg_token(), "Accept": "application/json"}

    # ---- Scheduler helpers ----
    def _scheduler_enabled_in_cfg(self) -> bool:
        self._reload_config()
        return self.cfg.get("scheduler", "enabled", fallback="no").lower() in ("1", "true", "yes", "on")

    def _scheduler_cron(self) -> str:
        self._reload_config()
        return self.cfg.get("scheduler", "cron", fallback="0 3 * * *")

    def _scheduler_last_run(self) -> str:
        self._reload_config()
        return self.cfg.get("scheduler", "last_run", fallback="")

    def _scheduler_update_last_run(self):
        """Update the last_run timestamp in config."""
        self._reload_config()
        if not self.cfg.has_section("scheduler"):
            self.cfg.add_section("scheduler")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cfg.set("scheduler", "last_run", timestamp)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            self.cfg.write(f)

    def _parse_cron_field(self, field: str, min_val: int, max_val: int, current: int) -> bool:
        """Check if current value matches a cron field."""
        if field == "*":
            return True

        # Handle */n (every n)
        if field.startswith("*/"):
            try:
                step = int(field[2:])
                return current % step == 0
            except ValueError:
                return False

        # Handle ranges like 1-5
        if "-" in field and "/" not in field:
            try:
                start, end = field.split("-")
                return int(start) <= current <= int(end)
            except ValueError:
                return False

        # Handle lists like 1,3,5
        if "," in field:
            try:
                values = [int(v.strip()) for v in field.split(",")]
                return current in values
            except ValueError:
                return False

        # Handle single value
        try:
            return int(field) == current
        except ValueError:
            return False

    def _cron_matches_now(self, cron_expr: str) -> bool:
        """Check if current time matches cron expression (minute hour day month weekday)."""
        now = datetime.now()

        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return False

        minute, hour, day, month, weekday = parts

        # weekday: 0=Sunday in cron, but Python uses 0=Monday
        # Convert Python weekday (0=Mon) to cron weekday (0=Sun)
        py_weekday = now.weekday()  # 0=Monday
        cron_weekday = (py_weekday + 1) % 7  # Convert to 0=Sunday

        return (
            self._parse_cron_field(minute, 0, 59, now.minute) and
            self._parse_cron_field(hour, 0, 23, now.hour) and
            self._parse_cron_field(day, 1, 31, now.day) and
            self._parse_cron_field(month, 1, 12, now.month) and
            self._parse_cron_field(weekday, 0, 6, cron_weekday)
        )

    @QtCore.Slot()
    def _check_scheduler(self):
        """Check if scheduled processing should run based on cron expression."""
        if not self._scheduler_enabled_in_cfg():
            return

        # Don't start if already processing
        if self._current_worker is not None:
            return

        cron_expr = self._scheduler_cron()

        # Check if current time matches cron expression
        if not self._cron_matches_now(cron_expr):
            return

        # Check if we already ran this minute (to avoid multiple runs)
        last_run_str = self._scheduler_last_run()
        if last_run_str:
            try:
                last_run = datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                # If last run was within the same minute, skip
                if (last_run.year == now.year and
                    last_run.month == now.month and
                    last_run.day == now.day and
                    last_run.hour == now.hour and
                    last_run.minute == now.minute):
                    return
            except ValueError:
                pass  # Invalid timestamp, proceed with run

        self.append_status(f"[Scheduler] Starting scheduled processing (cron: {cron_expr})...")
        self._scheduler_update_last_run()
        self.run_flag("--all")

    # ---- Styling helpers ----
    def _add_shadow(self, widget, radius=18, opacity=0.20, offset=(0, 4)):
        eff = QtWidgets.QGraphicsDropShadowEffect(widget)
        eff.setBlurRadius(radius)
        eff.setColor(QtGui.QColor(0, 0, 0, int(255 * opacity)))
        eff.setOffset(*offset)
        widget.setGraphicsEffect(eff)

    def _apply_styles(self):
        if getattr(self, "dark_mode", False):
            self._apply_dark_styles()
        else:
            self._apply_light_styles()

    def _apply_light_styles(self):
        c = self.primary_color
        def darken(hex_color, factor=0.15):
            col = QtGui.QColor(hex_color)
            r, g, b = col.red(), col.green(), col.blue()
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        hover = darken(c, 0.12)
        disabled = darken(c, 0.40)

        self.setStyleSheet(self.styleSheet() + f"""
            QLabel#AppTitle {{ font-size: 20pt; font-weight: 700; letter-spacing: .2px; color: #FFFFFF; }}
            QLabel#AppVersion {{ color: rgba(255,255,255,.95); font-size: 10pt; }}
            QLabel#SectionHeaderBig {{ font-size: 16pt; font-weight: 700; margin: 2px 0 10px 2px; color: rgba(0,0,0,.84); }}
            QLabel#SectionTitle {{ margin-top: 8px; margin-bottom: 6px; font-size: 12pt; font-weight: 600; color: rgba(0,0,0,.60); }}

            QFrame#AppBar {{ background: {c}; border-radius: 10px; }}

            QGroupBox#Card {{ background: #FFFFFF; border: 1px solid #E5E5EC; border-radius: 12px; padding: 6px; margin-top: 0px; }}

            QPushButton {{ padding: 8px 14px; border-radius: 8px; font-weight: 600; }}
            QPushButton#Primary {{ background: {c}; color: #FFFFFF; border: none; }}
            QPushButton#Primary:hover {{ background: {hover}; }}
            QPushButton#Primary:disabled {{ background: {disabled}; color: #FFFFFF; }}

            QPushButton#Outlined {{ background: #FFFFFF; color: #1D1B20; border: 1px solid #CAC4D0; }}
            QPushButton#Outlined:hover {{ background: #F4EFF7; }}

            QPushButton#Text {{ background: transparent; color: {c}; border: none; padding: 6px 10px; }}
            QPushButton#Text:hover {{ background: #EEE6F7; border-radius: 6px; }}

            QProgressBar {{ border: 1px solid #E5E5EC; border-radius: 8px; background: #F4F4F8; height: 14px; color: rgba(0,0,0,.65); text-align: center; }}
            QProgressBar::chunk {{ background-color: {c}; border-radius: 8px; }}

            QPlainTextEdit {{ background: #FAFAFD; border: 1px solid #E5E5EC; border-radius: 8px; padding: 8px; color: rgba(0,0,0,.84); }}

            QTabWidget::pane {{ border: 1px solid #E5E5EC; border-radius: 10px; padding: 6px; background: #FFFFFF; }}
            QTabBar::tab {{ padding: 8px 14px; margin: 2px; border-radius: 8px; background: #F6F2FB; color: #3A3650; border: 1px solid transparent; font-weight: 600; }}
            QTabBar::tab:selected {{ background: #FFFFFF; border-color: #CAC4D0; }}
        """)

    def _apply_dark_styles(self):
        c = self.primary_color
        def lighten(hex_color, factor=0.15):
            col = QtGui.QColor(hex_color)
            r, g, b = col.red(), col.green(), col.blue()
            r = min(255, int(r * (1 + factor)))
            g = min(255, int(g * (1 + factor)))
            b = min(255, int(b * (1 + factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        hover    = lighten(c, 0.12)
        disabled = lighten(c, 0.40)

        self.setStyleSheet(self.styleSheet() + f"""
            QLabel#AppTitle {{ font-size: 20pt; font-weight: 700; letter-spacing: .2px; color: #FFFFFF; }}
            QLabel#AppVersion {{ color: rgba(255,255,255,.85); font-size: 10pt; }}
            QLabel#SectionHeaderBig {{ font-size: 16pt; font-weight: 700; margin: 2px 0 10px 2px; color: rgba(255,255,255,.95); }}
            QLabel#SectionTitle {{ margin-top: 8px; margin-bottom: 6px; font-size: 12pt; font-weight: 600; color: rgba(255,255,255,.75); }}

            QFrame#AppBar {{ background: {c}; border-radius: 10px; }}

            QGroupBox#Card {{ background: #1E1E1E; border: 1px solid #2A2A2A; border-radius: 12px; padding: 6px; margin-top: 0px; }}

            QPushButton {{ padding: 8px 14px; border-radius: 8px; font-weight: 600; }}
            QPushButton#Primary {{ background: {c}; color: #FFFFFF; border: none; }}
            QPushButton#Primary:hover {{ background: {hover}; }}
            QPushButton#Primary:disabled {{ background: {disabled}; color: #FFFFFF; }}

            QPushButton#Outlined {{ background: transparent; color: #FFFFFF; border: 1px solid #3A3A3A; }}
            QPushButton#Outlined:hover {{ background: #252525; }}

            QPushButton#Text {{ background: transparent; color: {c}; border: none; padding: 6px 10px; }}
            QPushButton#Text:hover {{ background: #222222; border-radius: 6px; }}

            QProgressBar {{ border: 1px solid #2A2A2A; border-radius: 8px; background: #1A1A1A; height: 14px; color: rgba(255,255,255,.85); text-align: center; }}
            QProgressBar::chunk {{ background-color: {c}; border-radius: 8px; }}

            QPlainTextEdit {{ background: #151515; border: 1px solid #2A2A2A; border-radius: 8px; padding: 8px; color: rgba(255,255,255,.95); }}

            QTabWidget::pane {{ border: 1px solid #2A2A2A; border-radius: 10px; padding: 6px; background: #1E1E1E; }}
            QTabBar::tab {{ padding: 8px 14px; margin: 2px; border-radius: 8px; background: #222222; color: #FFFFFF; border: 1px solid transparent; font-weight: 600; }}
            QTabBar::tab:selected {{ background: #1E1E1E; border-color: #3A3A3A; }}
        """)

    # --- Settings ---
    def open_settings(self):
        dlg = SettingsDialog(self)
        result = dlg.exec()  # run ONCE

        if result == QtWidgets.QDialog.Accepted:
            # Re-read saved settings and apply
            self.cfg.read(CONFIG_FILE, encoding="utf-8")
            self.primary_color = self.cfg.get("appearance", "primary_color", fallback=self.primary_color)
            self.dark_mode     = self.cfg.getboolean("appearance", "dark_mode", fallback=self.dark_mode)

            app = QtWidgets.QApplication.instance()
            if app is not None:
                if self.dark_mode:
                    apply_dark_palette(app, self.primary_color)
                else:
                    apply_light_palette(app, self.primary_color)

            self._apply_styles()
            self._apply_webhook_state()

    # --- Process execution ---
    def run_flag(self, flag: str):
        if self._current_worker is not None:
            return
        self._set_buttons_enabled(False)

        self._current_worker = ProcessWorker(flag)
        self._current_worker.line.connect(self.append_status)
        self._current_worker.progress.connect(self.set_progress)
        self._current_worker.started.connect(self._on_started)
        self._current_worker.finished.connect(self._on_finished)

        QtCore.QTimer.singleShot(0, self._current_worker.start)

    @QtCore.Slot()
    def _on_started(self):
        self.progress.setRange(0, 0)

    @QtCore.Slot(int)
    def _on_finished(self, code: int):
        self._current_worker = None
        self._set_buttons_enabled(True)
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        if code == 0:
            self.set_progress(100)
            self.append_status("Completed successfully.")
        else:
            self.append_status(f"Exited with code {code}.")

    @QtCore.Slot(int)
    def set_progress(self, value: int):
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        value = max(0, min(100, value))
        self.progress.setValue(value)

    def _update_percent(self):
        if self.progress.maximum() == 0:
            self.progress.setFormat("…")
        else:
            self.progress.setFormat(f"{self.progress.value()}%")

    @QtCore.Slot(str)
    def append_status(self, text: str):
        self.status.appendPlainText(text)
        # Prune old lines if exceeding max limit to prevent memory leak
        doc = self.status.document()
        if doc.blockCount() > self._status_max_lines:
            cursor = QtGui.QTextCursor(doc)
            cursor.movePosition(QtGui.QTextCursor.Start)
            # Remove oldest lines (keep removing until under limit)
            lines_to_remove = doc.blockCount() - self._status_max_lines
            for _ in range(lines_to_remove):
                cursor.select(QtGui.QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # Remove the newline
        self.status.verticalScrollBar().setValue(self.status.verticalScrollBar().maximum())

    def _set_buttons_enabled(self, enabled: bool):
        for b in (self.btn_one, self.btn_all, self.btn_reset, self.btn_backup, self.btn_restore, self.btn_restore_file, self.btn_undo, self.btn_settings):
            b.setEnabled(enabled)

    def _webhook_cmd(self):
        return [sys.executable, str(Path(__file__).parent / "webhook_server.py")]

    def _webhook_enabled_in_cfg(self) -> bool:
        self._reload_config()
        return self.cfg.get("webhook", "enabled", fallback="no").lower() in ("1", "true", "yes", "on")

    def _apply_webhook_state(self):
        if self._webhook_enabled_in_cfg():
            self._start_webhook()
        else:
            self._stop_webhook()

    def _init_webhook_log_filter(self):
        if getattr(self, "_webhook_filter_ready", False):
            return

        # Patterns to ignore in the GUI
        self._webhook_drop_patterns = [
            re.compile(r"^INFO:edition_manager:", re.IGNORECASE),
            re.compile(r"\bProcessing ratingKey=", re.IGNORECASE),
            re.compile(r"^PROGRESS\b", re.IGNORECASE),
        ]

        self._webhook_connected_pat = re.compile(r"Successfully connected to server:", re.IGNORECASE)
        self._webhook_seen_connected = False  # once-only flag

        self._webhook_recent = deque(maxlen=100)

        self._webhook_filter_ready = True

    def _should_show_webhook_line(self, line: str) -> bool:
        s = line.strip()
        if not s:
            return False
        for pat in self._webhook_drop_patterns:
            if pat.search(s):
                return False

        if s in self._webhook_recent:
            return False
        self._webhook_recent.append(s)
        return True

    def _start_webhook(self):
        if not self._webhook_enabled_in_cfg():
            return
        if self._webhook_proc and self._webhook_proc.state() != QtCore.QProcess.NotRunning:
            return

        self.append_status("Starting webhook server…")

        self._webhook_proc = QtCore.QProcess(self)
        self._webhook_proc.setWorkingDirectory(str(Path(__file__).parent))
        self._webhook_proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)

        if sys.platform.startswith("win"):
            def _no_console(args):
                args["creationFlags"] = 0x08000000
            try:
                self._webhook_proc.setCreateProcessArgumentsModifier(_no_console)
            except Exception:
                pass

        self._webhook_proc.readyReadStandardOutput.connect(self._on_webhook_output)
        self._webhook_proc.finished.connect(self._on_webhook_finished)

        cmd = self._webhook_cmd()
        self._webhook_proc.start(cmd[0], cmd[1:])

    @QtCore.Slot()
    def _on_webhook_output(self):
        self._init_webhook_log_filter()

        if not self._webhook_proc:
            return

        data = self._webhook_proc.readAllStandardOutput().data().decode(errors="replace")
        for raw in data.splitlines():
            line = raw.rstrip("\r\n")

            if self._should_show_webhook_line(line):
                self.append_status(f"[webhook] {line}")

    def _restore_from_file(self):
        start_dir = str((Path(__file__).parent / "metadata_backup").resolve())
        dlg = QtWidgets.QFileDialog(self, "Choose Edition Manager backup")
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dlg.setNameFilters(["JSON Backups (*.json)", "All Files (*)"])
        dlg.setDirectory(start_dir)

        if dlg.exec() == QtWidgets.QDialog.Accepted:
            paths = dlg.selectedFiles()
            if paths:
                path = paths[0]
                # call CLI with explicit file path
                self.run_flag(f"--restore-file={path}")

    def _undo_last_operation(self):
        """Undo the last operation by restoring from the undo snapshot."""
        undo_snapshot = Path(__file__).parent / "metadata_backup" / ".undo_snapshot.json"

        if not undo_snapshot.exists():
            QtWidgets.QMessageBox.warning(
                self,
                "No Undo Available",
                "No undo snapshot available.\n\n"
                "An undo snapshot is created automatically before\n"
                "each 'Process All' or 'Reset All' operation."
            )
            return

        # Get timestamp from the snapshot file
        try:
            import json
            with open(undo_snapshot, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
            created_at = snapshot_data.get('created_at', 'Unknown time')
            movie_count = len(snapshot_data.get('data', {}))
        except Exception:
            created_at = 'Unknown time'
            movie_count = 0

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Undo",
            f"Undo the last operation?\n\n"
            f"Snapshot created: {created_at}\n"
            f"Movies to restore: {movie_count}\n\n"
            f"This will revert all edition titles to their state\n"
            f"before the last 'Process All' or 'Reset All' operation.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.append_status("Restoring from undo snapshot...")
            self.run_flag("--undo")

    # ---- System Tray ----
    def _setup_system_tray(self):
        """Setup system tray icon and menu."""
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            return

        self._tray_icon = QtWidgets.QSystemTrayIcon(self)

        # Set icon
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            self._tray_icon.setIcon(QtGui.QIcon(str(icon_path)))
        else:
            self._tray_icon.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

        self._tray_icon.setToolTip(APP_TITLE)

        # Create tray menu
        tray_menu = QtWidgets.QMenu()

        action_show = tray_menu.addAction("Show Window")
        action_show.triggered.connect(self._tray_show_window)

        tray_menu.addSeparator()

        action_process = tray_menu.addAction("Process All Movies")
        action_process.triggered.connect(lambda: self.run_flag("--all"))

        action_backup = tray_menu.addAction("Backup Editions")
        action_backup.triggered.connect(lambda: self.run_flag("--backup"))

        tray_menu.addSeparator()

        action_quit = tray_menu.addAction("Quit")
        action_quit.triggered.connect(self._tray_quit)

        self._tray_icon.setContextMenu(tray_menu)

        # Double-click to show window
        self._tray_icon.activated.connect(self._tray_activated)

        self._tray_icon.show()

    @QtCore.Slot(QtWidgets.QSystemTrayIcon.ActivationReason)
    def _tray_activated(self, reason):
        """Handle tray icon activation (double-click)."""
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self._tray_show_window()

    def _tray_show_window(self):
        """Show and raise the main window."""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _tray_quit(self):
        """Quit the application from tray."""
        self._force_quit = True
        self.close()

    @QtCore.Slot(int, QtCore.QProcess.ExitStatus)
    def _on_webhook_finished(self, code: int, _status):
        self.append_status(f"Webhook server stopped (exit={code}).")

    def _stop_webhook(self):
        if self._webhook_proc and self._webhook_proc.state() != QtCore.QProcess.NotRunning:
            self._webhook_proc.terminate()
            if not self._webhook_proc.waitForFinished(2000):
                self._webhook_proc.kill()
                self._webhook_proc.waitForFinished(2000)
        self._webhook_proc = None

    def changeEvent(self, event: QtCore.QEvent):
        """Handle window state changes (minimize to tray)."""
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.windowState() & QtCore.Qt.WindowMinimized:
                if self._tray_icon and self._tray_icon.isVisible():
                    # Minimize to tray
                    QtCore.QTimer.singleShot(0, self.hide)
                    self._tray_icon.showMessage(
                        APP_TITLE,
                        "Minimized to system tray. Scheduler continues running.",
                        QtWidgets.QSystemTrayIcon.Information,
                        2000
                    )
        super().changeEvent(event)

    def closeEvent(self, e: QtGui.QCloseEvent):
        """Handle window close - ask user whether to quit or minimize to tray."""
        # If force quit from tray menu, actually quit
        if getattr(self, '_force_quit', False):
            try:
                self._stop_webhook()
                if self._tray_icon:
                    self._tray_icon.hide()
            finally:
                e.accept()
                QtWidgets.QApplication.quit()
            return

        # If tray is available, ask the user what they want to do
        if self._tray_icon and self._tray_icon.isVisible():
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Close Application")
            msg_box.setText("What would you like to do?")
            msg_box.setInformativeText("The scheduler and webhook will continue running if minimized to tray.")
            msg_box.setIcon(QtWidgets.QMessageBox.Question)

            btn_minimize = msg_box.addButton("Minimize to Tray", QtWidgets.QMessageBox.ActionRole)
            btn_quit = msg_box.addButton("Quit", QtWidgets.QMessageBox.DestructiveRole)
            btn_cancel = msg_box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)

            msg_box.setDefaultButton(btn_minimize)

            msg_box.exec()

            clicked = msg_box.clickedButton()
            if clicked == btn_minimize:
                e.ignore()
                self.hide()
                self._tray_icon.showMessage(
                    APP_TITLE,
                    "Application minimized to system tray.\n"
                    "Scheduler and webhook continue running.\n"
                    "Right-click tray icon to quit.",
                    QtWidgets.QSystemTrayIcon.Information,
                    3000
                )
            elif clicked == btn_quit:
                try:
                    self._stop_webhook()
                    if self._tray_icon:
                        self._tray_icon.hide()
                finally:
                    e.accept()
                    QtWidgets.QApplication.quit()
            else:
                # Cancel - don't close
                e.ignore()
        else:
            # No tray, actually close
            try:
                self._stop_webhook()
            finally:
                e.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)

    f = app.font(); f.setPointSize(f.pointSize() + 1); app.setFont(f)

    cfg = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        cfg.read(CONFIG_FILE, encoding="utf-8")
    primary_color = cfg.get("appearance", "primary_color", fallback="#6750A4")

    apply_light_palette(app, primary_color)

    dark_mode = cfg.getboolean("appearance", "dark_mode", fallback=False)
    if dark_mode:
        apply_dark_palette(app, primary_color)
    else:
        apply_light_palette(app, primary_color)

    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()