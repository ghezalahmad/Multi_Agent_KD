# utils/kg_enrichment.py
from neo4j import GraphDatabase
import uuid

class KGAugmentor:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="eklil@2017"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def propose_fact(self, material, defect, method, confidence=0.8, source="LLM inference"):
        """
        Propose a new material-defect-method fact to the KG, if it does not already exist.
        """
        query_check = """
        MATCH (m:Material {name: $material})-[:HAS_DEFECT]->(d:Defect {name: $defect})
              -[:DETECTED_BY]->(n:NDTMethod {name: $method})
        RETURN m, d, n
        """

        query_create = """
        MERGE (m:Material {name: $material})
        MERGE (d:Defect {name: $defect})
        MERGE (n:NDTMethod {name: $method})
        MERGE (m)-[:HAS_DEFECT]->(d)
        MERGE (d)-[:DETECTED_BY]->(n)

        CREATE (p:ProposedFact {
            id: $id,
            material: $material,
            defect: $defect,
            method: $method,
            source: $source,
            confidence: $confidence,
            status: "pending"
        })
        MERGE (p)-[:PROPOSES]->(m)
        MERGE (p)-[:PROPOSES]->(d)
        MERGE (p)-[:PROPOSES]->(n)
        """

        with self.driver.session() as session:
            result = session.run(query_check, material=material, defect=defect, method=method)
            if result.peek():
                return False  # Already exists, no need to propose

            session.run(
                query_create,
                id=str(uuid.uuid4()),
                material=material,
                defect=defect,
                method=method,
                source=source,
                confidence=confidence
            )
            return True
