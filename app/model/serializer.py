"""JSON save/load for the hydro network."""
import json

from app.model.network_model import NetworkModel


class Serializer:
    @staticmethod
    def save(path: str, model: NetworkModel, scene):
        from app.canvas.items.subbasin_item import SubBasinItem
        from app.canvas.items.node_item import NodeItem
        from app.canvas.items.reach_item import ReachItem
        from app.canvas.items.connection_line import ConnectionLine
        from app.canvas.items.diversion_item import DiversionItem

        data = {
            "version": "1.0",
            "counters": model.counters,
            "subbasins": [],
            "nodes": [],
            "reaches": [],
            "diversions": [],
            "connections": [],
        }

        for item in scene.items():
            if isinstance(item, SubBasinItem):
                data["subbasins"].append({
                    "id": item.item_id,
                    "label": item.label,
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                    "parameters": dict(item.parameters),
                    "rainfall_time_unit": item.rainfall_time_unit,
                    "rainfall_data": item.rainfall_data,
                })
            elif isinstance(item, NodeItem):
                data["nodes"].append({
                    "id": item.item_id,
                    "label": item.label,
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                })
            elif isinstance(item, ReachItem):
                data["reaches"].append({
                    "id": item.item_id,
                    "label": item.label,
                    "source_node_id": item.source_item.item_id,
                    "dest_node_id": item.dest_item.item_id,
                })
            elif isinstance(item, DiversionItem):
                data["diversions"].append({
                    "id": item.item_id,
                    "label": item.label,
                    "source_node_id": item.source_item.item_id,
                    "dest_node_id": item.dest_item.item_id,
                })
            elif isinstance(item, ConnectionLine):
                data["connections"].append({
                    "id": item.item_id,
                    "source_subbasin_id": item.source_item.item_id,
                    "dest_node_id": item.dest_item.item_id,
                })

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(path: str, model: NetworkModel, scene):
        with open(path, "r") as f:
            data = json.load(f)

        scene.clear_all()
        model.reset()
        model.set_counters(data.get("counters", {}))

        # Phase 1: create nodes and sub-basins
        id_to_item = {}

        for sb in data.get("subbasins", []):
            model.register(sb["id"], "subbasin", sb["label"])
            item = scene.add_subbasin(sb["x"], sb["y"], sb["id"], sb["label"])
            if "parameters" in sb:
                item.parameters.update(sb["parameters"])
            item.rainfall_time_unit = sb.get("rainfall_time_unit", "hours")
            item.rainfall_data = sb.get("rainfall_data", [])
            id_to_item[sb["id"]] = item

        for nd in data.get("nodes", []):
            model.register(nd["id"], "node", nd["label"])
            item = scene.add_node(nd["x"], nd["y"], nd["id"], nd["label"])
            id_to_item[nd["id"]] = item

        # Phase 2: create edges
        for r in data.get("reaches", []):
            model.register(r["id"], "reach", r["label"])
            source = id_to_item.get(r["source_node_id"])
            dest = id_to_item.get(r["dest_node_id"])
            if source and dest:
                scene.add_reach(source, dest, r["id"], r["label"])

        for d in data.get("diversions", []):
            model.register(d["id"], "diversion", d["label"])
            source = id_to_item.get(d["source_node_id"])
            dest = id_to_item.get(d["dest_node_id"])
            if source and dest:
                scene.add_diversion(source, dest, d["id"], d["label"])

        for c in data.get("connections", []):
            model.register(c["id"], "connection", c.get("label", ""))
            source = id_to_item.get(c["source_subbasin_id"])
            dest = id_to_item.get(c["dest_node_id"])
            if source and dest:
                scene.add_connection(source, dest, c["id"])

        scene.element_counts_changed.emit()
