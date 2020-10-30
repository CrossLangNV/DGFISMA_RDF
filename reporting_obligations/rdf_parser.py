import abc
import os
from typing import Iterable, List, Tuple
from reporting_obligations import build_rdf

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
                          distinct=False) -> List[str]:
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

    def get_all_ro_uri(self) -> List[str]:
        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: <http://dgfisma.com/reporting_obligation#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?ro_id

            WHERE {{
                ?ro_id rdf:type <{build_rdf.ROGraph.class_rep_obl}> .
            }}
            """
        l = self.graph_wrapper.query(q)

        l_uri = [str(a) for a, *_ in l]

        return l_uri

    def get_all_ro_str(self):

        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: <http://dgfisma.com/reporting_obligation#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?value ?ro_id

            WHERE {{
                ?ro_id rdf:type <{build_rdf.ROGraph.class_rep_obl}> ;
                    rdf:value ?value
            }}
        """
        l = self.graph_wrapper.query(q)

        l_ro = [str(a) for a, *_ in l]

        return l_ro

    def get_filter_single(self, pred, value):
        """ Retrieve reporting obligations with a matching value for certain predicate

        Args:
            pred:
            value:

        Returns:

        """

        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: <http://dgfisma.com/reporting_obligation#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?value ?ro_id ?p

            WHERE {{
                ?ro_id rdf:type <{build_rdf.ROGraph.class_rep_obl}> ;
                    rdf:value ?value ;
                    <{pred}> ?ent .
                ?ent skos:prefLabel ?p
                FILTER (lang(?p) = "en"   )
                FILTER ( str(?p) ="{value}"    )
            }}
        """
        l = self.graph_wrapper.query(q)

        l_ro = [str(a) for a, *_ in l]

        return l_ro

    def get_filter_multiple(self, list_pred_value:List[Tuple[str]] = []):
        """ Retrieve reporting obligations with a matching value for certain predicate

        Args:
            list_pred_value: List[(pred:str, value:str)]

        Returns:

        """

        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: <http://dgfisma.com/reporting_obligation#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?value ?ro_id ?p

            WHERE {{
                ?ro_id rdf:type <{build_rdf.ROGraph.class_rep_obl}> ;
                   rdf:value ?value .

            """

        for i, (pred, value) in enumerate(list_pred_value):
            q_i = f"""
                     ?ro_id  <{pred}> ?ent{i} .
                        ?ent{i} skos:prefLabel ?p{i} .
                                FILTER (lang(?p{i}) = "en"   )
                                FILTER ( str(?p{i}) ="{value}"    )
            """

            q += q_i

        q += f"""
        }}
        """

        l = self.graph_wrapper.query(q)

        l_ro = [str(a) for a, *_ in l]

        return l_ro