"""
For reporting obligations segments could be linked with
"""
import os

from rdflib import Graph
from rdflib.namespace import SKOS

ROOT = os.path.join(os.path.dirname(__file__), "..")

MOCKUP_RDF = os.path.join(ROOT, "reporting_obligations/reporting_obligations_mockup.rdf")
# From https://op.europa.eu/en/web/eu-vocabularies/at-concept-scheme/-/resource/authority/frequency/
ATTO_FREQUENCIES = os.path.join(ROOT, "extra_features/frequencies-skos.rdf")

KEY_ANNUAL = "annual"


def main(b_save=False):
    g_rep_obl = Graph()
    g_atto = Graph()

    g_matches = Graph()

    g_rep_obl.parse(MOCKUP_RDF)
    g_atto.parse(ATTO_FREQUENCIES)

    # Get temp data
    q = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dgf: <http:/dgfisma.com/>
        PREFIX dgfo: <http:/dgfisma.com/ontology/>

        SELECT DISTINCT ?value ?segm

        WHERE {
            ?subject dgfo:hasPropTmp ?segm .
            ?segm skos:prefLabel ?value .
        }
    """

    qres = g_rep_obl.query(q)

    label_uri_temps = ((str(label), uri) for label, uri in qres)

    q_atto = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dgf: <http:/dgfisma.com/>
        PREFIX dgfo: <http:/dgfisma.com/ontology/>

        SELECT DISTINCT ?label ?concept

        WHERE {
            ?concept skos:prefLabel ?label ;
                rdf:type skos:Concept .
  
  			FILTER  (lang(?label) = "en")
        }
    """

    qres_atto = g_atto.query(q_atto)

    for row in qres_atto:
        print(row)

    atto_value_uri = {str(t): u for t, u in qres_atto}

    for label, uri in label_uri_temps:
        # annually
        if "year" in label.lower():

            g_matches.add((uri, SKOS.closeMatch, atto_value_uri[KEY_ANNUAL]))

        else:
            # TODO make link
            print("Has to be implemented")

    print(g_matches.serialize(format="pretty-xml").decode("utf-8"))
    if b_save:  # save
        g_matches.serialize(destination="matches_mockup_atto_freq.rfd", format="pretty-xml")

    return g_matches


if __name__ == "__main__":
    main()
