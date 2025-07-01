# kg_interface.py (updated for active decision support)

import os
from neo4j import GraphDatabase
from typing import List, Dict
import uuid # Added for uuid.uuid4()
from dotenv import load_dotenv

load_dotenv()

class KGInterface:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "eklil@2017")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def cypher(self, query: str, params: Dict = None, log: bool = True) -> List[Dict]:
        if log:
            print(f"\n[Cypher Query]\n{query}\nWith Params: {params}")
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]


    def recommend_ndt_methods(self, material: str, defect: str, environment: str) -> List[str]:
        query = """
        // High-level path
        MATCH (m:Material {name:$material})-[:HAS_DETERIORATION_MECHANISM]->(d:Deterioration {name:$defect})
        MATCH (d)-[:DETECTED_BY]->(n:NDTMethod)-[:REQUIRES_ENVIRONMENT]->(e:Environment {name:$environment})
        RETURN DISTINCT n.name AS method

        UNION

        // Mechanism-based path
        MATCH (m:Material {name:$material})-[:HAS_DETERIORATION_MECHANISM]->(dm:DeteriorationMechanism {name:$defect})
        MATCH (dm)-[:CAUSES_PHYSICAL_CHANGE]->(p:PhysicalChange)
        MATCH (p)-[:DETECTED_BY]->(n:NDTMethod)-[:REQUIRES_ENVIRONMENT]->(e:Environment {name:$environment})
        RETURN DISTINCT n.name AS method
        """
        return [r["method"] for r in self.cypher(query, {
            "material": material,
            "defect": defect,
            "environment": environment
        })]


    def recommend_sensors(self, defect: str) -> List[str]:
        query = """
        // Path A: Deterioration → NDTMethod → Sensor
        MATCH (d:Deterioration {name:$defect})-[:DETECTED_BY]->(n:NDTMethod)
        MATCH (s:Sensor)-[:RECOMMENDED_FOR]->(n)
        RETURN DISTINCT s.name AS sensor

        UNION

        // Path B: DeteriorationMechanism → PhysicalChange → NDTMethod → Sensor
        MATCH (dm:DeteriorationMechanism {name:$defect})-[:CAUSES_PHYSICAL_CHANGE]->(p:PhysicalChange)
        MATCH (p)-[:DETECTED_BY]->(n:NDTMethod)
        MATCH (s:Sensor)-[:RECOMMENDED_FOR]->(n)
        RETURN DISTINCT s.name AS sensor
        """
        return [r["sensor"] for r in self.cypher(query, {"defect": defect})]

    def get_reasoning_subgraph(self, material: str, defect: str, environment: str) -> List[Dict]:
        query = """
        OPTIONAL MATCH (m:Material {name:$material})-[:HAS_DETERIORATION_MECHANISM]->(d)
        WHERE d.name = $defect
        OPTIONAL MATCH (d)-[:DETECTED_BY]->(n:NDTMethod)-[:REQUIRES_ENVIRONMENT]->(e:Environment {name:$environment})
        OPTIONAL MATCH (s:Sensor)-[:RECOMMENDED_FOR]->(n)
        RETURN m.name AS material, d.name AS defect, n.name AS method, e.name AS env, s.name AS sensor
        """
        return self.cypher(query, {"material": material, "defect": defect, "environment": environment})

    # --- 1️⃣ Update KGInterface.py ---
    # Add this function to KGInterface class

import uuid # Added for uuid.uuid4()

class KGInterface:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "eklil@2017")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def cypher(self, query: str, params: Dict = None, log: bool = True) -> List[Dict]:
        if log:
            print(f"\n[Cypher Query]\n{query}\nWith Params: {params}")
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]


    def recommend_ndt_methods(self, material: str, defect: str, environment: str) -> List[str]:
        query = """
        // High-level path
        MATCH (m:Material {name:$material})-[:HAS_DETERIORATION_MECHANISM]->(d:Deterioration {name:$defect})
        MATCH (d)-[:DETECTED_BY]->(n:NDTMethod)-[:REQUIRES_ENVIRONMENT]->(e:Environment {name:$environment})
        RETURN DISTINCT n.name AS method

        UNION

        // Mechanism-based path
        MATCH (m:Material {name:$material})-[:HAS_DETERIORATION_MECHANISM]->(dm:DeteriorationMechanism {name:$defect})
        MATCH (dm)-[:CAUSES_PHYSICAL_CHANGE]->(p:PhysicalChange)
        MATCH (p)-[:DETECTED_BY]->(n:NDTMethod)-[:REQUIRES_ENVIRONMENT]->(e:Environment {name:$environment})
        RETURN DISTINCT n.name AS method
        """
        return [r["method"] for r in self.cypher(query, {
            "material": material,
            "defect": defect,
            "environment": environment
        })]


    def recommend_sensors(self, defect: str) -> List[str]:
        query = """
        // Path A: Deterioration → NDTMethod → Sensor
        MATCH (d:Deterioration {name:$defect})-[:DETECTED_BY]->(n:NDTMethod)
        MATCH (s:Sensor)-[:RECOMMENDED_FOR]->(n)
        RETURN DISTINCT s.name AS sensor

        UNION

        // Path B: DeteriorationMechanism → PhysicalChange → NDTMethod → Sensor
        MATCH (dm:DeteriorationMechanism {name:$defect})-[:CAUSES_PHYSICAL_CHANGE]->(p:PhysicalChange)
        MATCH (p)-[:DETECTED_BY]->(n:NDTMethod)
        MATCH (s:Sensor)-[:RECOMMENDED_FOR]->(n)
        RETURN DISTINCT s.name AS sensor
        """
        return [r["sensor"] for r in self.cypher(query, {"defect": defect})]

    def get_reasoning_subgraph(self, material: str, defect: str, environment: str) -> List[Dict]:
        query = """
        OPTIONAL MATCH (m:Material {name:$material})-[:HAS_DETERIORATION_MECHANISM]->(d)
        WHERE d.name = $defect
        OPTIONAL MATCH (d)-[:DETECTED_BY]->(n:NDTMethod)-[:REQUIRES_ENVIRONMENT]->(e:Environment {name:$environment})
        OPTIONAL MATCH (s:Sensor)-[:RECOMMENDED_FOR]->(n)
        RETURN m.name AS material, d.name AS defect, n.name AS method, e.name AS env, s.name AS sensor
        """
        return self.cypher(query, {"material": material, "defect": defect, "environment": environment})

    # --- 1️⃣ Update KGInterface.py ---
    # Add this function to KGInterface class

    def log_inspection_plan(self, plan: str, material: str, defect: str, environment: str) -> str: # Changed return type
        plan_id = str(uuid.uuid4())
        query = """
        CREATE (i:InspectionPlan {
            planID: $plan_id, // Added unique ID
            text: $plan,
            material: $material,
            defect: $defect,
            environment: $environment,
            timestamp: datetime()
        })
        """
        self.cypher(query, {
            "plan": plan,
            "material": material,
            "defect": defect,
            "environment": environment
        })

    def get_materials(self) -> List[str]:
        query = "MATCH (m:Material) RETURN DISTINCT m.name AS name ORDER BY name"
        return [r["name"] for r in self.cypher(query)]

    def get_deterioration_types(self) -> List[str]:
        query = "MATCH (d:Deterioration) RETURN DISTINCT d.name AS name ORDER BY name"
        return [r["name"] for r in self.cypher(query)]

    def get_environments(self) -> List[str]:
        query = "MATCH (e:Environment) RETURN DISTINCT e.name AS name ORDER BY name"
        return [r["name"] for r in self.cypher(query)]

    def log_plan_feedback(self, plan_identifier: str, is_helpful: bool, feedback_text: str = None) -> None:
        """
        Logs user feedback about an inspection plan.
        'plan_identifier' can be the forecast text or a hash of it for now.
        """
        query = """
        MATCH (ip:InspectionPlan {planID: $plan_id}) // Match plan by its unique ID
        CREATE (f:Feedback {
            is_helpful: $is_helpful,
            comment: $feedback_text,
            timestamp: datetime()
            // plan_ref_text: $plan_id // Optionally store plan_id on feedback too for direct ref
        })
        CREATE (f)-[:REFERS_TO_PLAN]->(ip)
        """
        self.cypher(query, {
            "plan_id": plan_id, # Changed parameter name
            "is_helpful": is_helpful,
            "feedback_text": feedback_text
        })
        print(f"Feedback logged for plan ID: {plan_id}. Helpful: {is_helpful}")
