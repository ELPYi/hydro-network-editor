"""Matplotlib chart widget embedded in a QWidget via FigureCanvasQTAgg."""
from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


class ChartWidget(QWidget):
    """Wraps a Matplotlib figure for use inside Qt layouts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._figure = Figure(tight_layout=True)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)
        self._ax = self._figure.add_subplot(111)

    # ------------------------------------------------------------------
    # Public plotting methods
    # ------------------------------------------------------------------

    def plot_line(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_label: str = "Time",
        y_label: str = "Value",
        title: str = "",
    ) -> None:
        self._ax.cla()
        if x.size > 0 and y.size > 0:
            self._ax.plot(x, y, marker="o", markersize=3, linewidth=1.5)
        self._ax.set_xlabel(x_label)
        self._ax.set_ylabel(y_label)
        if title:
            self._ax.set_title(title)
        self._ax.grid(True, linestyle="--", alpha=0.5)
        self._canvas.draw()

    def plot_bar(
        self,
        categories: np.ndarray,
        values: np.ndarray,
        x_label: str = "Time",
        y_label: str = "Value",
        title: str = "",
    ) -> None:
        self._ax.cla()
        if categories.size > 0 and values.size > 0:
            self._ax.bar(categories, values, width=float(np.diff(categories).mean()) * 0.8
                         if len(categories) > 1 else 1.0, align="center")
        self._ax.set_xlabel(x_label)
        self._ax.set_ylabel(y_label)
        if title:
            self._ax.set_title(title)
        self._ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        self._canvas.draw()

    def clear(self) -> None:
        self._ax.cla()
        self._canvas.draw()
