from typing import Dict, List

from rdflib import Literal, Namespace, Graph, URIRef
from rdflib.namespace import SKOS, RDF

from dgfisma_rdf.shared.rdf_dgfisma import NS_BASE

CONCEPT_BASE = Namespace(NS_BASE + 'concepts/')
EN = 'en'


class ConceptGraph(Graph):
    """
    Concepts RDF Graph
    """

    def __init__(self, *args, **kwargs):
        """ Looks quite clean if implemented with RDFLib https://github.com/RDFLib/rdflib
        Ontology can be visualised with http://www.visualdataweb.de/webvowl/

        Args:
            *args:
            **kwargs:
        """
        super(ConceptGraph, self).__init__(
            *args, **kwargs)

        self.bind("skos", SKOS)

        self.uid_iterator = UIDIterator()

    def add_terms(self, l_terms: List[str], l_def: List[str] = None, lang=EN):
        """ Add new terms to the RDF as SKOS concepts.

        Args:
            l_terms: List of the terms in string format
            l_def: Optional. List with definitions alongside the terms. If bool(term_i) is False, it is not added.
            lang: optional language parameter of the terms.

        Returns:
            list of RDF URI's of the new SKOS concepts.
        """

        l_terms = list(map(str, l_terms))  #

        if l_def is not None:
            assert len(l_terms) == len(l_def), "Terms and definitions should have the same length."

        l_uri = [None for _ in l_terms]  # Initialisation
        for i, term_i in enumerate(l_terms):
            node_term_i = self.uid_iterator.get_next()

            l_uri[i] = node_term_i

            self.add((node_term_i,
                      RDF.type,
                      SKOS.Concept
                      ))

            self.add((node_term_i,
                      SKOS.prefLabel,
                      Literal(term_i, lang=lang)
                      ))

            if l_def is not None:
                def_i = l_def[i]
                if bool(def_i):
                    self.add((node_term_i,
                              SKOS.definition,
                              Literal(def_i, lang=lang)
                              ))

        return l_uri


class LinkConceptGraph(ConceptGraph):
    """
    Builds further on a concept Graph but can be seen solely to add relationships between different glossaries
    """

    def add_similar_terms(self, sim_terms=Dict[str, List[str]]):
        """

        Args:
            sim_terms: Dictionary for similar term matches with the URI's of the

        Returns:
            None
        """

        for uri_i, l_matches_uri in sim_terms.items():
            for uri_j in l_matches_uri:
                self.add((URIRef(uri_i),
                          SKOS.relatedMatch,
                          URIRef(uri_j)
                          ))


class UIDIterator:
    def __init__(self, base=CONCEPT_BASE):
        self.i = 0
        self.base = base

    def get_next(self):
        return next(self)

    def __next__(self):
        node = self.base[str(self.i)]
        self.i += 1
        return node
