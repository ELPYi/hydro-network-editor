"""Reach graphics item: blue arrow line between two Nodes."""
from __future__ import annotations

import math

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsItem, QMenu, QStyleOptionGraphicsItem, QWidget


ARROW_SIZE = 12
NODE_RADIUS = 12  # slightly larger than visual radius to clear the node edge


class ReachItem(QGraphicsItem):
    """Blue directed line (with arrowhead) connecting two NodeItems."""

    def __init__(self, item_id: str, label: str, source_item, dest_item, parent=None):
        super().__init__(parent)
        self._item_id = item_id
        self._label = label
        self._source_item = source_item
        self._dest_item = dest_item
        self._line = QLineF()
        self._arrow_polygon = QPolygonF()

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(0)  # behind nodes
        self.adjust()

    @property
    def item_id(self) -> str:
        return self._item_id

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str):
        self._label = value
        self.update()

    @property
    def source_item(self):
        return self._source_item

    @property
    def dest_item(self):
        return self._dest_item

    def adjust(self):
        self.prepareGeometryChange()
        src_center = self._source_item.center_scene_pos()
        dst_center = self._dest_item.center_scene_pos()
        full_line = QLineF(src_center, dst_center)

        if full_line.length() < 1:
            self._line = full_line
            self._arrow_polygon = QPolygonF()
            return

        # Offset endpoints to node edges so arrow is visible
        angle = math.atan2(full_line.dy(), full_line.dx())
        src = src_center + QPointF(math.cos(angle) * NODE_RADIUS, math.sin(angle) * NODE_RADIUS)
        dst = dst_center - QPointF(math.cos(angle) * NODE_RADIUS, math.sin(angle) * NODE_RADIUS)
        self._line = QLineF(src, dst)

        # Arrowhead at destination end
        arr_angle = math.atan2(-self._line.dy(), self._line.dx())
        arrow_p1 = dst + QPointF(
            math.cos(arr_angle + math.pi + math.pi / 6) * ARROW_SIZE,
            -math.sin(arr_angle + math.pi + math.pi / 6) * ARROW_SIZE,
        )
        arrow_p2 = dst + QPointF(
            math.cos(arr_angle + math.pi - math.pi / 6) * ARROW_SIZE,
            -math.sin(arr_angle + math.pi - math.pi / 6) * ARROW_SIZE,
        )
        self._arrow_polygon = QPolygonF([dst, arrow_p1, arrow_p2])

    def boundingRect(self) -> QRectF:
        if self._line.isNull():
            return QRectF()
        extra = ARROW_SIZE + 20
        return QRectF(self._line.p1(), self._line.p2()).normalized().adjusted(
            -extra, -extra, extra, extra
        )

    def shape(self):
        path = QPainterPath()
        if self._line.isNull():
            return path
        # Wider hit area for easier selection
        stroker = QPainterPath()
        stroker.moveTo(self._line.p1())
        stroker.lineTo(self._line.p2())
        from PyQt6.QtGui import QPainterPathStroker
        ps = QPainterPathStroker()
        ps.setWidth(10)
        return ps.createStroke(stroker)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        if self._line.isNull():
            return

        color = QColor("#1565C0")
        pen = QPen(color, 2)
        if self.isSelected():
            pen = QPen(QColor("#DAA520"), 2.5, Qt.PenStyle.DashLine)

        painter.setPen(pen)
        painter.drawLine(self._line)

        # Arrowhead
        painter.setBrush(QBrush(color if not self.isSelected() else QColor("#DAA520")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(self._arrow_polygon)

        # Label at midpoint
        if self._label:
            mid = self._line.center()
            painter.setPen(Qt.GlobalColor.black)
            font = QFont("Arial", 8)
            font.setBold(True)
            painter.setFont(font)
            label_rect = QRectF(mid.x() - 20, mid.y() - 20, 40, 16)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self._label)

    def contextMenuEvent(self, event):
        menu = QMenu()
        rename_action = menu.addAction("Rename")
        props_action = menu.addAction("Properties")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec(event.screenPos())
        if action == rename_action:
            self.scene().rename_element(self)
        elif action == props_action:
            self.scene().show_properties(self)
        elif action == delete_action:
            self.scene().remove_element(self)
