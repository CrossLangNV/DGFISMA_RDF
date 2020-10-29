import abc
import os
from typing import Iterable

import rdflib

ROOT = os.path.join(os.path.dirname(__file__), '..')


class GraphWrapper(abc.ABC):
    """
    Abstract method for accessing RDF's for querying.
    """

    @abc.abstractmethod
    def query(self, q: str) -> Iterable[tuple]:
        """

        Args:
            q: SPARQL query string

        Returns:
            Iterable with tuples of query results.
        """
        pass


class RDFLibGraphWrapper(GraphWrapper):
    def __init__(self, path_rdf):
        super(RDFLibGraphWrapper, self).__init__()
        g = rdflib.Graph()
        g.parse(path_rdf)

        self.g = g

    def query(self, q):
        qres = self.g.query(q)

        return qres


class SPARQLGraphWrapper(GraphWrapper):
    def __init__(self, endpoint):
        raise NotImplementedError()

        # TODO connect to endpoint to allow querying

    def query(self, q: str) -> Iterable[tuple]:
        raise NotImplementedError()


class SPARQLReportingObligationProvider:
    def __init__(self, graph_wrapper: GraphWrapper):
        self.graph_wrapper = graph_wrapper

    def get_different_entities(self):
        q = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dgfro: <http://dgfisma.com/reporting_obligation#>


            SELECT DISTINCT ?pred ?entClass
            WHERE {
                ?pred rdfs:domain dgfro:ReportingObligation .
                ?pred rdfs:range ?entClass .
                ?_ro 			rdf:type dgfro:ReportingObligation .
    
            FILTER ( EXISTS { ?entClass rdfs:subClassOf skos:Concept . } ||
                ?entClass = skos:Concept 
            )
            }
        """

        l = list(self.graph_wrapper.query(q))

        l_entity_predicates = [str(a) for a, *_ in l]

        return l_entity_predicates

    def get_all_from_type(self, type_uri,
                          distinct=False):
        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: <http://dgfisma.com/reporting_obligation#>

            SELECT {'DISTINCT' if distinct else ''} ?value

            WHERE {{
                ?ro <{type_uri}> ?ent .
    			?ent skos:prefLabel ?value
                FILTER (lang(?value) = 'en')
            }}
        """
        l = list(self.graph_wrapper.query(q))

        l_values = [str(a) for a, *_ in l]

        return l_values
