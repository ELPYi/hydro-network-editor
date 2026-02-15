"""Data model for the hydro network: counters, ID generation, element registry."""


class NetworkModel:
    def __init__(self):
        self.reset()

    def reset(self):
        self._counters = {
            "subbasin": 0,
            "node": 0,
            "reach": 0,
            "connection": 0,
            "diversion": 0,
        }
        self._elements: dict[str, dict] = {}

    # --- creation helpers ---
    def create_subbasin(self) -> tuple[str, str]:
        self._counters["subbasin"] += 1
        n = self._counters["subbasin"]
        item_id = f"subbasin_{n}"
        label = f"B{n}"
        self._elements[item_id] = {"type": "subbasin", "label": label}
        return item_id, label

    def create_node(self) -> tuple[str, str]:
        self._counters["node"] += 1
        n = self._counters["node"]
        item_id = f"node_{n}"
        label = f"N{n}"
        self._elements[item_id] = {"type": "node", "label": label}
        return item_id, label

    def create_reach(self) -> tuple[str, str]:
        self._counters["reach"] += 1
        n = self._counters["reach"]
        item_id = f"reach_{n}"
        label = f"C{n}"
        self._elements[item_id] = {"type": "reach", "label": label}
        return item_id, label

    def create_diversion(self) -> tuple[str, str]:
        self._counters["diversion"] += 1
        n = self._counters["diversion"]
        item_id = f"diversion_{n}"
        label = f"D{n}"
        self._elements[item_id] = {"type": "diversion", "label": label}
        return item_id, label

    def create_connection(self) -> tuple[str, str]:
        self._counters["connection"] += 1
        n = self._counters["connection"]
        item_id = f"connection_{n}"
        label = ""
        self._elements[item_id] = {"type": "connection", "label": label}
        return item_id, label

    # --- registry ---
    def rename(self, item_id: str, new_label: str):
        if item_id in self._elements:
            self._elements[item_id]["label"] = new_label

    def remove(self, item_id: str):
        self._elements.pop(item_id, None)

    def get(self, item_id: str) -> dict | None:
        return self._elements.get(item_id)

    # --- counters for serialization ---
    @property
    def counters(self) -> dict[str, int]:
        return dict(self._counters)

    def set_counters(self, counters: dict[str, int]):
        self._counters.update(counters)

    # --- bulk creation for loading (allows specifying id/label) ---
    def register(self, item_id: str, element_type: str, label: str):
        self._elements[item_id] = {"type": element_type, "label": label}
