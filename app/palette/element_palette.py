"""Element palette: draggable buttons for Sub-basin and Node, plus connection/diversion mode toggles."""
from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QDrag, QPalette
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)


class DraggableElementButton(QPushButton):
    """A button that initiates a drag with MIME data identifying the element type."""

    def __init__(self, text: str, element_type: str, color: str, parent=None):
        super().__init__(text, parent)
        self._element_type = element_type
        self.setMinimumHeight(36)
        self.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: white; "
            f"font-weight: bold; border: 1px solid #555; border-radius: 4px; padding: 6px; }}"
            f"QPushButton:hover {{ border: 2px solid #333; }}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self._element_type)
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)
        else:
            super().mousePressEvent(event)


class ElementPalette(QWidget):
    """Palette widget with draggable element buttons and connection/diversion mode toggles."""

    connection_mode_changed = pyqtSignal(bool)
    diversion_mode_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Drag buttons
        layout.addWidget(DraggableElementButton("Sub-basin", "subbasin", "#43A047"))
        layout.addWidget(DraggableElementButton("Node", "node", "#E53935"))

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        # Connection mode toggle
        self._conn_btn = QPushButton("Draw Connection")
        self._conn_btn.setCheckable(True)
        self._conn_btn.setMinimumHeight(36)
        self._conn_btn.setStyleSheet(
            "QPushButton { background-color: #546E7A; color: white; font-weight: bold; "
            "border: 1px solid #555; border-radius: 4px; padding: 6px; }"
            "QPushButton:checked { background-color: #FF8F00; border: 2px solid #E65100; }"
        )
        self._conn_btn.toggled.connect(self._on_conn_toggle)
        layout.addWidget(self._conn_btn)

        # Diversion mode toggle
        self._div_btn = QPushButton("Draw Diversion")
        self._div_btn.setCheckable(True)
        self._div_btn.setMinimumHeight(36)
        self._div_btn.setStyleSheet(
            "QPushButton { background-color: #546E7A; color: white; font-weight: bold; "
            "border: 1px solid #555; border-radius: 4px; padding: 6px; }"
            "QPushButton:checked { background-color: #1565C0; border: 2px solid #0D47A1; }"
        )
        self._div_btn.toggled.connect(self._on_div_toggle)
        layout.addWidget(self._div_btn)

        layout.addStretch()

    def _on_conn_toggle(self, checked: bool):
        if checked:
            self._div_btn.blockSignals(True)
            self._div_btn.setChecked(False)
            self._div_btn.blockSignals(False)
            self.diversion_mode_changed.emit(False)
        self.connection_mode_changed.emit(checked)

    def _on_div_toggle(self, checked: bool):
        if checked:
            self._conn_btn.blockSignals(True)
            self._conn_btn.setChecked(False)
            self._conn_btn.blockSignals(False)
            self.connection_mode_changed.emit(False)
        self.diversion_mode_changed.emit(checked)
