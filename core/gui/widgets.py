"""Small shared GUI pieces: cards, toast banner, reorderable module list."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from . import theme

# Module name -> (what it detects, example value shown in the row and preview).
MODULE_INFO = {
    "AudioChannels": ("Channel layout", "7.1"),
    "AudioCodec": ("Audio format", "TrueHD Atmos"),
    "Bitrate": ("Video bitrate", "24.5 Mbps"),
    "ContentRating": ("Certification", "R"),
    "Country": ("Production country", "United States"),
    "Cut": ("Cut/edition from the filename", "Director's Cut"),
    "Director": ("Director name", "Ridley Scott"),
    "Duration": ("Runtime", "1hr 57min"),
    "DurationMinutes": ("Runtime in minutes", "117min"),
    "DynamicRange": ("HDR format", "Dolby Vision"),
    "FrameRate": ("Frame rate", "24fps"),
    "Genre": ("First genre", "Sci-Fi"),
    "Language": ("Audio language", "French"),
    "Rating": ("Online rating (Letterboxd/TMDb/RT)", "4.2/5"),
    "Release": ("Boutique label from the filename", "Criterion"),
    "Resolution": ("Video resolution", "4K"),
    "ShortFilm": ("Tags movies under 40 minutes", "Short Film"),
    "Size": ("File size", "46.6 GB"),
    "Source": ("Source type", "Remux"),
    "SpecialFeatures": ("Plex extras", "Deleted Scenes"),
    "Studio": ("Production studio", "Warner Bros."),
    "VideoCodec": ("Video codec", "H.265"),
    "Writer": ("Writer name", "Hampton Fancher"),
}


class Card(QtWidgets.QFrame):
    """Quiet bordered panel; shared by the dashboard and dialogs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")


class Toast(QtWidgets.QFrame):
    """Transient confirmation/error banner shown top-center of a window."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self._label = QtWidgets.QLabel(self)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(16, 9, 16, 9)
        layout.addWidget(self._label)
        self.hide()

    def show_message(self, message: str, ok: bool = True, msec: int = 2400) -> None:
        bg = "#1E8E3E" if ok else "#D93025"
        self.setStyleSheet(f"QFrame {{ background: {bg}; border-radius: 8px; }} QLabel {{ color: white; font-weight: 600; }}")
        self._label.setText(message)
        self.adjustSize()
        parent = self.parentWidget()
        self.move(parent.width() // 2 - self.width() // 2, 12)
        self.show()
        self.raise_()
        QtCore.QTimer.singleShot(msec, self.hide)


class TimePicker(QtWidgets.QWidget):
    """Time-of-day picker built from hour/minute/AM-PM dropdowns - friendlier
    than a segmented spinbox time edit."""

    timeChanged = QtCore.Signal()

    def __init__(self, initial: QtCore.QTime = QtCore.QTime(3, 0), parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.hour = QtWidgets.QComboBox()
        self.hour.addItems([str(h) for h in range(1, 13)])
        self.minute = QtWidgets.QComboBox()
        self.minute.addItems([f"{m:02d}" for m in range(0, 60, 5)])
        self.ampm = QtWidgets.QComboBox()
        self.ampm.addItems(["AM", "PM"])

        layout.addWidget(self.hour)
        layout.addWidget(QtWidgets.QLabel(":"))
        layout.addWidget(self.minute)
        layout.addWidget(self.ampm)
        layout.addStretch(1)

        self.setTime(initial)
        for combo in (self.hour, self.minute, self.ampm):
            combo.currentIndexChanged.connect(self.timeChanged)

    def setTime(self, t: QtCore.QTime) -> None:
        h24, minute = t.hour(), t.minute()
        self.hour.setCurrentText(str(h24 % 12 or 12))
        minute_text = f"{minute:02d}"
        if self.minute.findText(minute_text) < 0:
            # Keep odd minutes from hand-edited cron expressions selectable.
            self.minute.addItem(minute_text)
        self.minute.setCurrentText(minute_text)
        self.ampm.setCurrentIndex(0 if h24 < 12 else 1)

    def time(self) -> QtCore.QTime:
        h24 = int(self.hour.currentText()) % 12 + (12 if self.ampm.currentIndex() == 1 else 0)
        return QtCore.QTime(h24, int(self.minute.currentText()))


def _is_checked(index: QtCore.QModelIndex) -> bool:
    return index.data(Qt.CheckStateRole) in (Qt.Checked, Qt.Checked.value)


class ModuleRowDelegate(QtWidgets.QStyledItemDelegate):
    """Paints a module row: checkbox, position badge, name + description,
    example value chip, and a drag handle."""

    ROW_HEIGHT = 48
    BADGE_SIZE = 22

    def sizeHint(self, option, index):
        return QtCore.QSize(0, self.ROW_HEIGHT)

    def paint(self, painter: QtGui.QPainter, option, index) -> None:
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        name = opt.text
        opt.text = ""  # let the style draw background/selection/checkbox; we draw the rest
        widget = opt.widget
        style = widget.style() if widget else QtWidgets.QApplication.style()
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, opt, painter, widget)

        t = theme.current
        checked = _is_checked(index)
        subtext = QtGui.QColor(t.text)
        subtext.setAlphaF(0.55)

        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = opt.rect

        # Position badge: enabled modules get their 1-based order number.
        check_rect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemCheckIndicator, opt, widget)
        badge = QtCore.QRectF(
            check_rect.right() + 12,
            rect.center().y() - self.BADGE_SIZE / 2,
            self.BADGE_SIZE, self.BADGE_SIZE,
        )
        if checked:
            model = index.model()
            number = sum(
                1 for row in range(index.row() + 1)
                if _is_checked(model.index(row, 0))
            )
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(t.accent))
            painter.drawEllipse(badge)
            badge_font = QtGui.QFont(opt.font)
            badge_font.setBold(True)
            badge_font.setPointSize(max(8, opt.font.pointSize() - 1))
            painter.setFont(badge_font)
            painter.setPen(QtGui.QColor(t.on_accent))
            painter.drawText(badge, Qt.AlignCenter, str(number))
        else:
            pen = QtGui.QPen(QtGui.QColor(t.border))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(badge.adjusted(3, 3, -3, -3))

        # Drag handle at the far right.
        handle_font = QtGui.QFont(opt.font)
        handle_font.setPointSize(opt.font.pointSize() + 2)
        painter.setFont(handle_font)
        painter.setPen(subtext)
        handle_rect = QtCore.QRect(rect.right() - 30, rect.top(), 22, rect.height())
        painter.drawText(handle_rect, Qt.AlignCenter, "≡")

        # Example value chip, right-aligned before the handle.
        desc, example = MODULE_INFO.get(name, ("", ""))
        desc_font = QtGui.QFont(opt.font)
        desc_font.setPointSizeF(max(7.5, opt.font.pointSizeF() - 1.5))
        chip_left = handle_rect.left() - 8
        if example:
            metrics = QtGui.QFontMetrics(desc_font)
            chip_width = metrics.horizontalAdvance(example) + 18
            chip_left -= chip_width
            chip = QtCore.QRectF(chip_left, rect.center().y() - 11, chip_width, 22)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(t.hover))
            painter.drawRoundedRect(chip, 11, 11)
            painter.setFont(desc_font)
            painter.setPen(QtGui.QColor(t.text) if checked else subtext)
            painter.drawText(chip, Qt.AlignCenter, example)

        # Module name (top line) and description (bottom line).
        text_x = int(badge.right()) + 12
        text_width = chip_left - 10 - text_x
        name_font = QtGui.QFont(opt.font)
        name_font.setBold(True)
        painter.setFont(name_font)
        painter.setPen(QtGui.QColor(t.text) if checked else subtext)
        name_rect = QtCore.QRect(text_x, rect.top() + 6, text_width, rect.height() // 2 - 4)
        elided = QtGui.QFontMetrics(name_font).elidedText(name, Qt.ElideRight, text_width)
        painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, elided)

        painter.setFont(desc_font)
        painter.setPen(subtext)
        desc_rect = QtCore.QRect(text_x, rect.center().y() + 1, text_width, rect.height() // 2 - 6)
        elided_desc = QtGui.QFontMetrics(desc_font).elidedText(desc, Qt.ElideRight, text_width)
        painter.drawText(desc_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_desc)

        painter.restore()


class ModulesList(QtWidgets.QListWidget):
    """Checkable, drag-reorderable list of detector modules.

    Emits `changed` whenever the enabled set or order changes (check toggles,
    drag-drops, and programmatic moves), coalesced through the event loop.
    """

    changed = QtCore.Signal()

    def __init__(self, all_modules: list[str], enabled_order: list[str], parent=None):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setItemDelegate(ModuleRowDelegate(self))
        self.setUniformItemSizes(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._all_modules = all_modules
        self.set_enabled_order(enabled_order)

        self.itemChanged.connect(self._notify)
        self.model().rowsInserted.connect(self._notify)
        self.model().rowsRemoved.connect(self._notify)
        self.model().rowsMoved.connect(self._notify)

    def _notify(self, *_args) -> None:
        self.viewport().update()  # refresh position badges
        QtCore.QTimer.singleShot(0, self.changed.emit)

    def set_enabled_order(self, enabled_order: list[str]) -> None:
        """Rebuild the list: enabled modules first (in order), then the rest unchecked."""
        self.clear()
        enabled = [m for m in enabled_order if m in self._all_modules]
        disabled = [m for m in self._all_modules if m not in enabled]
        for name in enabled + disabled:
            item = QtWidgets.QListWidgetItem(name, self)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
            item.setCheckState(Qt.Checked if name in enabled else Qt.Unchecked)
            desc, example = MODULE_INFO.get(name, ("", ""))
            item.setToolTip(f"{name} - {desc} (e.g. {example})" if desc else name)

    def enabled_modules_in_order(self) -> list[str]:
        return [
            self.item(i).text() for i in range(self.count())
            if self.item(i).checkState() == Qt.Checked
        ]

    def move_current(self, delta: int) -> None:
        """Move the selected row up (-1) or down (+1)."""
        row = self.currentRow()
        new_row = row + delta
        if row < 0 or not (0 <= new_row < self.count()):
            return
        item = self.takeItem(row)
        self.insertItem(new_row, item)
        self.setCurrentRow(new_row)
