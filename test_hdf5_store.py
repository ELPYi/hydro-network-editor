"""Standalone round-trip test for HDF5Store — no Qt required.

Run with:
    python test_hdf5_store.py
"""
import os
import sys
import tempfile
import traceback

import numpy as np

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app.workbook.hdf5_store import HDF5Store

PASSED = []
FAILED = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSED.append(name)
        print(f"  PASS  {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


def run_tests() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        h5_path = os.path.join(tmpdir, "test_project.h5")
        store = HDF5Store(h5_path)

        # ----------------------------------------------------------------
        # 1. open() creates file and skeleton
        # ----------------------------------------------------------------
        print("\n[1] open() creates file and skeleton")
        store.open(project_name="TestProject")
        check("file exists after open()", os.path.exists(h5_path))

        import h5py
        with h5py.File(h5_path, "r") as h5:
            check("metadata group exists", "metadata" in h5)
            check("inputs/rainfall group exists", "inputs/rainfall" in h5)
            check("intermediates/soil_moisture exists", "intermediates/soil_moisture" in h5)
            check("outputs/hydrographs exists", "outputs/hydrographs" in h5)
            pname = h5["metadata/project_name"][()].decode() if isinstance(
                h5["metadata/project_name"][()], bytes
            ) else h5["metadata/project_name"][()]
            check("project_name written", pname == "TestProject", repr(pname))

        # ----------------------------------------------------------------
        # 2. write_rainfall round-trip
        # ----------------------------------------------------------------
        print("\n[2] write_rainfall() round-trip")
        times = np.array([0.0, 1.0, 2.0, 3.0])
        values = np.array([0.5, 2.3, 4.1, 1.0])
        store.write_rainfall(
            subbasin_label="B1",
            subbasin_id="sb-001",
            times=times,
            values=values,
            time_unit="hours",
            area_km2=12.5,
        )

        with h5py.File(h5_path, "r") as h5:
            check("inputs/rainfall/B1 group created", "inputs/rainfall/B1" in h5)
            t_read = h5["inputs/rainfall/B1/time"][()]
            r_read = h5["inputs/rainfall/B1/rainfall_mm"][()]
            check("time array matches", np.allclose(t_read, times), f"{t_read}")
            check("rainfall_mm array matches", np.allclose(r_read, values), f"{r_read}")
            check("time_unit attr", h5["inputs/rainfall/B1"].attrs["time_unit"] == "hours")
            check("subbasin_id attr", h5["inputs/rainfall/B1"].attrs["subbasin_id"] == "sb-001")
            check("area_km2 attr", h5["inputs/rainfall/B1"].attrs["area_km2"] == 12.5)

        # ----------------------------------------------------------------
        # 3. read_dataset for a group path
        # ----------------------------------------------------------------
        print("\n[3] read_dataset() on group path")
        mat, cols = store.read_dataset("inputs/rainfall/B1")
        check("returns ndarray", isinstance(mat, np.ndarray))
        check("shape is (4, 2)", mat.shape == (4, 2), str(mat.shape))
        check("cols has 2 entries", len(cols) == 2, str(cols))
        check("time column matches", np.allclose(mat[:, cols.index("time")], times))
        check("rainfall_mm column matches", np.allclose(mat[:, cols.index("rainfall_mm")], values))

        # ----------------------------------------------------------------
        # 4. list_tree returns nested dict
        # ----------------------------------------------------------------
        print("\n[4] list_tree()")
        tree = store.list_tree()
        check("tree has 'inputs' key", "inputs" in tree)
        check("tree has 'metadata' key", "metadata" in tree)
        check(
            "B1 group is in tree",
            "B1" in tree.get("inputs", {}).get("rainfall", {}),
        )

        # ----------------------------------------------------------------
        # 5. Overwrite rainfall (second write_rainfall call)
        # ----------------------------------------------------------------
        print("\n[5] Overwrite with new data")
        new_times = np.array([0.0, 1.0])
        new_vals = np.array([9.9, 8.8])
        store.write_rainfall("B1", "sb-001", new_times, new_vals)
        mat2, cols2 = store.read_dataset("inputs/rainfall/B1")
        check("overwrite: shape (2, 2)", mat2.shape == (2, 2), str(mat2.shape))
        check("overwrite: values correct", np.allclose(mat2[:, cols2.index("rainfall_mm")], new_vals))

        # ----------------------------------------------------------------
        # 6. read_dataset on non-existent path
        # ----------------------------------------------------------------
        print("\n[6] read_dataset on non-existent path")
        mat3, cols3 = store.read_dataset("inputs/rainfall/NOSUCHBASIN")
        check("empty array returned", mat3.size == 0)
        check("empty cols returned", cols3 == [])

        # ----------------------------------------------------------------
        # 7. open() is idempotent (no error on second call)
        # ----------------------------------------------------------------
        print("\n[7] open() idempotent")
        try:
            store.open(project_name="AnotherName")
            check("second open() does not raise", True)
        except Exception as exc:
            check("second open() does not raise", False, str(exc))

        # ----------------------------------------------------------------
        # 8. write_hydrograph round-trip
        # ----------------------------------------------------------------
        print("\n[8] write_hydrograph() round-trip")
        t_h = np.array([0.0, 0.5, 1.0])
        f_h = np.array([0.0, 1.2, 0.4])
        store.write_hydrograph("N1", t_h, f_h)
        mat4, cols4 = store.read_dataset("outputs/hydrographs/N1")
        check("hydrograph shape (3, 2)", mat4.shape == (3, 2), str(mat4.shape))
        check("flow_m3s values correct", np.allclose(mat4[:, cols4.index("flow_m3s")], f_h))

        # ----------------------------------------------------------------
        # 9. update_project_name
        # ----------------------------------------------------------------
        print("\n[9] update_project_name()")
        store.update_project_name("UpdatedProject")
        with h5py.File(h5_path, "r") as h5:
            pname2 = h5["metadata/project_name"][()]
            if isinstance(pname2, bytes):
                pname2 = pname2.decode()
            check("project_name updated", pname2 == "UpdatedProject", repr(pname2))

        # ----------------------------------------------------------------
        # 10. close() is safe to call
        # ----------------------------------------------------------------
        print("\n[10] close() is safe")
        try:
            store.close()
            check("close() does not raise", True)
        except Exception as exc:
            check("close() does not raise", False, str(exc))

    # Summary
    print(f"\n{'='*50}")
    print(f"Results: {len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("Failed tests:", FAILED)
        sys.exit(1)
    else:
        print("All tests passed.")


if __name__ == "__main__":
    try:
        run_tests()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
