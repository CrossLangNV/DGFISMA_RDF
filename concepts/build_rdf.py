from rdflib import Literal, Namespace, Graph
from rdflib.namespace import SKOS, RDF

from reporting_obligations.build_rdf import NS_BASE

CONCEPT_BASE = Namespace(NS_BASE + 'concepts/')
LANG = 'en'


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

    def add_terms(self, l_terms, lang=LANG):
        """ Build the RDF from cas content.
        """

        for i, term_i in enumerate(l_terms):
            node_term_i = self.uid_iterator.get_next()

            self.add((node_term_i,
                      RDF.type,
                      RDF.Property
                      ))

            self.add((node_term_i,
                      SKOS.prefLabel,
                      Literal(term_i, lang=lang)
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
