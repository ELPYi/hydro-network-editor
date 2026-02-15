"""Connection line: gray-green line from Sub-basin to Node (no label)."""
from __future__ import annotations

from PyQt6.QtCore import QLineF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsItem, QMenu, QStyleOptionGraphicsItem, QWidget


class ConnectionLine(QGraphicsItem):
    """Gray-green line connecting a SubBasinItem to a NodeItem."""

    def __init__(self, item_id: str, source_item, dest_item, parent=None):
        super().__init__(parent)
        self._item_id = item_id
        self._label = ""
        self._source_item = source_item
        self._dest_item = dest_item
        self._line = QLineF()

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(-1)  # behind everything
        self.adjust()

    @property
    def item_id(self) -> str:
        return self._item_id

    @property
    def label(self) -> str:
        return self._label

    @property
    def source_item(self):
        return self._source_item

    @property
    def dest_item(self):
        return self._dest_item

    def adjust(self):
        self.prepareGeometryChange()
        src = self._source_item.center_scene_pos()
        dst = self._dest_item.center_scene_pos()
        self._line = QLineF(src, dst)

    def boundingRect(self) -> QRectF:
        if self._line.isNull():
            return QRectF()
        extra = 10
        return QRectF(self._line.p1(), self._line.p2()).normalized().adjusted(
            -extra, -extra, extra, extra
        )

    def shape(self):
        path = QPainterPath()
        if self._line.isNull():
            return path
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

        if self.isSelected():
            pen = QPen(QColor("#DAA520"), 2, Qt.PenStyle.DashLine)
        else:
            pen = QPen(QColor("#6B8E6B"), 2)

        painter.setPen(pen)
        painter.drawLine(self._line)

    def contextMenuEvent(self, event):
        menu = QMenu()
        props_action = menu.addAction("Properties")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec(event.screenPos())
        if action == props_action:
            self.scene().show_properties(self)
        elif action == delete_action:
            self.scene().remove_element(self)
