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

                    # Fetch and append linked risks for the NDT method
                    query_risks = """
                    MATCH (n:NDTMethod {name: $method_name})-[:hasPotentialRisk]->(r:RiskType)
                    RETURN r.name AS riskName, r.riskDescription AS riskDescription, r.mitigationSuggestion AS mitigationSuggestion
                    """
                    risks_details = self.cypher(query_risks, {"method_name": method_name}, log=False) # log=False to reduce noise for sub-queries
                    if risks_details:
                        context_parts.append(f"  Potential Risks:")
                        for risk_detail in risks_details:
                            risk_name = risk_detail.get('riskName', 'Unnamed Risk')
                            desc = risk_detail.get('riskDescription', 'No description.')
                            mitigation = risk_detail.get('mitigationSuggestion', 'None specified.')
                            context_parts.append(f"    - {risk_name}: {desc} (Mitigation: {mitigation})")

        if not context_parts:
            return "No specific details found in KG for the provided entities."

        return "\n".join(context_parts)

    # --- Methods for LLM Function Calling ---

    def get_initial_recommendations_structured(self, material: str, defect: str, environment: str) -> Dict:
        recommended_methods = self.recommend_ndt_methods(material, defect, environment) # Uses existing method
        recommended_sensors = self.recommend_sensors(defect) # Uses existing method
        return {
            "recommended_methods": recommended_methods,
            "recommended_sensors": recommended_sensors
        }

    def get_ndt_method_structured_details(self, method_name: str) -> Dict | None:
        query = """
        MATCH (n:NDTMethod {name: $method_name})
        OPTIONAL MATCH (n)-[:hasPotentialRisk]->(r:RiskType)
        RETURN n.name AS name,
               n.description AS description,
               n.costEstimate AS costEstimate,
               n.methodCategory AS methodCategory,
               n.detectionCapabilities AS detectionCapabilities,
               n.applicableMaterialsNote AS applicableMaterialsNote,
               n.methodLimitations AS methodLimitations,
               collect({riskName: r.name, riskDescription: r.riskDescription, mitigationSuggestion: r.mitigationSuggestion}) AS potential_risks
        LIMIT 1
        """
        results = self.cypher(query, {"method_name": method_name})
        if not results or not results[0] or results[0].get("name") is None: # Check if method was found
            return None

        # Clean up potential_risks: if no risks, 'collect' might return a list with one dict of nulls
        details = results[0]
        if details.get("potential_risks") and \
           len(details["potential_risks"]) == 1 and \
           all(value is None for value in details["potential_risks"][0].values()):
            details["potential_risks"] = []

        return details


    def get_material_structured_details(self, material_name: str) -> Dict | None:
        query = """
        MATCH (m:Material {name: $material_name})
        RETURN m.name AS name, m.description AS description, m.commonApplications AS commonApplications
        LIMIT 1
        """
        results = self.cypher(query, {"material_name": material_name})
        return results[0] if results and results[0].get("name") is not None else None

    def get_defect_structured_details(self, defect_name: str) -> Dict | None:
        query_det = """
        MATCH (d:Deterioration {name: $defect_name})
        RETURN d.name AS name, d.detailedDescription AS detailedDescription
        LIMIT 1
        """
        results_det = self.cypher(query_det, {"defect_name": defect_name})
        if results_det and results_det[0].get("name") is not None:
            return results_det[0]

        query_pc = """
        MATCH (pc:PhysicalChange {name: $defect_name})
        RETURN pc.name AS name, pc.detailedDescription AS detailedDescription
        LIMIT 1
        """
        results_pc = self.cypher(query_pc, {"defect_name": defect_name})
        if results_pc and results_pc[0].get("name") is not None:
            return results_pc[0]

        return None
