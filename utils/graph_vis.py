# utils/graph_viz.py
from pyvis.network import Network
from pathlib import Path
import streamlit.components.v1 as components

def render_kg_graph(subgraph_data):
    from pyvis.network import Network
    from pathlib import Path
    import streamlit.components.v1 as components

    net = Network(height="450px", width="100%", bgcolor="#222222", font_color="white")

    for row in subgraph_data:
        m, d, n, e, s = row['material'], row['defect'], row['method'], row['env'], row['sensor']

        if m: net.add_node(m, label=m, color="#00aaff")
        if d: net.add_node(d, label=d, color="#ffaa00")
        if n: net.add_node(n, label=n, color="#66ff66")
        if e: net.add_node(e, label=e, color="#dd44ff")
        if s: net.add_node(s, label=s, color="#ff5555")

        if m and d: net.add_edge(m, d)
        if d and n: net.add_edge(d, n)
        if n and e: net.add_edge(n, e)
        if s and n: net.add_edge(s, n)

    net.set_options(""" 
        {
        "nodes": {
            "shape": "dot",
            "size": 16,
            "font": { "size": 14 }
        },
        "edges": {
            "arrows": "to"
        }
        }
        """)

    net.save_graph("graph.html")
    components.html(Path("graph.html").read_text(), height=480)

