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
        The 'defect' parameter will be treated as the name for a 'Deterioration' node.
        """
        query_check = """
        MATCH (m:Material {name: $material})-[:hasDeteriorationMechanism]->(d:Deterioration {name: $defect_name})
        MATCH (d)-[:detectedBy]->(n:NDTMethod {name: $method_name})
        RETURN m, d, n
        """

        query_create = """
        MERGE (m:Material {name: $material_name})
        MERGE (d:Deterioration {name: $defect_name}) // Create/merge as Deterioration
        MERGE (n:NDTMethod {name: $method_name})
        MERGE (m)-[r1:hasDeteriorationMechanism]->(d) // Use ontology-aligned relationship
        MERGE (d)-[r2:detectedBy]->(n) // Use ontology-aligned relationship

        CREATE (p:ProposedFact {
            factId: $id, // Aligned with ontology
            proposedMaterialName: $material_name, // Aligned with ontology
            proposedDefectName: $defect_name, // Aligned with ontology
            methodName: $method_name, // Aligned with ontology
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
