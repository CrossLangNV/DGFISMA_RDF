import abc
import logging
import os
from typing import Iterable, List, Tuple, Dict

import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Literal, BNode, URIRef

from . import build_rdf

ROOT = os.path.join(os.path.dirname(__file__), '..')

B_LOG_QUERIES = False


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

                d_i = {'type': t,
                       'value': v.toPython()
                       }

                try:
                    lang = v.language
                except AttributeError as e:
                    pass
                else:
                    d_i['xml:lang'] = lang

                l_i[str(k)] = d_i

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
        q = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dgfro: <{build_rdf.RO_BASE}>
    
            SELECT DISTINCT ?pred # ?entClass
            WHERE {{
                ?pred rdfs:domain dgfro:ReportingObligation ;
                    rdfs:range ?entClass .
       
            FILTER ( EXISTS {{ ?entClass rdfs:subClassOf skos:Concept . }} ||
                ?entClass = skos:Concept 
            )
            }}
        """

        l = list(self.graph_wrapper.query(q))

        l_entity_predicates = self.graph_wrapper.get_column(l, 'pred')

        return l_entity_predicates

    def get_all_from_type(self, type_uri,
                          distinct=True) -> List[str]:
        """

        Args:
            type_uri:
            distinct: Returning distinct elements is base behaviour

        Returns:

        """

        VALUE = 'value_ent'

        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

            SELECT {'DISTINCT' if distinct else ''} ?{VALUE}

            WHERE {{
                ?ro a {build_rdf.ROGraph.class_rep_obl.n3()} ;
                    {URIRef(type_uri).n3()} ?ent .
    			?ent skos:prefLabel ?{VALUE}
            }}
            
            ORDER BY (LCASE(?{VALUE}))
        """
        #                 FILTER (lang(?value) = 'en')
        l = list(self.graph_wrapper.query(q))

        l_values = self.graph_wrapper.get_column(l, VALUE)

        return l_values

    def get_all_ro_uri(self) -> List[str]:
        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: {build_rdf.RO_BASE[None].n3()}
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?ro_id

            WHERE {{
                ?ro_id rdf:type {build_rdf.ROGraph.class_rep_obl.n3()} .
            }}
            """
        l = self.graph_wrapper.query(q)

        l_uri = self.graph_wrapper.get_column(l, 'ro_id')

        return l_uri

    def get_all_ro_str(self):
        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: {build_rdf.RO_BASE[None].n3()}
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?value ?ro_id

            WHERE {{
                ?ro_id rdf:type {build_rdf.ROGraph.class_rep_obl.n3()} ;
                    rdf:value ?value
            }}
        """
        l = self.graph_wrapper.query(q)

        l_ro = self.graph_wrapper.get_column(l, 'value')

        return l_ro

    def get_filter_single(self, pred, value) -> List[str]:
        """ Retrieve reporting obligations with a matching value for certain predicate

        Args:
            pred: predicate URI
            value: string to match

        Returns:
            List of reporting obligations with matching content.
        """

        return self.get_filter_multiple([(pred, value)])

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
            PREFIX dgfro: {build_rdf.RO_BASE[None].n3()}
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?value ?ro_id ?p

            WHERE {{
                ?ro_id rdf:type {build_rdf.ROGraph.class_rep_obl.n3()} ;
                    rdf:value ?value .
            """

        for i, (pred, value) in enumerate(list_pred_value):
            q_i = f"""
                ?ro_id  <{pred}> ?ent{i} .
                    ?ent{i} skos:prefLabel ?p{i} .
                    FILTER (lcase(str(?p{i})) =lcase({Literal(value).n3()}))
            """
            #         FILTER (lang(?p{i}) = "en"   )

            q += q_i

        q += f"""
        }}
        """

        if B_LOG_QUERIES:
            logging.info(q)

        l = self.graph_wrapper.query(q)

        l_ro = self.graph_wrapper.get_column(l, 'value')

        return l_ro

    def get_filter_ro_id_multiple(self, list_pred_value: List[Tuple[str]] = [],
                                  limit=None,
                                  offset=0) -> List[str]:
        """ Retrieve reporting obligations UID's with a matching value for certain predicate

        Args:
            list_pred_value: List[(pred:str, value:str)]
            e.g. [ ("<pred 1>", "<value 1>"),
                    ...
                    ("<pred n>", "<value n>") ]
            limit: number of id's to return
            offset: what index to start from (counting from 0)

        Returns:
            List with URI's of the Reporting obligations.
        """

        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: {build_rdf.RO_BASE[None].n3()}
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT DISTINCT ?ro_id

            WHERE {{
                ?ro_id rdf:type {build_rdf.ROGraph.class_rep_obl.n3()} ;
                   rdf:value ?value .
            """

        for i, (pred, value) in enumerate(list_pred_value):
            q_i = f"""
                     ?ro_id {URIRef(pred).n3()} ?ent{i} .
                        ?ent{i} skos:prefLabel ?p{i} .
                                FILTER (
                                    lcase(str(?p{i})) =lcase({Literal(value).n3()})
                                )
            """

            q += q_i

        q += f"""
        }}
        
        ORDER BY (LCASE(?value))

        """

        if limit is not None:
            q += f"""LIMIT {limit}"""

        if offset:
            q += f"""OFFSET {offset}"""

        if B_LOG_QUERIES:
            logging.info(q)

        l = self.graph_wrapper.query(q)

        l_ro_id = self.graph_wrapper.get_column(l, 'ro_id')

        return l_ro_id

    def get_filter_entities(self,
                            list_pred_value: List[Tuple[str]] = [],
                            distinct=True):
        """ Return all entities per type based on filters

        Args:
            list_pred_value: Filters to apply similar to get_filter_ro_id_multiple.
            distinct:

        Returns:

        """

        VALUE = 'value_ent'
        PRED = 'pred'
        COUNT = 'count'

        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: {build_rdf.RO_BASE[None].n3()}
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT {'DISTINCT' if distinct else ''} ?{PRED} ?{VALUE} (count(?ro_id) as ?{COUNT})

            WHERE {{
                ?ro_id rdf:type {build_rdf.ROGraph.class_rep_obl.n3()} ;
                    ?{PRED} ?ent .
                ?ent skos:prefLabel ?{VALUE} .
            """

        for i, (pred, value) in enumerate(list_pred_value):
            q_i = f"""
                       ?ro_id {URIRef(pred).n3()} ?ent{i} .
                          ?ent{i} skos:prefLabel ?p{i} .
                                  FILTER (
                                      lcase(str(?p{i})) =lcase({Literal(value).n3()})
                                  )
              """

            q += q_i

        q += f"""
            }}
            
            GROUPBY ?{PRED} ?{VALUE}
    
            ORDER BY (LCASE(?{PRED})) (LCASE(?{VALUE}))

        """

        l = list(self.graph_wrapper.query(q))

        d_filtered_ents = {}
        for l_i in l:
            ent_i = l_i.get(PRED).get('value')

            d_filtered_ents.setdefault(ent_i, []).append({VALUE: l_i.get(VALUE).get('value'),
                                                          COUNT: l_i.get(COUNT).get('value')})

        return d_filtered_ents

    def get_filter_entities_from_type(self,
                                      type_uri,
                                      list_pred_value: List[Tuple[str]] = [],
                                      distinct=True):
        """

        Args:
            type_uri: from which type of entity to return entities of.
            list_pred_value: Filters to apply similar to get_filter_ro_id_multiple.
            distinct:

        Returns:

        """

        VALUE = 'value_ent'

        q = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX dgfro: {build_rdf.RO_BASE[None].n3()}
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
            # SELECT DISTINCT ?ro_id
            SELECT {'DISTINCT' if distinct else ''} ?{VALUE}

            WHERE {{
                ?ro_id rdf:type {build_rdf.ROGraph.class_rep_obl.n3()} ;
                    rdf:value ?value ;
                    {URIRef(type_uri).n3()} ?ent .
                ?ent skos:prefLabel ?{VALUE} .
            """

        for i, (pred, value) in enumerate(list_pred_value):
            q_i = f"""
                       ?ro_id {URIRef(pred).n3()} ?ent{i} .
                          ?ent{i} skos:prefLabel ?p{i} .
                                  FILTER (
                                      lcase(str(?p{i})) =lcase({Literal(value).n3()})
                                  )
              """

            q += q_i

        q += f"""
          }}

          ORDER BY (LCASE(?{VALUE}))

          """

        l = list(self.graph_wrapper.query(q))
        l_values = self.graph_wrapper.get_column(l, VALUE)

        return l_values
