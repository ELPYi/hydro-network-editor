"""QGraphicsView with zoom, pan, and drag-drop forwarding."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QPainter, QWheelEvent
from PyQt6.QtWidgets import QGraphicsView

MIN_ZOOM = 0.1
MAX_ZOOM = 5.0
ZOOM_FACTOR = 1.15


class NetworkView(QGraphicsView):
    zoom_changed = pyqtSignal()

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._zoom = 1.0
        self._panning = False
        self._pan_start = None

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setAcceptDrops(True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Grid background
        self.setBackgroundBrush(Qt.GlobalColor.white)

    @property
    def current_zoom(self) -> float:
        return self._zoom

    def set_drawing_mode(self, active: bool):
        if active:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    # --- Zoom ---
    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            factor = ZOOM_FACTOR
        else:
            factor = 1.0 / ZOOM_FACTOR

        new_zoom = self._zoom * factor
        if new_zoom < MIN_ZOOM or new_zoom > MAX_ZOOM:
            return

        self._zoom = new_zoom
        self.scale(factor, factor)
        self.zoom_changed.emit()

    # --- Pan (middle click) ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning and self._pan_start is not None:
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # --- Drag-drop forwarding ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        # Forward to scene
        super().dropEvent(event)

    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)
        # Draw grid
        from PyQt6.QtGui import QColor, QPen
        grid_size = 20
        pen = QPen(QColor("#E0E0E0"), 0.5)
        painter.setPen(pen)

        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        x = left
        while x < rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += grid_size

        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += grid_size
