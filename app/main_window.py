"""Main application window."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QFileDialog, QMessageBox, QToolBar,
)

from app.canvas.network_scene import NetworkScene
from app.canvas.network_view import NetworkView
from app.model.network_model import NetworkModel
from app.model.serializer import Serializer
from app.palette.element_palette import ElementPalette
from app.dialogs.subbasin_table_dialog import SubBasinTableDialog
from app.palette.properties_panel import PropertiesPanel
from app.workbook.workbook_window import WorkbookWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_file: str | None = None
        self._model = NetworkModel()
        self._workbook: WorkbookWindow | None = None

        self._init_ui()
        self._update_title()

    def _init_ui(self):
        self.setMinimumSize(900, 600)

        # Scene & View
        self._scene = NetworkScene(self._model, parent=self)
        self._scene.element_counts_changed.connect(self._update_status)
        self._view = NetworkView(self._scene)
        self._view.zoom_changed.connect(self._update_status)
        self.setCentralWidget(self._view)

        # Palette dock
        self._palette = ElementPalette()
        self._palette.connection_mode_changed.connect(
            self._scene.set_connection_mode
        )
        self._palette.connection_mode_changed.connect(
            self._view.set_drawing_mode
        )
        self._palette.diversion_mode_changed.connect(
            self._scene.set_diversion_mode
        )
        self._palette.diversion_mode_changed.connect(
            self._view.set_drawing_mode
        )
        dock = QDockWidget("Elements", self)
        dock.setWidget(self._palette)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        # Properties panel dock (right side)
        self._props_panel = PropertiesPanel()
        props_dock = QDockWidget("Properties", self)
        props_dock.setWidget(self._props_panel)
        props_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        props_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, props_dock)

        # Wire selection changes to properties panel
        self._scene.selectionChanged.connect(self._on_selection_changed)

        self._build_menus()
        self._build_toolbar()

        # Status bar
        self.statusBar().showMessage("Ready")

    def _build_menus(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")
        self._add_action(file_menu, "&New", self._new_file, QKeySequence.StandardKey.New)
        self._add_action(file_menu, "&Open...", self._open_file, QKeySequence.StandardKey.Open)
        file_menu.addSeparator()
        self._add_action(file_menu, "&Save", self._save_file, QKeySequence.StandardKey.Save)
        self._add_action(file_menu, "Save &As...", self._save_file_as, QKeySequence("Ctrl+Shift+S"))
        file_menu.addSeparator()
        self._add_action(file_menu, "E&xit", self.close, QKeySequence("Alt+F4"))

        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        self._add_action(edit_menu, "&Delete", self._delete_selected, QKeySequence.StandardKey.Delete)
        self._add_action(edit_menu, "Select &All", self._select_all, QKeySequence.StandardKey.SelectAll)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Sub-basin &Table...", self._open_subbasin_table, QKeySequence("Ctrl+T"))

        # Workbook menu
        workbook_menu = menu_bar.addMenu("&Workbook")
        self._add_action(workbook_menu, "&Open Workbook", self._open_workbook, QKeySequence("Ctrl+W"))

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        self._add_action(help_menu, "&Help Contents", self._show_help, QKeySequence.StandardKey.HelpContents)

    def _build_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        tb.addAction("New", self._new_file)
        tb.addAction("Open", self._open_file)
        tb.addAction("Save", self._save_file)
        tb.addSeparator()
        tb.addAction("Delete", self._delete_selected)
        tb.addSeparator()
        tb.addAction("Basin Table", self._open_subbasin_table)

    def _add_action(self, menu, text, slot, shortcut=None):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    # --- File operations ---
    def _new_file(self):
        if not self._confirm_discard():
            return
        self._scene.clear_all()
        self._model.reset()
        self._current_file = None
        self._update_title()
        if self._workbook is not None:
            self._workbook.set_project_file(self._current_file)

    def _open_file(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Network", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        self._open_file_path(path)

    def _open_file_path(self, path: str):
        try:
            Serializer.load(path, self._model, self._scene)
            self._current_file = path
            self._update_title()
            if self._workbook is not None:
                self._workbook.set_project_file(self._current_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def _save_file(self):
        if self._current_file:
            self._do_save(self._current_file)
        else:
            self._save_file_as()

    def _save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Network", "", "JSON Files (*.json);;All Files (*)"
        )
        if path:
            self._do_save(path)

    def _do_save(self, path: str):
        try:
            self._props_panel._commit()
            Serializer.save(path, self._model, self._scene)
            self._current_file = path
            self._update_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def _confirm_discard(self) -> bool:
        if not self._scene.items():
            return True
        result = QMessageBox.question(
            self, "Unsaved Changes",
            "Discard current network?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    # --- Edit operations ---
    def _delete_selected(self):
        self._scene.delete_selected()

    def _select_all(self):
        for item in self._scene.items():
            item.setSelected(True)

    def _open_subbasin_table(self):
        self._props_panel._commit()
        dlg = SubBasinTableDialog(self._scene, parent=self)
        if dlg.exec():
            # Refresh properties panel if a sub-basin is selected
            self._on_selection_changed()

    def _open_workbook(self):
        if self._workbook is None:
            self._workbook = WorkbookWindow(self._model, self._scene, parent=self)
        self._workbook.set_project_file(self._current_file)
        self._workbook.show()
        self._workbook.raise_()
        self._workbook.activateWindow()

    def _on_selection_changed(self):
        self._props_panel.update_selection(self._scene.selectedItems())

    # --- UI updates ---
    def _update_title(self):
        name = self._current_file or "Untitled"
        self.setWindowTitle(f"Hydro Network Editor - {name}")

    def _update_status(self):
        zoom = self._view.current_zoom
        counts = self._scene.get_element_counts()
        parts = [f"Zoom: {zoom:.0%}"]
        for label, count in counts.items():
            parts.append(f"{label}: {count}")
        self.statusBar().showMessage("  |  ".join(parts))

    def _show_help(self):
        QMessageBox.information(
            self,
            "Hydro Network Editor – Help",
            """<h2>Hydro Network Editor</h2>
<p>A desktop application for visually creating and editing hydrological network models.</p>

<h3>Elements</h3>
<ul>
  <li><b>Subbasin</b> – Represents a drainage area that collects and routes runoff.</li>
  <li><b>Reach</b> – A river or stream segment that conveys flow between nodes.</li>
  <li><b>Node</b> – A junction point where reaches and subbasins connect.</li>
  <li><b>Diversion</b> – A branch that diverts flow away from the main channel.</li>
  <li><b>Connection Line</b> – Links elements together to define flow paths.</li>
</ul>

<h3>Building a Network</h3>
<ol>
  <li>Drag elements from the <b>Elements palette</b> (left panel) onto the canvas.</li>
  <li>Use the <b>Connect</b> tool to draw connection lines between elements.</li>
  <li>Click any element to select it and edit its properties in the <b>Properties panel</b> (right panel).</li>
  <li>Double-click an element to open its detailed properties dialog.</li>
</ol>

<h3>Subbasin Table</h3>
<p>Use <b>Edit &gt; Sub-basin Table</b> (Ctrl+T) to view and edit all subbasin parameters in a tabular format.</p>

<h3>Saving and Loading</h3>
<p>Networks are saved as <b>JSON files</b> via <b>File &gt; Save</b> (Ctrl+S) and reopened with <b>File &gt; Open</b> (Ctrl+O).</p>

<h3>Canvas Navigation</h3>
<ul>
  <li><b>Scroll wheel</b> – Zoom in / out</li>
  <li><b>Middle-click drag</b> – Pan the canvas</li>
  <li><b>Delete key</b> – Remove selected elements</li>
  <li><b>Ctrl+A</b> – Select all elements</li>
</ul>"""
        )
