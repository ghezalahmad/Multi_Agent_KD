# utils/kg_exporter.py
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import XSD, OWL
from datetime import datetime
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kg_interface import KGInterface # Import for type hinting only

# Helper to create safe URI components (e.g., replace spaces, slashes)
def make_safe_uri_component(value: str) -> str:
    if not isinstance(value, str):
        value = str(value)
    # Remove or replace characters not suitable for URIs
    # This is a basic version; more robust IRI generation might be needed for production
    value = value.replace(" ", "_").replace("/", "-").replace("\\", "-")
    value = re.sub(r'[^\w\s-]', '', value) # Remove non-alphanumeric (excluding underscore, hyphen)
    return value

def export_kg_to_owl(kg_interface: 'KGInterface', output_file: str = "ndt_kg_exported.ttl"):
    g = Graph()
    NDT = Namespace("http://example.org/ndt#")
    EX = Namespace("http://example.org/instance/")  # Namespace for our individuals

    g.bind("ndt", NDT)
    g.bind("ex", EX)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)

    # 1. Define node types, their OWL classes, primary keys for URI, and properties to export
    #    (property_in_neo4j, owl_property_uri, datatype)
    node_definitions = {
        "Material": {"class": NDT.Material, "key": "name", "props": [
            ("name", NDT.name, XSD.string),
            ("description", NDT.description, XSD.string),
            ("commonApplications", NDT.commonApplications, XSD.string)
        ]},
        "Deterioration": {"class": NDT.Deterioration, "key": "name", "props": [
            ("name", NDT.name, XSD.string),
            ("detailedDescription", NDT.detailedDescription, XSD.string)
        ]},
        "DeteriorationMechanism": {"class": NDT.DeteriorationMechanism, "key": "name", "props": [
            ("name", NDT.name, XSD.string),
            ("description", NDT.description, XSD.string) # Assuming it might have one
        ]},
        "PhysicalChange": {"class": NDT.PhysicalChange, "key": "name", "props": [
            ("name", NDT.name, XSD.string),
            ("detailedDescription", NDT.detailedDescription, XSD.string)
        ]},
        "NDTMethod": {"class": NDT.NDTMethod, "key": "name", "props": [
            ("name", NDT.name, XSD.string),
            ("description", NDT.description, XSD.string),
            ("costEstimate", NDT.costEstimate, XSD.string),
            ("methodCategory", NDT.methodCategory, XSD.string),
            ("detectionCapabilities", NDT.detectionCapabilities, XSD.string),
            ("applicableMaterialsNote", NDT.applicableMaterialsNote, XSD.string),
            ("methodLimitations", NDT.methodLimitations, XSD.string)
        ]},
        "Environment": {"class": NDT.Environment, "key": "name", "props": [
            ("name", NDT.name, XSD.string),
            ("description", NDT.description, XSD.string)
        ]},
        "Sensor": {"class": NDT.Sensor, "key": "name", "props": [
            ("name", NDT.name, XSD.string),
            ("description", NDT.description, XSD.string)
        ]},
        "RiskType": {"class": NDT.RiskType, "key": "name", "props": [
            ("name", NDT.name, XSD.string),
            ("riskDescription", NDT.riskDescription, XSD.string),
            ("mitigationSuggestion", NDT.mitigationSuggestion, XSD.string)
        ]},
        "InspectionPlan": {"class": NDT.InspectionPlan, "key": "planID", "props": [
            ("planID", NDT.factId, XSD.string), # Reusing factId for planID as it's a unique string identifier
            ("text", NDT.planText, XSD.string),
            ("material", NDT.materialName, XSD.string), # Maps to inspection plan specific material name
            ("defect", NDT.defectName, XSD.string),     # Maps to inspection plan specific defect name
            ("environment", NDT.environmentName, XSD.string),# Maps to inspection plan specific env name
            ("timestamp", NDT.timestamp, XSD.dateTime)
        ]},
        "Feedback": {"class": NDT.Feedback, "key": "uuid", "props": [ # Assuming Feedback nodes have a uuid
            ("uuid", NDT.factId, XSD.string), # Or some unique ID for feedback
            ("is_helpful", NDT.isHelpful, XSD.boolean), # Assuming NDT.isHelpful, xsd:boolean
            ("comment", NDT.comment, XSD.string),       # Assuming NDT.comment
            ("timestamp", NDT.timestamp, XSD.dateTime)
        ]},
        # ProposedFact might also be exported if desired
    }

    # Process nodes
    for label, defn in node_definitions.items():
        nodes_data = kg_interface.cypher(f"MATCH (n:{label}) RETURN n")
        for record in nodes_data:
            node = record['n']
            node_key_value = node.get(defn["key"])
            if node_key_value is None:
                # kg_interface.logger.warning(f"Node of type {label} found without key '{defn['key']}'. Skipping.")
                print(f"Node of type {label} found without key '{defn['key']}'. Skipping node: {node}")
                continue

            individual_uri = EX[make_safe_uri_component(str(node_key_value))]
            g.add((individual_uri, RDF.type, defn["class"]))
            g.add((individual_uri, RDF.type, OWL.NamedIndividual)) # Declare as NamedIndividual

            for neo_prop, owl_prop, dtype in defn["props"]:
                if neo_prop in node:
                    value = node[neo_prop]
                    if value is not None:
                        # Handle Neo4j temporal types specifically for xsd:dateTime
                        if dtype == XSD.dateTime and hasattr(value, 'to_iso_format'): # Check for Neo4j DateTime object
                            g.add((individual_uri, owl_prop, Literal(value.to_iso_format(), datatype=dtype)))
                        elif dtype == XSD.dateTime and isinstance(value, str): # If already string, assume ISO
                             g.add((individual_uri, owl_prop, Literal(value, datatype=dtype)))
                        elif dtype == XSD.boolean:
                             g.add((individual_uri, owl_prop, Literal(bool(value), datatype=dtype)))
                        else:
                            g.add((individual_uri, owl_prop, Literal(str(value), datatype=dtype)))

    # 2. Define relationships to export
    # (start_label, neo4j_rel_type, end_label, owl_object_property, start_key, end_key)
    relationship_definitions = [
        ("Material", "HAS_DETERIORATION_MECHANISM", "Deterioration", NDT.hasDeteriorationMechanism, "name", "name"),
        ("Material", "HAS_DETERIORATION_MECHANISM", "DeteriorationMechanism", NDT.hasDeteriorationMechanism, "name", "name"),
        ("DeteriorationMechanism", "CAUSES_PHYSICAL_CHANGE", "PhysicalChange", NDT.causesPhysicalChange, "name", "name"),
        ("Deterioration", "DETECTED_BY", "NDTMethod", NDT.detectedBy, "name", "name"),
        ("PhysicalChange", "DETECTED_BY", "NDTMethod", NDT.detectedBy, "name", "name"),
        ("Sensor", "RECOMMENDED_FOR", "NDTMethod", NDT.recommendedFor, "name", "name"),
        ("NDTMethod", "REQUIRES_ENVIRONMENT", "Environment", NDT.requiresEnvironment, "name", "name"),
        ("NDTMethod", "HAS_POTENTIAL_RISK", "RiskType", NDT.hasPotentialRisk, "name", "name"),
        # Assuming Feedback nodes have a 'uuid' property and InspectionPlan has 'planID'
        # And a relationship [:REFERS_TO_PLAN] exists from Feedback to InspectionPlan
        # If Feedback node does not have a unique key, this will be problematic.
        # We need a consistent way to get Feedback node's key. Let's assume 'uuid' for Feedback.
        ("Feedback", "REFERS_TO_PLAN", "InspectionPlan", NDT.refersToPlan, node_definitions["Feedback"]["key"], node_definitions["InspectionPlan"]["key"]),
    ]

    # Add a placeholder for NDT.refersToPlan if not in ontology (for export to proceed)
    # In a real scenario, the ontology should be updated.
    if not hasattr(NDT, "refersToPlan"): NDT.refersToPlan = NDT["refersToPlan"]
    if not hasattr(NDT, "isHelpful"): NDT.isHelpful = NDT["isHelpful"]
    if not hasattr(NDT, "comment"): NDT.comment = NDT["comment"]


    for start_label, rel_type, end_label, owl_prop, start_key_name, end_key_name in relationship_definitions:
        query = f"""
        MATCH (a:{start_label})-[r:{rel_type}]->(b:{end_label})
        RETURN a.`{start_key_name}` AS start_node_key, b.`{end_key_name}` AS end_node_key
        """
        relations_data = kg_interface.cypher(query)
        for rel in relations_data:
            start_node_key_val = rel.get('start_node_key')
            end_node_key_val = rel.get('end_node_key')

            if start_node_key_val is None or end_node_key_val is None:
                # kg_interface.logger.warning(f"Skipping relationship {rel_type} due to missing key(s). Start: {start_node_key_val}, End: {end_node_key_val}")
                print(f"Skipping relationship {rel_type} due to missing key(s). Start: {start_node_key_val}, End: {end_node_key_val}")
                continue

            start_uri = EX[make_safe_uri_component(str(start_node_key_val))]
            end_uri = EX[make_safe_uri_component(str(end_node_key_val))]
            g.add((start_uri, owl_prop, end_uri))

    # Serialize the graph
    # Using Turtle format as it's more readable than RDF/XML
    g.serialize(destination=output_file, format="turtle")
    # kg_interface.logger.info(f"✅ Exported KG to {output_file} in Turtle format.")
    print(f"✅ Exported KG to {output_file} in Turtle format.")

if __name__ == '__main__':
    # This is a dummy example for testing the exporter directly.
    # In actual use, KGInterface instance would be passed from app/main.py
    class MockKGInterface:
        def __init__(self):
            self.nodes_data = {
                "Material": [{"n": {"name": "Concrete", "description": "A composite material", "commonApplications": "Buildings"}}],
                "Deterioration": [{"n": {"name": "Cracking", "detailedDescription": "A linear fracture"}}],
                "NDTMethod": [{"n": {"name": "Ultrasonic Testing", "description": "Uses sound waves"}}],
                "InspectionPlan": [{"n": {"planID": "plan123", "text": "Test plan", "material": "Concrete", "defect": "Cracking", "environment": "Humid", "timestamp": datetime.now()}}],
                "Feedback": [{"n": {"uuid": "fb123", "is_helpful": True, "comment": "Good plan!", "timestamp": datetime.now()}}]

            }
            self.rels_data = {
                "MATCH (a:Material)-[r:HAS_DETERIORATION_MECHANISM]->(b:Deterioration) RETURN a.`name` AS start_node_key, b.`name` AS end_node_key": [
                    {"start_node_key": "Concrete", "end_node_key": "Cracking"}
                ],
                "MATCH (a:Feedback)-[r:REFERS_TO_PLAN]->(b:InspectionPlan) RETURN a.`uuid` AS start_node_key, b.`planID` AS end_node_key": [
                     {"start_node_key": "fb123", "end_node_key": "plan123"}
                ]
            }
            # Add other queries if needed for the mock
            for key in self.rels_data: # Ensure all relationship queries are present in mock
                if "DETECTED_BY" in key: self.rels_data[key] = self.rels_data.get(key, [])
                # ... and so on for other relationship types

        def cypher(self, query: str, params: dict = None, log: bool = True):
            print(f"Mock Cypher: {query} with {params}")
            if query.startswith("MATCH (n:"):
                label = query.split(":")[1].split(")")[0].strip()
                return self.nodes_data.get(label, [])
            for rel_query_template, data in self.rels_data.items():
                # Simple match, real matching would be more complex
                if rel_query_template.split(" RETURN")[0] in query: # Check if the MATCH part is similar
                    return data
            return []

    # Create a mock KGInterface
    mock_kg = MockKGInterface()
    print("Running exporter with mock KGInterface...")
    # Define some missing NDT properties for the mock to run without ontology file access here
    NDT = Namespace("http://example.org/ndt#")
    NDT.isHelpful = NDT["isHelpful"]
    NDT.comment = NDT["comment"]
    NDT.refersToPlan = NDT["refersToPlan"]

    # export_kg_to_owl(mock_kg, "ndt_kg_mock_exported.ttl") # Comment out direct execution for now
    print("Mock export finished. Check ndt_kg_mock_exported.ttl (if uncommented).")
