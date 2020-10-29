# RDF ontology


## TODO's
* [build_rdf.py](./build_rdf.py)
    * [ ] Decide on Namespace for DGFISMA reporting obligations.
    * [ ] index documents and reporting obligations. They are saved as *blank nodes*.
    * [x] catch if sentence segment (e.g. Report, Frequency, RegulatoryBody) has no known representation.        
        e.g. ARGM-PRP, ARGM-PRD.
        
        This is now solved by linking directly to a SKOS:Concept through hasEntity predicate. 