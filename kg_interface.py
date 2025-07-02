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

    def get_entities_details_for_rag(self, material_name: str = None, defect_name: str = None, method_names: list[str] = None) -> str:
        """
        Fetches details for specified material, defect (name only for now), and NDT methods
        to be used as context for Retrieval Augmented Generation.
        """
        context_parts = []

        if material_name:
            query_material = """
            MATCH (m:Material {name: $material_name})
            RETURN m.description AS description, m.commonApplications AS commonApplications
            LIMIT 1
            """
            material_details = self.cypher(query_material, {"material_name": material_name})
            if material_details and material_details[0]:
                md = material_details[0]
                context_parts.append(f"--- Material: {material_name} ---")
                if md.get("description"):
                    context_parts.append(f"Description: {md['description']}")
                if md.get("commonApplications"):
                    context_parts.append(f"Common Applications: {md['commonApplications']}")

        if defect_name:
            context_parts.append(f"--- Defect/Observation of Concern: {defect_name} ---")
            # Try to fetch detailedDescription for the defect (checking Deterioration then PhysicalChange)
            query_defect_desc = """
            OPTIONAL MATCH (d:Deterioration {name: $defect_name})
            RETURN d.detailedDescription AS description
            LIMIT 1
            """
            defect_desc_details = self.cypher(query_defect_desc, {"defect_name": defect_name})
            if defect_desc_details and defect_desc_details[0] and defect_desc_details[0].get("description"):
                context_parts.append(f"Defect Description: {defect_desc_details[0]['description']}")
            else: # Try PhysicalChange if not found on Deterioration
                query_defect_pc_desc = """
                OPTIONAL MATCH (pc:PhysicalChange {name: $defect_name})
                RETURN pc.detailedDescription AS description
                LIMIT 1
                """
                defect_pc_desc_details = self.cypher(query_defect_pc_desc, {"defect_name": defect_name})
                if defect_pc_desc_details and defect_pc_desc_details[0] and defect_pc_desc_details[0].get("description"):
                     context_parts.append(f"Defect Description: {defect_pc_desc_details[0]['description']}")


        if method_names:
            context_parts.append("--- NDT Method Details ---")
            for method_name in method_names:
                query_method = """
                MATCH (n:NDTMethod {name: $method_name})
                RETURN n.description AS description,
                       n.costEstimate AS costEstimate,
                       n.methodCategory AS methodCategory,
                       n.detectionCapabilities AS detectionCapabilities,
                       n.applicableMaterialsNote AS applicableMaterialsNote,
                       n.methodLimitations AS methodLimitations
                LIMIT 1
                """
                method_details = self.cypher(query_method, {"method_name": method_name})
                if method_details and method_details[0]:
                    m_details = method_details[0]
                    context_parts.append(f"Method: {method_name}")
                    if m_details.get("description"):
                        context_parts.append(f"  Description: {m_details['description']}")
                    if m_details.get("methodCategory"):
                        context_parts.append(f"  Category: {m_details['methodCategory']}")
                    if m_details.get("costEstimate"):
                        context_parts.append(f"  Cost Estimate: {m_details['costEstimate']}")
                    if m_details.get("detectionCapabilities"):
                        context_parts.append(f"  Detection Capabilities: {m_details['detectionCapabilities']}")
                    if m_details.get("applicableMaterialsNote"):
                        context_parts.append(f"  Applicable Materials Note: {m_details['applicableMaterialsNote']}")
                    if m_details.get("methodLimitations"):
                        context_parts.append(f"  Method Limitations: {m_details['methodLimitations']}")

        if not context_parts:
            return "No specific details found in KG for the provided entities."

        return "\n".join(context_parts)
