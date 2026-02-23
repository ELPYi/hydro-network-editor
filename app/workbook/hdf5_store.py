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
        times,
        values: np.ndarray,
        time_unit: str = "hours",
        area_km2: float = 0.0,
    ) -> None:
        """Write (or overwrite) a subbasin rainfall dataset.

        *times* may be a list/array of strings (date/time) or floats.
        """
        with h5py.File(self._path, "a") as h5:
            group_path = f"inputs/rainfall/{subbasin_label}"
            # Remove existing group so we can recreate cleanly
            if group_path in h5:
                del h5[group_path]
            grp = h5.require_group(group_path)
            # Write time dataset: strings or floats
            if _is_string_sequence(times):
                grp.create_dataset(
                    "time",
                    data=np.array([str(t) for t in times], dtype=h5py.string_dtype()),
                )
            else:
                grp.create_dataset("time", data=np.asarray(times, dtype=np.float64))
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
                arr = _read_dataset_values(node)
                return arr.reshape(-1, 1), [hdf5_path.split("/")[-1]]
            # It's a group — collect child datasets
            datasets: dict[str, np.ndarray] = {}
            for name, item in node.items():
                if isinstance(item, h5py.Dataset):
                    datasets[name] = _read_dataset_values(item)

        if not datasets:
            return np.empty((0, 0)), []

        # Always put 'time' first so Date/Time appears as column 0
        col_names = sorted(datasets.keys(), key=lambda c: (0 if c == "time" else 1, c))
        length = min(len(v) for v in datasets.values())
        # Use object array so strings and floats can coexist
        mat = np.empty((length, len(col_names)), dtype=object)
        for i, col in enumerate(col_names):
            mat[:, i] = datasets[col][:length]
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

def _is_string_sequence(seq) -> bool:
    """Return True if *seq* contains string values."""
    if isinstance(seq, np.ndarray):
        return seq.dtype.kind in ("U", "S", "O") and seq.size > 0 and isinstance(seq.flat[0], str)
    return bool(seq) and isinstance(next(iter(seq)), str)


def _read_dataset_values(ds: h5py.Dataset) -> np.ndarray:
    """Read a dataset, decoding bytes→str for string datasets."""
    data = ds[()]
    if ds.dtype.kind == "S" or (ds.dtype.kind == "O" and data.size > 0 and isinstance(data.flat[0], bytes)):
        return np.array([v.decode("utf-8") if isinstance(v, bytes) else str(v) for v in data])
    if ds.dtype.kind == "O" and data.size > 0 and isinstance(data.flat[0], str):
        return data  # already decoded strings (h5py 3.x vlen)
    return data


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
