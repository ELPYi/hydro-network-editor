"""QGraphicsScene: drop handling, connection drawing, element management."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import (
    QGraphicsLineItem, QGraphicsScene, QGraphicsSceneDragDropEvent,
    QGraphicsSceneMouseEvent,
)

from app.canvas.items.connection_line import ConnectionLine
from app.canvas.items.diversion_item import DiversionItem
from app.canvas.items.node_item import NodeItem
from app.canvas.items.reach_item import ReachItem
from app.canvas.items.subbasin_item import SubBasinItem
from app.dialogs.properties_dialog import PropertiesDialog
from app.dialogs.rename_dialog import rename_element
from app.dialogs.subbasin_params_dialog import SubBasinParamsDialog
from app.model.network_model import NetworkModel

SCENE_SIZE = 5000


class NetworkScene(QGraphicsScene):
    element_counts_changed = pyqtSignal()

    def __init__(self, model: NetworkModel, parent=None):
        super().__init__(parent)
        self._model = model
        self._connection_mode = False
        self._diversion_mode = False
        self._temp_line: QGraphicsLineItem | None = None
        self._conn_source = None

        self.setSceneRect(-SCENE_SIZE / 2, -SCENE_SIZE / 2, SCENE_SIZE, SCENE_SIZE)

    def set_connection_mode(self, enabled: bool):
        self._connection_mode = enabled
        if enabled:
            self._diversion_mode = False
        if not enabled:
            self._cancel_temp_line()

    def set_diversion_mode(self, enabled: bool):
        self._diversion_mode = enabled
        if enabled:
            self._connection_mode = False
        if not enabled:
            self._cancel_temp_line()

    # ------------------------------------------------------------------ #
    #  Drag-and-drop from palette                                         #
    # ------------------------------------------------------------------ #
    def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QGraphicsSceneDragDropEvent):
        element_type = event.mimeData().text()
        pos = event.scenePos()
        if element_type == "subbasin":
            self.add_subbasin(pos.x(), pos.y())
        elif element_type == "node":
            self.add_node(pos.x(), pos.y())
        event.acceptProposedAction()

    # ------------------------------------------------------------------ #
    #  Element creation helpers                                           #
    # ------------------------------------------------------------------ #
    def add_subbasin(self, x: float, y: float, item_id: str = None, label: str = None) -> SubBasinItem:
        if item_id is None:
            item_id, label = self._model.create_subbasin()
        item = SubBasinItem(item_id, label)
        item.setPos(x, y)
        self.addItem(item)
        self.element_counts_changed.emit()
        return item

    def add_node(self, x: float, y: float, item_id: str = None, label: str = None) -> NodeItem:
        if item_id is None:
            item_id, label = self._model.create_node()
        item = NodeItem(item_id, label)
        item.setPos(x, y)
        self.addItem(item)
        self.element_counts_changed.emit()
        return item

    def add_reach(self, source: NodeItem, dest: NodeItem, item_id: str = None, label: str = None) -> ReachItem:
        if item_id is None:
            item_id, label = self._model.create_reach()
        reach = ReachItem(item_id, label, source, dest)
        source.add_edge(reach)
        dest.add_edge(reach)
        self.addItem(reach)
        self.element_counts_changed.emit()
        return reach

    def add_connection(self, source: SubBasinItem, dest: NodeItem, item_id: str = None) -> ConnectionLine | None:
        # Each sub-basin can only connect to one node at a time
        if item_id is None and source.connections:
            return None
        if item_id is None:
            item_id, _ = self._model.create_connection()
        conn = ConnectionLine(item_id, source, dest)
        source.add_connection(conn)
        dest.add_connection(conn)
        self.addItem(conn)
        self.element_counts_changed.emit()
        return conn

    def add_diversion(self, source: NodeItem, dest: NodeItem, item_id: str = None, label: str = None) -> DiversionItem:
        if item_id is None:
            item_id, label = self._model.create_diversion()
        div = DiversionItem(item_id, label, source, dest)
        source.add_diversion(div)
        dest.add_diversion(div)
        self.addItem(div)
        self.element_counts_changed.emit()
        return div

    # ------------------------------------------------------------------ #
    #  Connection drawing mode                                            #
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if (self._connection_mode or self._diversion_mode) and event.button() == Qt.MouseButton.LeftButton:
            item = self._item_at(event.scenePos())
            if isinstance(item, (SubBasinItem, NodeItem)):
                self._conn_source = item
                self._temp_line = QGraphicsLineItem()
                pen = QPen(QColor("#999999"), 1.5, Qt.PenStyle.DashLine)
                self._temp_line.setPen(pen)
                self._temp_line.setZValue(10)
                start = item.center_scene_pos()
                self._temp_line.setLine(start.x(), start.y(), start.x(), start.y())
                self.addItem(self._temp_line)
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self._temp_line is not None:
            line = self._temp_line.line()
            pos = event.scenePos()
            self._temp_line.setLine(line.x1(), line.y1(), pos.x(), pos.y())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._temp_line is not None and event.button() == Qt.MouseButton.LeftButton:
            target = self._item_at(event.scenePos())
            self._try_connect(self._conn_source, target)
            self._cancel_temp_line()
            return
        super().mouseReleaseEvent(event)

    def _item_at(self, pos: QPointF):
        """Return the topmost SubBasinItem or NodeItem at pos, or None."""
        for item in self.items(pos):
            if isinstance(item, (SubBasinItem, NodeItem)):
                return item
        return None

    def _try_connect(self, source, target):
        if source is None or target is None or source is target:
            return
        if self._diversion_mode:
            # Diversion mode: Node -> Node only
            if isinstance(source, NodeItem) and isinstance(target, NodeItem):
                self.add_diversion(source, target)
            return
        # SubBasin -> Node = ConnectionLine
        if isinstance(source, SubBasinItem) and isinstance(target, NodeItem):
            self.add_connection(source, target)
        # Node -> Node = Reach
        elif isinstance(source, NodeItem) and isinstance(target, NodeItem):
            self.add_reach(source, target)
        # Everything else is blocked (SubBasin -> SubBasin, etc.)

    def _cancel_temp_line(self):
        if self._temp_line is not None:
            self.removeItem(self._temp_line)
            self._temp_line = None
        self._conn_source = None

    # ------------------------------------------------------------------ #
    #  Context menu actions                                               #
    # ------------------------------------------------------------------ #
    def rename_element(self, item):
        new_label = rename_element(item.label)
        if new_label is not None:
            item.label = new_label
            self._model.rename(item.item_id, new_label)

    def show_properties(self, item):
        if isinstance(item, SubBasinItem):
            dlg = SubBasinParamsDialog(item)
        else:
            dlg = PropertiesDialog(item)
        dlg.exec()

    # ------------------------------------------------------------------ #
    #  Deletion with cascading cleanup                                    #
    # ------------------------------------------------------------------ #
    def remove_element(self, item):
        if isinstance(item, SubBasinItem):
            # Remove all connections from this sub-basin
            for conn in list(item.connections):
                self._remove_connection_line(conn)
            self._model.remove(item.item_id)
            self.removeItem(item)

        elif isinstance(item, NodeItem):
            # Remove all reaches attached to this node
            for edge in list(item.edges):
                self._remove_reach(edge)
            # Remove all diversions attached to this node
            for div in list(item.diversions):
                self._remove_diversion(div)
            # Remove all connections to this node
            for conn in list(item.connections):
                self._remove_connection_line(conn)
            self._model.remove(item.item_id)
            self.removeItem(item)

        elif isinstance(item, ReachItem):
            self._remove_reach(item)

        elif isinstance(item, DiversionItem):
            self._remove_diversion(item)

        elif isinstance(item, ConnectionLine):
            self._remove_connection_line(item)

        self.element_counts_changed.emit()

    def _remove_reach(self, reach: ReachItem):
        reach.source_item.remove_edge(reach)
        reach.dest_item.remove_edge(reach)
        self._model.remove(reach.item_id)
        self.removeItem(reach)

    def _remove_diversion(self, div: DiversionItem):
        div.source_item.remove_diversion(div)
        div.dest_item.remove_diversion(div)
        self._model.remove(div.item_id)
        self.removeItem(div)

    def _remove_connection_line(self, conn: ConnectionLine):
        conn.source_item.remove_connection(conn)
        conn.dest_item.remove_connection(conn)
        self._model.remove(conn.item_id)
        self.removeItem(conn)

    def delete_selected(self):
        for item in list(self.selectedItems()):
            if item.scene() is not None:
                self.remove_element(item)

    # ------------------------------------------------------------------ #
    #  Clear all                                                          #
    # ------------------------------------------------------------------ #
    def clear_all(self):
        self.clear()
        self.element_counts_changed.emit()

    # ------------------------------------------------------------------ #
    #  Status info                                                        #
    # ------------------------------------------------------------------ #
    def get_element_counts(self) -> dict[str, int]:
        counts = {"Sub-basins": 0, "Nodes": 0, "Reaches": 0, "Diversions": 0, "Connections": 0}
        for item in self.items():
            if isinstance(item, SubBasinItem):
                counts["Sub-basins"] += 1
            elif isinstance(item, NodeItem):
                counts["Nodes"] += 1
            elif isinstance(item, ReachItem):
                counts["Reaches"] += 1
            elif isinstance(item, DiversionItem):
                counts["Diversions"] += 1
            elif isinstance(item, ConnectionLine):
                counts["Connections"] += 1
        return counts
