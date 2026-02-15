"""Dialog for editing sub-basin rainfall-runoff parameters."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QVBoxLayout,
)

BASIN_CHAR_PARAMS = [
    ("AREA", "Area (km\u00b2)"),
    ("IMP", "Imperviousness (%)"),
    ("LAG", "Lag time (hours)"),
    ("INFIL", "Infiltration rate (mm/h)"),
]

SURFACE_STORE_PARAMS = [
    ("SS", "Surface store capacity (mm)"),
    ("FS", "Evaporation scaling factor"),
    ("RC", "Runoff coefficient"),
    ("RS", "Recession constant for surface"),
    ("RR", "Rainfall excess threshold"),
    ("RK", "Routing storage coefficient"),
    ("RX", "Routing storage exponent"),
    ("RDEL", "Runoff delay (time steps)"),
]

GROUNDWATER_PARAMS = [
    ("FC", "Field capacity fraction"),
    ("DCS", "Dry condition store (mm)"),
    ("DCT", "Drain capacity threshold (mm)"),
    ("A", "Groundwater percolation fraction"),
    ("GSU", "Groundwater store upper limit (mm)"),
    ("GSP", "Groundwater store power"),
    ("GDEL", "Groundwater delay (time steps)"),
]


class SubBasinParamsDialog(QDialog):
    def __init__(self, subbasin_item, parent=None):
        super().__init__(parent)
        self._item = subbasin_item
        self._spin_boxes: dict[str, QDoubleSpinBox] = {}

        self.setWindowTitle(f"Parameters - {subbasin_item.label}")
        self.setMinimumWidth(560)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Basin characteristics on top
        layout.addWidget(
            self._make_group("Basin Characteristics", BASIN_CHAR_PARAMS)
        )

        # Two model groups side by side
        h_layout = QHBoxLayout()

        h_layout.addWidget(
            self._make_group("Surface / Runoff Store", SURFACE_STORE_PARAMS)
        )
        h_layout.addWidget(
            self._make_group("Groundwater Store", GROUNDWATER_PARAMS)
        )

        layout.addLayout(h_layout)

        # OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _make_group(self, title: str, params: list[tuple[str, str]]) -> QGroupBox:
        group = QGroupBox(title)
        form = QFormLayout(group)

        for key, description in params:
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(-1e9, 1e9)
            spin.setValue(self._item.parameters.get(key, 0.0))
            spin.setToolTip(description)
            spin.setMinimumWidth(100)
            self._spin_boxes[key] = spin
            form.addRow(f"{key}:", spin)

        return group

    def _apply(self):
        for key, spin in self._spin_boxes.items():
            self._item.parameters[key] = spin.value()
        self.accept()
