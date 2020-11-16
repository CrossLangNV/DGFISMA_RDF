import abc
import os

import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Literal, BNode, URIRef
from typing import Iterable, List, Tuple, Dict

from reporting_obligations import build_rdf

ROOT = os.path.join(os.path.dirname(__file__), '..')


class GraphWrapper(abc.ABC):
    """
    Abstract method for accessing RDF's for querying.
    """

    @abc.abstractmethod
    def query(self, q: str) -> Iterable[Dict[str, Dict[str, str]]]:
        """

        Args:
            q: SPARQL query string

        Returns:
            Iterable with tuples of query results.
        """
        pass

    def get_column(self, l, k: str):
        """ Convert results to simpler format

        Args:
            l:
            k: key

        Returns:

        """

        return [row[k]['value'] for row in l]


class RDFLibGraphWrapper(GraphWrapper):
    def __init__(self, path_rdf):
        super(RDFLibGraphWrapper, self).__init__()
        g = rdflib.Graph()
        g.parse(path_rdf)

        self.g = g

    def query(self, q) -> List[Tuple[str]]:
        qres = self.g.query(q)

        l = []

        for binding_i in qres.bindings:

            l_i = {}
            for k, v in binding_i.items():
                t = 'literal' if isinstance(v, Literal) else (
                    'bnode' if isinstance(v, BNode) else (
                        'uri' if isinstance(v, URIRef) else None)
                )

                l_i[str(k)] = {'type': t,
                               'value': v.toPython()
                               }

            l.append(l_i)

        return l


class SPARQLGraphWrapper(GraphWrapper):
    def __init__(self, endpoint):
        self.sparql = SPARQLWrapper(endpoint)
        self.sparql.setReturnFormat(JSON)

    def query(self, q: str) -> Iterable[Dict[str, Dict[str, str]]]:
        self.sparql.setQuery(q)
        ret = self.sparql.query()
        results = ret.convert()

        l = []
        for binding_i in results["results"]["bindings"]:
            # l.append({k: v['value'] for k, v in binding_i.items()})
            # list(binding_i.keys())
            #
            # l_i = tuple(binding_i[k]['value'] for k in list(binding_i.keys()))

            l.append(binding_i)

        return l


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

        l_entity_predicates = self.graph_wrapper.get_column(l, 'pred')

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

        l_values = self.graph_wrapper.get_column(l, 'value')

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

        l_uri = self.graph_wrapper.get_column(l, 'ro_id')

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

        l_ro = self.graph_wrapper.get_column(l, 'value')

        return l_ro

    def get_filter_single(self, pred, value) -> List[str]:
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

        l_ro = self.graph_wrapper.get_column(l, 'value')

        return l_ro

    def get_filter_multiple(self, list_pred_value: List[Tuple[str]] = []) -> List[str]:
        """ Retrieve reporting obligations with a matching value for certain predicate

        Args:
            list_pred_value: List[(pred:str, value:str)]
            e.g. [ ("<pred 1>", "<value 1>"),
                    ...
                    ("<pred n>", "<value n>") ]

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

        l_ro = self.graph_wrapper.get_column(l, 'value')

        return l_ro
