"""Node graphics item: red 20px diameter circle."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget

from app.canvas.items.base_item import BaseNetworkItem

DIAMETER = 20


class NodeItem(BaseNetworkItem):
    def __init__(self, item_id: str, label: str, parent=None):
        super().__init__(item_id, label, parent)
        self._edges: list = []       # ReachItem objects
        self._diversions: list = []  # DiversionItem objects
        self._connections: list = []  # ConnectionLine objects
        self.setZValue(1)

    @property
    def edges(self) -> list:
        return self._edges

    @property
    def diversions(self) -> list:
        return self._diversions

    @property
    def connections(self) -> list:
        return self._connections

    def add_edge(self, edge):
        self._edges.append(edge)

    def remove_edge(self, edge):
        if edge in self._edges:
            self._edges.remove(edge)

    def add_diversion(self, div):
        self._diversions.append(div)

    def remove_diversion(self, div):
        if div in self._diversions:
            self._diversions.remove(div)

    def add_connection(self, conn):
        self._connections.append(conn)

    def remove_connection(self, conn):
        if conn in self._connections:
            self._connections.remove(conn)

    def update_connections(self):
        for edge in self._edges:
            edge.adjust()
        for div in self._diversions:
            div.adjust()
        for conn in self._connections:
            conn.adjust()

    def center_scene_pos(self):
        return self.pos() + QRectF(0, 0, DIAMETER, DIAMETER).center()

    def boundingRect(self) -> QRectF:
        return QRectF(-5, -5, DIAMETER + 10, DIAMETER + 25)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(QRectF(0, 0, DIAMETER, DIAMETER))
        return path

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        rect = QRectF(0, 0, DIAMETER, DIAMETER)

        # Red fill
        painter.setPen(QPen(QColor("#B71C1C"), 1.5))
        painter.setBrush(QBrush(QColor("#EF5350")))
        painter.drawEllipse(rect)

        # Label below
        painter.setPen(Qt.GlobalColor.black)
        font = QFont("Arial", 9)
        font.setBold(True)
        painter.setFont(font)
        label_rect = QRectF(-5, DIAMETER + 2, DIAMETER + 10, 16)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._label)

        self._draw_selection_highlight(painter, rect)
