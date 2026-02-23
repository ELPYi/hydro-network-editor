"""HDF5 I/O layer — the only module that imports h5py.

Uses an open-per-operation pattern (no persistent file handle) to avoid
Windows file-locking issues when other processes/threads also read the file.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np


# ---------------------------------------------------------------------------
# Group / dataset skeleton written on first file creation
# ---------------------------------------------------------------------------
_SKELETON: dict[str, Any] = {
    "metadata": {
        "project_name": "",
        "created_at": "",
        "units": {
            "rainfall": "mm",
            "flow": "m3/s",
            "time": "hours",
        },
    },
    "inputs": {
        "rainfall": {},
    },
    "intermediates": {
        "soil_moisture": {},
    },
    "outputs": {
        "hydrographs": {},
    },
}


def _write_skeleton(h5: h5py.File, project_name: str) -> None:
    """Recursively create group skeleton in a freshly opened file."""
    def _recurse(parent, d):
        for key, val in d.items():
            if isinstance(val, dict):
                grp = parent.require_group(key)
                _recurse(grp, val)
            elif isinstance(val, str):
                if key not in parent:
                    parent[key] = val

    _recurse(h5, _SKELETON)

    # Overwrite placeholder scalars with real values
    h5["metadata"]["project_name"][()] = project_name
    h5["metadata"]["created_at"][()] = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class HDF5Store:
    """Thin wrapper around h5py for workbook I/O."""

    def __init__(self, h5_path: str | Path):
        self._path = Path(h5_path)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self, project_name: str = "") -> None:
        """Create the file and write the group skeleton if it does not exist."""
        if self._path.exists():
            return  # Already initialised
        with h5py.File(self._path, "w") as h5:
            _write_skeleton(h5, project_name)

    def close(self) -> None:
        """No-op: open-per-operation pattern holds no persistent handle."""

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def write_rainfall(
        self,
        subbasin_label: str,
        subbasin_id: str,
        times: np.ndarray,
        values: np.ndarray,
        time_unit: str = "hours",
        area_km2: float = 0.0,
    ) -> None:
        """Write (or overwrite) a subbasin rainfall dataset."""
        with h5py.File(self._path, "a") as h5:
            group_path = f"inputs/rainfall/{subbasin_label}"
            # Remove existing group so we can recreate cleanly
            if group_path in h5:
                del h5[group_path]
            grp = h5.require_group(group_path)
            grp.create_dataset("time", data=times.astype(np.float64))
            grp.create_dataset("rainfall_mm", data=values.astype(np.float64))
            grp.attrs["time_unit"] = time_unit
            grp.attrs["subbasin_id"] = subbasin_id
            grp.attrs["area_km2"] = float(area_km2)

    def write_hydrograph(
        self,
        node_label: str,
        times: np.ndarray,
        flows: np.ndarray,
    ) -> None:
        """Write (or overwrite) a node hydrograph dataset."""
        with h5py.File(self._path, "a") as h5:
            group_path = f"outputs/hydrographs/{node_label}"
            if group_path in h5:
                del h5[group_path]
            grp = h5.require_group(group_path)
            grp.create_dataset("time", data=times.astype(np.float64))
            grp.create_dataset("flow_m3s", data=flows.astype(np.float64))

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def read_dataset(self, hdf5_path: str) -> tuple[np.ndarray, list[str]]:
        """
        Read a leaf group (e.g. 'inputs/rainfall/B1') and return
        ``(array[N,2], col_names)`` where col_names are the dataset names.

        If *hdf5_path* points to individual datasets rather than a group,
        returns a single-column array.
        """
        with h5py.File(self._path, "r") as h5:
            if hdf5_path not in h5:
                return np.empty((0, 2)), []
            node = h5[hdf5_path]
            if isinstance(node, h5py.Dataset):
                arr = node[()]
                return arr.reshape(-1, 1), [hdf5_path.split("/")[-1]]
            # It's a group — collect child datasets
            datasets: dict[str, np.ndarray] = {}
            for name, item in node.items():
                if isinstance(item, h5py.Dataset):
                    datasets[name] = item[()]

        if not datasets:
            return np.empty((0, 0)), []

        col_names = list(datasets.keys())
        # Stack column-wise; if lengths differ, pad/trim to minimum
        length = min(len(v) for v in datasets.values())
        mat = np.column_stack([datasets[c][:length] for c in col_names])
        return mat, col_names

    def list_tree(self) -> dict:
        """
        Return a nested dict representing all groups/datasets in the file.
        Leaf values are the full HDF5 path strings.
        """
        if not self._path.exists():
            return {}
        result: dict = {}
        with h5py.File(self._path, "r") as h5:
            h5.visititems(lambda name, obj: _collect(result, name, obj))
        return result

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def update_project_name(self, project_name: str) -> None:
        if not self._path.exists():
            return
        with h5py.File(self._path, "a") as h5:
            if "metadata/project_name" in h5:
                h5["metadata/project_name"][()] = project_name


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _collect(result: dict, name: str, obj) -> None:
    """visititems callback — builds nested dict; leaves store the full path."""
    parts = name.split("/")
    node = result
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    leaf = parts[-1]
    if isinstance(obj, h5py.Group):
        node.setdefault(leaf, {})
    else:
        node[leaf] = name  # store full path for read_dataset


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def store_for_json(json_path: str | Path) -> HDF5Store:
    """Return an HDF5Store whose path is derived from *json_path* (same stem)."""
    p = Path(json_path)
    return HDF5Store(p.with_suffix(".h5"))
