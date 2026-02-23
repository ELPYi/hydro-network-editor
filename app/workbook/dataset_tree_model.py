"""QStandardItemModel that mirrors the HDF5 group hierarchy."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel

from app.workbook.hdf5_store import HDF5Store


class DatasetTreeModel(QStandardItemModel):
    """Wraps the nested dict returned by HDF5Store.list_tree()."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["Dataset"])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate_from_store(self, store: HDF5Store) -> None:
        """Rebuild the tree from the current HDF5 file contents."""
        self.clear()
        self.setHorizontalHeaderLabels(["Dataset"])
        tree = store.list_tree()
        self._build(self.invisibleRootItem(), tree)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build(self, parent_item: QStandardItem, node: dict) -> None:
        for key, val in sorted(node.items()):
            item = QStandardItem(key)
            item.setEditable(False)
            if isinstance(val, dict):
                # Group node — recurse
                item.setData(None, Qt.ItemDataRole.UserRole)
                parent_item.appendRow(item)
                self._build(item, val)
            else:
                # Leaf dataset — store full HDF5 path
                item.setData(val, Qt.ItemDataRole.UserRole)
                parent_item.appendRow(item)
