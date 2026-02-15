"""Sub-basin graphics item: green 40x40 square."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget

from app.canvas.items.base_item import BaseNetworkItem

SIZE = 40


DEFAULT_PARAMETERS = {
    # Basin characteristics
    "AREA": 0.0,
    "IMP": 0.0,
    "LAG": 0.0,
    "INFIL": 0.0,
    # Surface / Runoff store
    "SS": 3.0,
    "FS": 0.4,
    "RC": 0.3,
    "RS": 0.0,
    "RR": 0.0,
    "RK": 0.3,
    "RX": 1.2,
    "RDEL": 0.0,
    # Groundwater store
    "FC": 0.8,
    "DCS": 300.0,
    "DCT": 360.0,
    "A": 0.3,
    "GSU": 300.0,
    "GSP": 2.0,
    "GDEL": 0.0,
}


class SubBasinItem(BaseNetworkItem):
    def __init__(self, item_id: str, label: str, parent=None):
        super().__init__(item_id, label, parent)
        self._connections: list = []  # ConnectionLine objects
        self._parameters: dict[str, float] = dict(DEFAULT_PARAMETERS)
        self.setZValue(1)

    @property
    def parameters(self) -> dict[str, float]:
        return self._parameters

    @parameters.setter
    def parameters(self, value: dict[str, float]):
        self._parameters = value

    @property
    def connections(self) -> list:
        return self._connections

    def add_connection(self, conn):
        self._connections.append(conn)

    def remove_connection(self, conn):
        if conn in self._connections:
            self._connections.remove(conn)

    def update_connections(self):
        for conn in self._connections:
            conn.adjust()

    def center_scene_pos(self):
        return self.pos() + QRectF(0, 0, SIZE, SIZE).center()

    def boundingRect(self) -> QRectF:
        return QRectF(-5, -5, SIZE + 10, SIZE + 25)

    def shape(self):
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRect(QRectF(0, 0, SIZE, SIZE))
        return path

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        rect = QRectF(0, 0, SIZE, SIZE)

        # Green fill
        painter.setPen(QPen(QColor("#2E7D32"), 1.5))
        painter.setBrush(QBrush(QColor("#66BB6A")))
        painter.drawRect(rect)

        # Label below
        painter.setPen(Qt.GlobalColor.black)
        font = QFont("Arial", 9)
        font.setBold(True)
        painter.setFont(font)
        label_rect = QRectF(0, SIZE + 2, SIZE, 16)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._label)

        self._draw_selection_highlight(painter, rect)
