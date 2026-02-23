"""Matplotlib chart widget embedded in a QWidget via FigureCanvasQTAgg."""
from __future__ import annotations

from datetime import datetime

import matplotlib.dates as mdates
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d-%m-%Y",
)


def _try_parse_dates(x) -> np.ndarray | None:
    """Return matplotlib date numbers if every value in *x* parses as a date."""
    dates = []
    for v in x:
        s = str(v).strip()
        parsed = None
        for fmt in _DATE_FORMATS:
            try:
                parsed = datetime.strptime(s, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            return None
        dates.append(parsed)
    return mdates.date2num(dates) if dates else None


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
        y_f = np.array(y, dtype=float)
        if x.size > 0 and y_f.size > 0:
            date_nums = _try_parse_dates(x)
            if date_nums is not None:
                self._ax.plot_date(date_nums, y_f, "-o", markersize=3, linewidth=1.5)
                self._ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(
                    self._ax.xaxis.get_major_locator()))
                self._figure.autofmt_xdate(rotation=30, ha="right")
            else:
                try:
                    x_f = np.array(x, dtype=float)
                except (ValueError, TypeError):
                    x_f = np.arange(len(y_f))
                self._ax.plot(x_f, y_f, marker="o", markersize=3, linewidth=1.5)
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
        y_f = np.array(values, dtype=float)
        if categories.size > 0 and y_f.size > 0:
            date_nums = _try_parse_dates(categories)
            if date_nums is not None:
                # Use bar with numeric positions, then format the axis
                width = float(np.diff(date_nums).mean()) * 0.8 if len(date_nums) > 1 else 1.0
                self._ax.bar(date_nums, y_f, width=width, align="center")
                self._ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(
                    self._ax.xaxis.get_major_locator()))
                self._figure.autofmt_xdate(rotation=30, ha="right")
            else:
                try:
                    x_f = np.array(categories, dtype=float)
                    width = float(np.diff(x_f).mean()) * 0.8 if len(x_f) > 1 else 1.0
                except (ValueError, TypeError):
                    x_f = np.arange(len(y_f))
                    width = 0.8
                self._ax.bar(x_f, y_f, width=width, align="center")
        self._ax.set_xlabel(x_label)
        self._ax.set_ylabel(y_label)
        if title:
            self._ax.set_title(title)
        self._ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        self._canvas.draw()

    def clear(self) -> None:
        self._ax.cla()
        self._canvas.draw()
