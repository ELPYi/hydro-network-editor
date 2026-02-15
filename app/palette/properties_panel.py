"""Side panel that displays properties of the currently selected element."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDoubleSpinBox, QFormLayout, QGroupBox, QLabel, QLineEdit,
    QScrollArea, QVBoxLayout, QWidget,
)

from app.canvas.items.subbasin_item import SubBasinItem, DEFAULT_PARAMETERS
from app.canvas.items.node_item import NodeItem
from app.canvas.items.reach_item import ReachItem
from app.canvas.items.diversion_item import DiversionItem
from app.canvas.items.connection_line import ConnectionLine

BASIN_CHAR_KEYS = ["AREA", "IMP", "LAG", "INFIL"]
SURFACE_STORE_KEYS = ["SS", "FS", "RC", "RS", "RR", "RK", "RX", "RDEL"]
GROUNDWATER_KEYS = ["FC", "DCS", "DCT", "A", "GSU", "GSP", "GDEL"]

PARAM_DESCRIPTIONS = {
    "AREA": "Area (km\u00b2)",
    "IMP": "Imperviousness (%)",
    "LAG": "Lag time (hours)",
    "INFIL": "Infiltration rate (mm/h)",
    "SS": "Surface store capacity (mm)",
    "FS": "Evaporation scaling factor",
    "RC": "Runoff coefficient",
    "RS": "Recession constant for surface",
    "RR": "Rainfall excess threshold",
    "RK": "Routing storage coefficient",
    "RX": "Routing storage exponent",
    "RDEL": "Runoff delay (time steps)",
    "FC": "Field capacity fraction",
    "DCS": "Dry condition store (mm)",
    "DCT": "Drain capacity threshold (mm)",
    "A": "Groundwater percolation fraction",
    "GSU": "Groundwater store upper limit (mm)",
    "GSP": "Groundwater store power",
    "GDEL": "Groundwater delay (time steps)",
}

PARAM_LABELS = {
    "AREA": "Area (km\u00b2):",
    "IMP": "Imperviousness (%):",
    "LAG": "Lag time (hrs):",
    "INFIL": "Infiltration (mm/h):",
}


class PropertiesPanel(QWidget):
    """Dockable panel showing properties of the selected scene element."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item = None
        self._spin_boxes: dict[str, QDoubleSpinBox] = {}

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        self._show_empty()

    # -------------------------------------------------------------- #
    #  Public API                                                      #
    # -------------------------------------------------------------- #
    def update_selection(self, selected_items: list):
        """Called when scene selection changes."""
        # Commit edits from previous item before switching
        self._commit()

        # Pick the first relevant item
        item = None
        for i in selected_items:
            if isinstance(i, (SubBasinItem, NodeItem, ReachItem, DiversionItem, ConnectionLine)):
                item = i
                break

        if item is None:
            self._current_item = None
            self._show_empty()
        elif item is not self._current_item:
            self._current_item = item
            self._build_panel(item)

    # -------------------------------------------------------------- #
    #  Panel builders                                                  #
    # -------------------------------------------------------------- #
    def _show_empty(self):
        self._spin_boxes.clear()
        w = QWidget()
        layout = QVBoxLayout(w)
        label = QLabel("No element selected")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
        layout.addWidget(label)
        layout.addStretch()
        self._scroll.setWidget(w)

    def _build_panel(self, item):
        self._spin_boxes.clear()
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        if isinstance(item, SubBasinItem):
            self._build_subbasin_panel(layout, item)
        elif isinstance(item, NodeItem):
            self._build_node_panel(layout, item)
        elif isinstance(item, ReachItem):
            self._build_reach_panel(layout, item)
        elif isinstance(item, DiversionItem):
            self._build_diversion_panel(layout, item)
        elif isinstance(item, ConnectionLine):
            self._build_connection_panel(layout, item)

        layout.addStretch()
        self._scroll.setWidget(w)

    def _build_subbasin_panel(self, layout: QVBoxLayout, item: SubBasinItem):
        # Header
        layout.addWidget(self._header("Sub-basin"))

        # Info group
        info = QGroupBox("Info")
        form = QFormLayout(info)
        form.addRow("ID:", QLabel(item.item_id))
        form.addRow("Label:", QLabel(item.label))
        pos = item.pos()
        form.addRow("Position:", QLabel(f"({pos.x():.1f}, {pos.y():.1f})"))
        layout.addWidget(info)

        # Basin characteristics
        basin = QGroupBox("Basin Characteristics")
        form_b = QFormLayout(basin)
        for key in BASIN_CHAR_KEYS:
            spin = self._make_spin(item.parameters.get(key, 0.0), key)
            self._spin_boxes[key] = spin
            form_b.addRow(PARAM_LABELS.get(key, f"{key}:"), spin)
        layout.addWidget(basin)

        # Surface / Runoff parameters
        surface = QGroupBox("Surface / Runoff Store")
        form_s = QFormLayout(surface)
        for key in SURFACE_STORE_KEYS:
            spin = self._make_spin(item.parameters.get(key, 0.0), key)
            self._spin_boxes[key] = spin
            form_s.addRow(f"{key}:", spin)
        layout.addWidget(surface)

        # Groundwater parameters
        gw = QGroupBox("Groundwater Store")
        form_g = QFormLayout(gw)
        for key in GROUNDWATER_KEYS:
            spin = self._make_spin(item.parameters.get(key, 0.0), key)
            self._spin_boxes[key] = spin
            form_g.addRow(f"{key}:", spin)
        layout.addWidget(gw)

    def _build_node_panel(self, layout: QVBoxLayout, item: NodeItem):
        layout.addWidget(self._header("Node"))
        info = QGroupBox("Info")
        form = QFormLayout(info)
        form.addRow("ID:", QLabel(item.item_id))
        form.addRow("Label:", QLabel(item.label))
        pos = item.pos()
        form.addRow("Position:", QLabel(f"({pos.x():.1f}, {pos.y():.1f})"))
        form.addRow("Reaches:", QLabel(str(len(item.edges))))
        form.addRow("Diversions:", QLabel(str(len(item.diversions))))
        form.addRow("Connections:", QLabel(str(len(item.connections))))
        layout.addWidget(info)

    def _build_reach_panel(self, layout: QVBoxLayout, item: ReachItem):
        layout.addWidget(self._header("Reach"))
        info = QGroupBox("Info")
        form = QFormLayout(info)
        form.addRow("ID:", QLabel(item.item_id))
        form.addRow("Label:", QLabel(item.label))
        form.addRow("From:", QLabel(f"{item.source_item.label} ({item.source_item.item_id})"))
        form.addRow("To:", QLabel(f"{item.dest_item.label} ({item.dest_item.item_id})"))
        layout.addWidget(info)

    def _build_diversion_panel(self, layout: QVBoxLayout, item: DiversionItem):
        layout.addWidget(self._header("Diversion"))
        info = QGroupBox("Info")
        form = QFormLayout(info)
        form.addRow("ID:", QLabel(item.item_id))
        form.addRow("Label:", QLabel(item.label))
        form.addRow("From:", QLabel(f"{item.source_item.label} ({item.source_item.item_id})"))
        form.addRow("To:", QLabel(f"{item.dest_item.label} ({item.dest_item.item_id})"))
        layout.addWidget(info)

    def _build_connection_panel(self, layout: QVBoxLayout, item: ConnectionLine):
        layout.addWidget(self._header("Connection"))
        info = QGroupBox("Info")
        form = QFormLayout(info)
        form.addRow("ID:", QLabel(item.item_id))
        form.addRow("From:", QLabel(f"{item.source_item.label} ({item.source_item.item_id})"))
        form.addRow("To:", QLabel(f"{item.dest_item.label} ({item.dest_item.item_id})"))
        layout.addWidget(info)

    # -------------------------------------------------------------- #
    #  Helpers                                                         #
    # -------------------------------------------------------------- #
    def _header(self, type_name: str) -> QLabel:
        label = QLabel(type_name)
        label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 4px 0;"
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _make_spin(self, value: float, key: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setDecimals(4)
        spin.setRange(-1e9, 1e9)
        spin.setValue(value)
        spin.setToolTip(PARAM_DESCRIPTIONS.get(key, ""))
        return spin

    def _commit(self):
        """Write spin box values back to the current sub-basin item."""
        if isinstance(self._current_item, SubBasinItem) and self._spin_boxes:
            for key, spin in self._spin_boxes.items():
                self._current_item.parameters[key] = spin.value()
