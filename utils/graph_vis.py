# utils/graph_viz.py
from pyvis.network import Network
from pathlib import Path
import streamlit.components.v1 as components
import tempfile

def render_kg_graph(subgraph_data):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white", directed=True)
    net.barnes_hut()

    type_colors = {
        "Material": "#00aaff",
        "Defect": "#ffaa00",
        "NDTMethod": "#66ff66",
        "Sensor": "#ff5555",
        "Environment": "#dd44ff"
    }

    for node in subgraph_data["nodes"]:
        net.add_node(
            node["id"],
            label=node["label"],
            title=node["type"],
            color=type_colors.get(node["type"], "#999999"),
            shape="dot"
        )

    for edge in subgraph_data["edges"]:
        net.add_edge(edge["from"], edge["to"], label=edge.get("label", ""))

    tmp_path = Path(tempfile.gettempdir()) / "graph.html"
    net.save_graph(str(tmp_path))
    components.html(tmp_path.read_text(), height=500)
