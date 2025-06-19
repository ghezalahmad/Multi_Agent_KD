# utils/kg_exporter.py
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from datetime import datetime

def export_kg_to_owl(triples, output_file="ndt_kg.owl"):
    g = Graph()
    NDT = Namespace("http://example.org/ndt#")
    EX = Namespace("http://example.org/instance#")
    g.bind("ndt", NDT)
    g.bind("ex", EX)

    for subj, pred, obj in triples:
        subj_uri = EX[subj.replace(" ", "_")]
        pred_uri = NDT[pred.replace(" ", "_")]
        if isinstance(obj, str):
            if obj.lower() in ["concrete", "steel", "cracking"]:
                obj_uri = EX[obj.replace(" ", "_")]
                g.add((subj_uri, pred_uri, obj_uri))
            else:
                g.add((subj_uri, pred_uri, Literal(obj)))
        else:
            g.add((subj_uri, pred_uri, obj))

    g.serialize(destination=output_file, format="pretty-xml")
    print(f"✅ Exported KG to {output_file}")
