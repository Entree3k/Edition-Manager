"""Search dialog: find a movie in Plex and pick it for single processing.

Search and poster downloads run on background threads so the UI never freezes.
"""

from __future__ import annotations

import threading

from PySide6 import QtCore, QtGui, QtWidgets

from ..plex import PlexClient
from ..logutil import mask_sensitive
from . import theme


class _SearchSignals(QtCore.QObject):
    results = QtCore.Signal(int, list)
    error = QtCore.Signal(int, str)
    thumb = QtCore.Signal(int, int, bytes)


class SearchDialog(QtWidgets.QDialog):
    def __init__(self, plex: PlexClient, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find a Movie")
        self.resize(820, 660)
        self.setMinimumSize(600, 500)
        self._plex = plex
        self._chosen_rating_key = None
        self._search_generation = 0  # invalidates stale background results
        self.finished.connect(self._invalidate_search)

        self._signals = _SearchSignals()
        self._signals.results.connect(self._show_results)
        self._signals.error.connect(self._show_error)
        self._signals.thumb.connect(self._set_thumb)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)
        title = QtWidgets.QLabel("Find a movie")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        hint = QtWidgets.QLabel("Search your Plex libraries and apply your edition rules to one title.")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        row = QtWidgets.QHBoxLayout()
        layout.addLayout(row)
        self.edit = QtWidgets.QLineEdit()
        self.edit.setPlaceholderText("Type a movie title…")
        self.edit.setClearButtonEnabled(True)
        self.btn_search = QtWidgets.QPushButton("Search")
        self.btn_search.setObjectName("Primary")
        row.addWidget(self.edit, 1)
        row.addWidget(self.btn_search)
        self.btn_search.clicked.connect(self.search_now)
        self.edit.returnPressed.connect(self.search_now)

        self.status_label = QtWidgets.QLabel("Enter a title to search your library.")
        self.status_label.setTextFormat(QtCore.Qt.PlainText)
        self.status_label.setObjectName("Hint")
        layout.addWidget(self.status_label)

        self.listw = QtWidgets.QListWidget()
        self.listw.setViewMode(QtWidgets.QListView.IconMode)
        self.listw.setIconSize(QtCore.QSize(120, 180))
        self.listw.setGridSize(QtCore.QSize(168, 252))
        self.listw.setResizeMode(QtWidgets.QListView.Adjust)
        self.listw.setMovement(QtWidgets.QListView.Static)
        self.listw.setSpacing(12)
        self.listw.setWordWrap(True)
        self.listw.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.listw, 1)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.btn_process = buttons.button(QtWidgets.QDialogButtonBox.Ok)
        self.btn_process.setText("Process Selected")
        self.btn_process.setObjectName("Primary")
        self.btn_process.setEnabled(False)
        self.listw.itemSelectionChanged.connect(
            lambda: self.btn_process.setEnabled(bool(self.listw.selectedItems())))
        self.btn_search.setDefault(True)
        self.btn_process.setAutoDefault(False)
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.edit.setFocus()

    def _invalidate_search(self, _result) -> None:
        self._search_generation += 1

    def chosen_rating_key(self):
        return self._chosen_rating_key

    # ---- search -------------------------------------------------------------

    def search_now(self) -> None:
        query = self.edit.text().strip()
        if not query:
            return
        self._search_generation += 1
        generation = self._search_generation
        self.listw.clear()
        self.status_label.setText("Searching…")
        self.btn_search.setEnabled(False)

        def _work():
            try:
                results = self._plex.search_movies(query)
            except Exception as err:
                if generation == self._search_generation:
                    self._signals.error.emit(generation, mask_sensitive(str(err)))
                return
            if generation == self._search_generation:
                self._signals.results.emit(generation, results)

        threading.Thread(target=_work, daemon=True).start()

    @QtCore.Slot(int, list)
    def _show_results(self, generation: int, results: list) -> None:
        if generation != self._search_generation:
            return
        self.btn_search.setEnabled(True)
        if not results:
            self.status_label.setText("No movies found. Try a shorter title or check your library in Plex.")
            return
        self.status_label.setText(f"{len(results)} movies found · Select a title, then choose Process Selected.")

        generation = self._search_generation
        placeholder = self._poster_placeholder()
        for row, movie in enumerate(results):
            label = f"{movie.get('title', 'Unknown')} ({movie.get('year', '')})\n{movie.get('library', '')}"
            item = QtWidgets.QListWidgetItem(placeholder, label)
            item.setData(QtCore.Qt.UserRole, movie.get("ratingKey"))
            item.setSizeHint(QtCore.QSize(156, 240))
            item.setToolTip(label)
            self.listw.addItem(item)
            if movie.get("thumb"):
                self._fetch_thumb(generation, row, movie["thumb"])

    def _poster_placeholder(self) -> QtGui.QIcon:
        pixmap = QtGui.QPixmap(120, 180)
        pixmap.fill(QtGui.QColor(theme.current.hover))
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QColor(theme.current.subtext))
        painter.setFont(QtGui.QFont(self.font().family(), 10))
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, "PLEX\nNo poster")
        painter.end()
        return QtGui.QIcon(pixmap)

    def _fetch_thumb(self, generation: int, row: int, thumb_path: str) -> None:
        def _work():
            try:
                data = self._plex.image_bytes(thumb_path)
            except Exception:
                return
            if generation == self._search_generation:
                self._signals.thumb.emit(generation, row, data)

        threading.Thread(target=_work, daemon=True).start()

    @QtCore.Slot(int, int, bytes)
    def _set_thumb(self, generation: int, row: int, data: bytes) -> None:
        if generation != self._search_generation:
            return
        item = self.listw.item(row)
        if item is None:
            return
        pixmap = QtGui.QPixmap()
        if pixmap.loadFromData(data):
            item.setIcon(QtGui.QIcon(pixmap))

    @QtCore.Slot(int, str)
    def _show_error(self, generation: int, message: str) -> None:
        if generation != self._search_generation:
            return
        self.btn_search.setEnabled(True)
        self.status_label.setText("Search failed.")
        QtWidgets.QMessageBox.warning(self, "Error", f"Could not search Plex:\n{message}")

    def accept_selection(self) -> None:
        item = self.listw.currentItem()
        if not item:
            return
        self._chosen_rating_key = item.data(QtCore.Qt.UserRole)
        if self._chosen_rating_key:
            self.accept()
