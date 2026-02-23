"""WorkbookWindow — QMainWindow composing tree, table, chart and validation."""
from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTableView,
    QToolBar,
    QTreeView,
)

from app.workbook.chart_widget import ChartWidget
from app.workbook.dataset_tree_model import DatasetTreeModel
from app.workbook.hdf5_store import HDF5Store, store_for_json
from app.workbook.table_model import WorkbookTableModel
from app.workbook.validation_panel import ValidationPanel


class WorkbookWindow(QMainWindow):
    """Data workbook: tree browser, table view, chart, and validation panel."""

    def __init__(self, model, scene, parent=None):
        super().__init__(parent)
        self._model = model
        self._scene = scene
        self._store: HDF5Store | None = None
        self._chart_mode: str = "line"   # "line" | "bar"
        self._current_hdf5_path: str | None = None  # full HDF5 path of selected leaf

        self.setWindowTitle("Hydro Workbook")
        self.setMinimumSize(900, 600)

        self._build_ui()

    # ------------------------------------------------------------------
    # Public API (called by MainWindow)
    # ------------------------------------------------------------------

    def set_project_file(self, json_path: str | None) -> None:
        """Switch to the HDF5 file that corresponds to *json_path*."""
        if json_path is None:
            self._store = None
            self._tree_model.clear()
            self._table_model.clear()
            self._chart.clear()
            self._validation.clear()
            self.setWindowTitle("Hydro Workbook — (no project)")
            return

        self._store = store_for_json(json_path)
        stem = Path(json_path).stem
        self.setWindowTitle(f"Hydro Workbook — {stem}")

        # Initialise the HDF5 file if it does not yet exist
        self._store.open(project_name=stem)

    # ------------------------------------------------------------------
    # Qt events
    # ------------------------------------------------------------------

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._sync_from_model()
        self._refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ---- Toolbar ----
        tb = QToolBar("Workbook Tools")
        tb.setMovable(False)
        self.addToolBar(tb)

        self._act_refresh = tb.addAction("Refresh", self._on_refresh)
        self._act_refresh.setShortcut(QKeySequence("F5"))

        tb.addSeparator()
        self._act_import = tb.addAction("Import CSV", self._import_csv)
        self._act_export = tb.addAction("Export CSV", self._export_csv)
        tb.addSeparator()
        self._act_line = tb.addAction("Line", self._set_line_mode)
        self._act_bar = tb.addAction("Bar", self._set_bar_mode)

        # ---- Tree (left dock) ----
        self._tree_model = DatasetTreeModel()
        self._tree_view = QTreeView()
        self._tree_view.setModel(self._tree_model)
        self._tree_view.setHeaderHidden(False)
        self._tree_view.selectionModel().currentChanged.connect(self._on_tree_selection)

        tree_dock = QDockWidget("Datasets", self)
        tree_dock.setWidget(self._tree_view)
        tree_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        tree_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, tree_dock)

        # ---- Central: table (top) + chart (bottom) via splitter ----
        self._table_model = WorkbookTableModel()
        self._table_view = QTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.horizontalHeader().setStretchLastSection(True)

        self._chart = ChartWidget()

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._table_view)
        splitter.addWidget(self._chart)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        # ---- Validation (bottom dock) ----
        self._validation = ValidationPanel()
        val_dock = QDockWidget("Validation", self)
        val_dock.setWidget(self._validation)
        val_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )
        val_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, val_dock)

    # ------------------------------------------------------------------
    # Sync & refresh
    # ------------------------------------------------------------------

    def _sync_from_model(self) -> None:
        """Read SubBasinItem rainfall from the scene and write to HDF5."""
        if self._store is None:
            return
        from app.canvas.items.subbasin_item import SubBasinItem
        for item in self._scene.items():
            if not isinstance(item, SubBasinItem):
                continue
            data = item.rainfall_data
            if not data:
                continue
            times = np.array([d["time"] for d in data], dtype=np.float64)
            values = np.array([d["rainfall_mm"] for d in data], dtype=np.float64)
            area = float(item.parameters.get("AREA", 0.0))
            self._store.write_rainfall(
                subbasin_label=item.label,
                subbasin_id=item.item_id,
                times=times,
                values=values,
                time_unit=item.rainfall_time_unit,
                area_km2=area,
            )

    def _refresh(self) -> None:
        """Re-populate tree and validation from HDF5."""
        if self._store is None:
            return
        self._tree_model.populate_from_store(self._store)
        self._tree_view.expandAll()
        self._update_validation()

    def _update_validation(self) -> None:
        if self._store is None:
            return
        rows = []
        tree = self._store.list_tree()
        rainfall_groups = tree.get("inputs", {}).get("rainfall", {})
        for label, subtree in rainfall_groups.items():
            if not isinstance(subtree, dict):
                continue
            hdf5_path = f"inputs/rainfall/{label}"
            mat, cols = self._store.read_dataset(hdf5_path)
            annual_rain = 0.0
            if mat.size > 0 and "rainfall_mm" in cols:
                idx = cols.index("rainfall_mm")
                annual_rain = float(mat[:, idx].sum())
            rows.append({
                "subbasin": label,
                "annual_rain_mm": annual_rain,
                "annual_runoff_mm": None,  # no runoff computed yet
            })
        self._validation.update_rows(rows)

    # ------------------------------------------------------------------
    # Tree selection
    # ------------------------------------------------------------------

    def _on_tree_selection(self, current, _previous) -> None:
        hdf5_path = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(hdf5_path, str) or self._store is None:
            return
        self._current_hdf5_path = hdf5_path
        mat, cols = self._store.read_dataset(hdf5_path)
        self._table_model.set_data(mat, cols)
        self._plot(mat, cols, hdf5_path)

    def _plot(self, mat: np.ndarray, cols: list[str], title: str) -> None:
        if mat.size == 0 or mat.shape[1] < 2:
            self._chart.clear()
            return
        x = mat[:, 0]
        y = mat[:, 1]
        x_label = cols[0] if cols else "x"
        y_label = cols[1] if len(cols) > 1 else "y"
        if self._chart_mode == "bar":
            self._chart.plot_bar(x, y, x_label=x_label, y_label=y_label, title=title)
        else:
            self._chart.plot_line(x, y, x_label=x_label, y_label=y_label, title=title)

    # ------------------------------------------------------------------
    # Toolbar actions
    # ------------------------------------------------------------------

    def _on_refresh(self) -> None:
        self._sync_from_model()
        self._refresh()

    def _set_line_mode(self) -> None:
        self._chart_mode = "line"
        if self._current_hdf5_path and self._store:
            mat, cols = self._store.read_dataset(self._current_hdf5_path)
            self._plot(mat, cols, self._current_hdf5_path)

    def _set_bar_mode(self) -> None:
        self._chart_mode = "bar"
        if self._current_hdf5_path and self._store:
            mat, cols = self._store.read_dataset(self._current_hdf5_path)
            self._plot(mat, cols, self._current_hdf5_path)

    def _export_csv(self) -> None:
        if self._current_hdf5_path is None or self._store is None:
            QMessageBox.information(self, "Export CSV", "Select a dataset in the tree first.")
            return
        mat, cols = self._store.read_dataset(self._current_hdf5_path)
        if mat.size == 0:
            QMessageBox.information(self, "Export CSV", "Selected dataset is empty.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                for row in mat:
                    writer.writerow([f"{v:.6g}" for v in row])
        except OSError as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _import_csv(self) -> None:
        """Import CSV into the currently selected leaf dataset (rainfall groups only)."""
        if self._current_hdf5_path is None or self._store is None:
            QMessageBox.information(self, "Import CSV", "Select a rainfall dataset in the tree first.")
            return

        # Only allow import into inputs/rainfall/<label> groups
        parts = self._current_hdf5_path.split("/")
        # path might be inputs/rainfall/B1/time — find the subbasin group
        if len(parts) < 3 or parts[0] != "inputs" or parts[1] != "rainfall":
            QMessageBox.information(self, "Import CSV", "CSV import is only supported for rainfall datasets.")
            return
        subbasin_label = parts[2]

        path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        rows: list[tuple[float, float]] = []
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                sample = f.read(4096)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
                has_header = csv.Sniffer().has_header(sample)
                reader = csv.reader(f, dialect)
                if has_header:
                    next(reader, None)
                for lineno, row in enumerate(reader, start=2 if has_header else 1):
                    if not row or all(c.strip() == "" for c in row):
                        continue
                    if len(row) < 2:
                        raise ValueError(f"Line {lineno}: expected ≥2 columns, got {len(row)}.")
                    rows.append((float(row[0].strip()), float(row[1].strip())))
        except (OSError, csv.Error, ValueError) as exc:
            QMessageBox.warning(self, "Import Error", str(exc))
            return

        if not rows:
            QMessageBox.information(self, "Import CSV", "No data rows found.")
            return

        times = np.array([r[0] for r in rows], dtype=np.float64)
        values = np.array([r[1] for r in rows], dtype=np.float64)

        # Preserve existing attrs if possible
        try:
            import h5py
            with h5py.File(self._store.path, "r") as h5:
                grp_path = f"inputs/rainfall/{subbasin_label}"
                attrs = dict(h5[grp_path].attrs) if grp_path in h5 else {}
        except Exception:
            attrs = {}

        self._store.write_rainfall(
            subbasin_label=subbasin_label,
            subbasin_id=attrs.get("subbasin_id", subbasin_label),
            times=times,
            values=values,
            time_unit=attrs.get("time_unit", "hours"),
            area_km2=float(attrs.get("area_km2", 0.0)),
        )
        self._refresh()
        # Re-select the same path
        mat, cols = self._store.read_dataset(f"inputs/rainfall/{subbasin_label}")
        self._table_model.set_data(mat, cols)
        self._plot(mat, cols, f"inputs/rainfall/{subbasin_label}")
        self._current_hdf5_path = f"inputs/rainfall/{subbasin_label}"
