"""QAbstractTableModel wrapping a NumPy 2-D array."""
from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
import numpy as np


class WorkbookTableModel(QAbstractTableModel):
    """Displays a NumPy array[N, M] in a QTableView."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: np.ndarray = np.empty((0, 0))
        self._headers: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_data(self, array: np.ndarray, headers: list[str]) -> None:
        self.beginResetModel()
        self._data = array
        self._headers = headers
        self.endResetModel()

    def clear(self) -> None:
        self.set_data(np.empty((0, 0)), [])

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return self._data.shape[0] if self._data.ndim >= 1 else 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        if self._data.ndim < 2:
            return 0
        return self._data.shape[1]

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            val = self._data[index.row(), index.column()]
            if isinstance(val, (float, np.floating)):
                return f"{val:.4f}"
            return str(val)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            val = self._data[index.row(), index.column()]
            if isinstance(val, str):
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            if section < len(self._headers):
                return self._headers[section]
            return str(section)
        return str(section + 1)
