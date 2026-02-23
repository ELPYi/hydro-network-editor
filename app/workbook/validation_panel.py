"""Per-subbasin rainfall vs runoff validation panel."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_COL_SUBBASIN = 0
_COL_RAIN = 1
_COL_RUNOFF = 2
_COL_STATUS = 3
_HEADERS = ["Subbasin", "Annual Rain (mm)", "Annual Runoff (mm)", "Status"]

_COLOR_OK = QColor("#C8E6C9")      # light green
_COLOR_VIOLATION = QColor("#FFCDD2")  # light red
_COLOR_NO_DATA = QColor("#E0E0E0")   # grey


class ValidationPanel(QWidget):
    """Shows a QTableWidget with green/red/grey rows per-subbasin."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(QLabel("Rainfall / Runoff Validation"))

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_rows(self, rows: list[dict]) -> None:
        """
        Populate the table.

        Each dict in *rows* must have:
          - ``subbasin``: str
          - ``annual_rain_mm``: float
          - ``annual_runoff_mm``: float | None  (None = no runoff data)
        """
        self._table.setRowCount(0)
        for row in rows:
            r = self._table.rowCount()
            self._table.insertRow(r)

            label = row.get("subbasin", "")
            rain = row.get("annual_rain_mm", 0.0)
            runoff = row.get("annual_runoff_mm", None)

            if runoff is None:
                status = "No runoff data"
                color = _COLOR_NO_DATA
            elif runoff > rain:
                status = "VIOLATION"
                color = _COLOR_VIOLATION
            else:
                status = "OK"
                color = _COLOR_OK

            runoff_str = f"{runoff:.1f}" if runoff is not None else "—"

            self._set_cell(r, _COL_SUBBASIN, label, color)
            self._set_cell(r, _COL_RAIN, f"{rain:.1f}", color, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._set_cell(r, _COL_RUNOFF, runoff_str, color, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._set_cell(r, _COL_STATUS, status, color, Qt.AlignmentFlag.AlignCenter)

    def clear(self) -> None:
        self._table.setRowCount(0)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _set_cell(
        self,
        row: int,
        col: int,
        text: str,
        bg: QColor,
        alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
    ) -> None:
        item = QTableWidgetItem(text)
        item.setBackground(bg)
        item.setTextAlignment(alignment)
        self._table.setItem(row, col, item)
