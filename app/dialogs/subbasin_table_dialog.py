"""Table dialog for bulk sub-basin parameter editing with Excel paste support."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QDialogButtonBox, QHeaderView,
    QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from app.canvas.items.subbasin_item import SubBasinItem

# Row order matching the spreadsheet layout
PARAM_ROWS = [
    ("AREA", "Area"),
    ("IMP", "Imperv"),
    ("LAG", "Lg"),
    ("INFIL", "Infil"),
    ("SS", "SS"),
    ("FS", "FS"),
    ("RC", "RC"),
    ("RS", "RS"),
    ("RR", "RR"),
    ("RK", "RK"),
    ("RX", "RX"),
    ("FC", "FC"),
    ("DCS", "DCS"),
    ("DCT", "DCT"),
    ("A", "A"),
    ("GSU", "GSU"),
    ("GSP", "GSP"),
    ("GDEL", "GDEL"),
    ("RDEL", "RDEL"),
]


class SubBasinTableDialog(QDialog):
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self._scene = scene
        self._subbasins: list[SubBasinItem] = []
        self._collect_subbasins()

        self.setWindowTitle("Sub-basin Parameters Table")
        self.setMinimumSize(800, 550)
        self._build_ui()
        self._populate()

    def _collect_subbasins(self):
        for item in self._scene.items():
            if isinstance(item, SubBasinItem):
                self._subbasins.append(item)
        # Sort by label for consistent column order
        self._subbasins.sort(key=lambda sb: sb.label)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self._table = QTableWidget()
        self._table.setRowCount(len(PARAM_ROWS))
        self._table.setColumnCount(len(self._subbasins))

        # Row headers = parameter names
        self._table.setVerticalHeaderLabels([display for _, display in PARAM_ROWS])

        # Column headers = sub-basin labels
        self._table.setHorizontalHeaderLabels([sb.label for sb in self._subbasins])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        layout.addWidget(self._table)

        # Keyboard shortcuts
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self._table)
        paste_shortcut.activated.connect(self._paste_from_clipboard)

        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self._table)
        copy_shortcut.activated.connect(self._copy_to_clipboard)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self):
        for row, (key, _) in enumerate(PARAM_ROWS):
            for col, sb in enumerate(self._subbasins):
                value = sb.parameters.get(key, 0.0)
                item = QTableWidgetItem(f"{value:g}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._table.setItem(row, col, item)

    def _paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        # Parse tab/newline separated data from Excel
        lines = text.strip().split("\n")
        current_row = self._table.currentRow()
        current_col = self._table.currentColumn()
        if current_row < 0:
            current_row = 0
        if current_col < 0:
            current_col = 0

        for r, line in enumerate(lines):
            cells = line.split("\t")
            for c, value in enumerate(cells):
                target_row = current_row + r
                target_col = current_col + c
                if target_row < self._table.rowCount() and target_col < self._table.columnCount():
                    value = value.strip()
                    item = self._table.item(target_row, target_col)
                    if item is None:
                        item = QTableWidgetItem()
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        self._table.setItem(target_row, target_col, item)
                    item.setText(value)

    def _copy_to_clipboard(self):
        selection = self._table.selectedRanges()
        if not selection:
            return

        # Build tab-separated text from selection
        sel = selection[0]
        lines = []
        for row in range(sel.topRow(), sel.bottomRow() + 1):
            cells = []
            for col in range(sel.leftColumn(), sel.rightColumn() + 1):
                item = self._table.item(row, col)
                cells.append(item.text() if item else "")
            lines.append("\t".join(cells))
        text = "\n".join(lines)

        QApplication.clipboard().setText(text)

    def _apply(self):
        for row, (key, _) in enumerate(PARAM_ROWS):
            for col, sb in enumerate(self._subbasins):
                item = self._table.item(row, col)
                if item:
                    try:
                        sb.parameters[key] = float(item.text())
                    except ValueError:
                        QMessageBox.warning(
                            self, "Invalid Value",
                            f"Cannot parse '{item.text()}' for {key} in {sb.label}. Skipped."
                        )
        self.accept()
