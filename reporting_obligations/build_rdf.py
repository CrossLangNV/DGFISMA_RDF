from reporting_obligations import html_parser
import os
import rdflib
from rdflib import URIRef, BNode, Literal, Namespace, Graph
from rdflib.namespace import SKOS, OWL, RDF

# TODO find good URI base
NS_BASE = Namespace("http://example.org/reporting_obligations/")


def main(l):
    """ Build an RDF.
    Looks quite clean to do with RDFLib

    :param l: TODO this should probably change to an other object
    :return:
    """

    g = Graph()
    g.bind("skos", SKOS)

    # TODO change!
    type_line = URIRef(NS_BASE + 'line')
    type_string = URIRef(NS_BASE + 'string')

    # the lines
    for i, l_i in enumerate(l):
        # todo

        # URIRef(URI_BASE + f'{i}')
        n_i = BNode(_prefix=NS_BASE)

        # TODO give type
        g.add((n_i, RDF.type, type_line))
        g.add((n_i, SKOS.prefLabel, Literal(f"line {i}")))

        for j, s_j in enumerate(l_i):
            n_j = BNode(_prefix=NS_BASE)

            g.add((n_j, RDF.type, type_string))
            g.add((n_j, SKOS.prefLabel, Literal(f"string {j}")))

        pass

    print(g.serialize(format="turtle").decode("utf-8"))

    # TODO with blank nodes, double check if correct with a query.

    return g

if __name__ == '__main__':

    path_html = 'reporting_obligations/output_reporting_obligations/doc_bf4ef384-bd7a-51c8-8f7d-d2f61865d767.html'

    # from ROOT
    path_html_full = os.path.join(os.path.dirname(__file__), '..', path_html)
    l = html_parser.main(path_html_full)

    main(l)