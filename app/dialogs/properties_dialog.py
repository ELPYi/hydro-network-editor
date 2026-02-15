"""Placeholder properties dialog for future use."""
from PyQt6.QtWidgets import QDialog, QFormLayout, QLabel, QDialogButtonBox

from app.canvas.items.subbasin_item import SubBasinItem
from app.canvas.items.node_item import NodeItem
from app.canvas.items.reach_item import ReachItem
from app.canvas.items.diversion_item import DiversionItem
from app.canvas.items.connection_line import ConnectionLine


def _element_type_name(item) -> str:
    if isinstance(item, SubBasinItem):
        return "Sub-basin"
    if isinstance(item, NodeItem):
        return "Node"
    if isinstance(item, ReachItem):
        return "Reach"
    if isinstance(item, DiversionItem):
        return "Diversion"
    if isinstance(item, ConnectionLine):
        return "Connection"
    return "Unknown"


class PropertiesDialog(QDialog):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Properties")
        self.setMinimumWidth(250)

        layout = QFormLayout(self)
        layout.addRow("Type:", QLabel(_element_type_name(item)))
        layout.addRow("ID:", QLabel(item.item_id))
        layout.addRow("Label:", QLabel(item.label if item.label else "(none)"))

        if hasattr(item, "pos"):
            pos = item.pos()
            layout.addRow("Position:", QLabel(f"({pos.x():.1f}, {pos.y():.1f})"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addRow(buttons)
