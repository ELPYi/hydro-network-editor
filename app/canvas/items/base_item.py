"""Abstract base class for Sub-basin and Node graphics items."""
from __future__ import annotations
from abc import abstractmethod

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsSceneMouseEvent, QMenu, QStyleOptionGraphicsItem,
    QWidget,
)


class BaseNetworkItem(QGraphicsItem):
    """Movable, selectable network element with a label and context menu."""

    def __init__(self, item_id: str, label: str, parent=None):
        super().__init__(parent)
        self._item_id = item_id
        self._label = label

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

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

    @abstractmethod
    def update_connections(self):
        """Update all attached edges/connections when position changes."""

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.update_connections()
        return super().itemChange(change, value)

    def _draw_selection_highlight(self, painter, shape_rect: QRectF):
        if self.isSelected():
            pen = QPen(QColor("#DAA520"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(shape_rect.adjusted(-3, -3, 3, 3))

    def contextMenuEvent(self, event: QGraphicsSceneMouseEvent):
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
