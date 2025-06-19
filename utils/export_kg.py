# utils/export_kg.py

from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal
from neo4j import GraphDatabase
import os

# Namespaces for ontology (schema) and instances
NDT = Namespace("http://example.org/ndt#")
EX = Namespace("http://example.org/instance#")

def export_kg_to_owl(output_file="kg_export.ttl"):
    print("[INFO] Starting KG export...")

    # Setup Neo4j connection
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "eklil@2017")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    g = Graph()
    g.bind("ndt", NDT)
    g.bind("ex", EX)

    with driver.session() as session:
        # Export nodes and their types
        print("[INFO] Fetching nodes...")
        nodes = session.run("MATCH (n) RETURN ID(n) AS id, labels(n) AS labels, n.name AS name")
        for record in nodes:
            node_uri = EX[f"node{record['id']}"]
            for label in record["labels"]:
                g.add((node_uri, RDF.type, NDT[label]))
            g.add((node_uri, RDFS.label, Literal(record["name"])))

        # Export relationships
        print("[INFO] Fetching relationships...")
        rels = session.run("""
            MATCH (a)-[r]->(b)
            RETURN ID(a) AS source, type(r) AS rel, ID(b) AS target
        """)
        for record in rels:
            g.add((EX[f"node{record['source']}"], NDT[record["rel"]], EX[f"node{record['target']}"]))

    # Serialize graph
    g.serialize(destination=output_file, format="turtle")
    print(f"[✅] Exported KG to {output_file}")

# Execute if run as script
if __name__ == "__main__":
    export_kg_to_owl()
