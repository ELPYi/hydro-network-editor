"""Dialog for editing per-subbasin rainfall time series (hyetograph)."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox,
    QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)

from app.canvas.items.subbasin_item import SubBasinItem

TIME_UNITS = ["Hours", "Days", "Minutes"]


class RainfallDialog(QDialog):
    def __init__(self, item: SubBasinItem, parent=None):
        super().__init__(parent)
        self._item = item
        self.setWindowTitle(f"Rainfall – {item.label}")
        self.setMinimumSize(400, 450)
        self._build_ui()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Time unit row
        unit_row = QHBoxLayout()
        unit_row.addWidget(QLabel("Time step unit:"))
        self._unit_combo = QComboBox()
        self._unit_combo.addItems(TIME_UNITS)
        unit_row.addWidget(self._unit_combo)
        unit_row.addStretch()
        layout.addLayout(unit_row)

        # Table buttons
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        remove_btn = QPushButton("Remove Row")
        add_btn.clicked.connect(self._add_row)
        remove_btn.clicked.connect(self._remove_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Table
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Time Step", "Rainfall (mm)"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self._table)

        # Paste shortcut (Ctrl+V)
        paste_sc = QShortcut(QKeySequence("Ctrl+V"), self._table)
        paste_sc.activated.connect(self._paste_from_clipboard)

        # OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self):
        # Set unit combo
        unit = self._item.rainfall_time_unit.capitalize()
        idx = self._unit_combo.findText(unit, Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            self._unit_combo.setCurrentIndex(idx)

        # Fill table rows
        for row_data in self._item.rainfall_data:
            self._append_row(row_data.get("time", 0.0), row_data.get("rainfall_mm", 0.0))

    def _append_row(self, time_val=0.0, rain_val=0.0):
        row = self._table.rowCount()
        self._table.insertRow(row)
        t_item = QTableWidgetItem(f"{time_val:g}")
        t_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        r_item = QTableWidgetItem(f"{rain_val:g}")
        r_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(row, 0, t_item)
        self._table.setItem(row, 1, r_item)

    def _add_row(self):
        self._append_row()

    def _remove_row(self):
        rows = sorted(set(idx.row() for idx in self._table.selectedIndexes()), reverse=True)
        if not rows:
            # Remove last row if nothing selected
            if self._table.rowCount() > 0:
                self._table.removeRow(self._table.rowCount() - 1)
        else:
            for row in rows:
                self._table.removeRow(row)

    def _paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        lines = text.strip().split("\n")
        current_row = self._table.currentRow()
        current_col = self._table.currentColumn()
        if current_row < 0:
            current_row = 0
        if current_col < 0:
            current_col = 0

        for r, line in enumerate(lines):
            cells = line.split("\t")
            target_row = current_row + r
            # Auto-extend table
            while target_row >= self._table.rowCount():
                self._table.insertRow(self._table.rowCount())
            for c, value in enumerate(cells):
                target_col = current_col + c
                if target_col < self._table.columnCount():
                    value = value.strip()
                    item = self._table.item(target_row, target_col)
                    if item is None:
                        item = QTableWidgetItem()
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        self._table.setItem(target_row, target_col, item)
                    item.setText(value)

    def _apply(self):
        data = []
        for row in range(self._table.rowCount()):
            t_item = self._table.item(row, 0)
            r_item = self._table.item(row, 1)
            try:
                t = float(t_item.text()) if t_item else 0.0
                r = float(r_item.text()) if r_item else 0.0
                data.append({"time": t, "rainfall_mm": r})
            except ValueError:
                pass  # Skip unparseable rows silently

        self._item.rainfall_data = data
        self._item.rainfall_time_unit = self._unit_combo.currentText().lower()
        self.accept()
