# utils/shacl_validator.py
from pyshacl import validate
from rdflib import Graph

def validate_owl_with_shacl(data_file, shacl_file):
    data_graph = Graph().parse(data_file)
    shacl_graph = Graph().parse(shacl_file)
    
    conforms, results_graph, results_text = validate(
        data_graph=data_graph,
        shacl_graph=shacl_graph,
        inference='rdfs',
        debug=False
    )
    
    return conforms, results_text
