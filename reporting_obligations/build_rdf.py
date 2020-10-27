import os

from rdflib import URIRef, BNode, Literal, Namespace, Graph
from rdflib.namespace import SKOS, RDF

from reporting_obligations.cas_parser import CasContent, KEY_CHILD, KEY_SENTENCE_FRAG_CLASS

# TODO find good URI base
NS_BASE = Namespace("http://dgfisma.com/")
RO_BASE = Namespace(NS_BASE + 'reporting_obligation/')
ONT_BASE = Namespace(NS_BASE + 'ontology/reporting_obligations#')

MOCKUP_FILENAME = 'reporting_obligations_mockup.rdf'


def main(l: CasContent):
    """ Build an RDF.
    Looks quite clean if implemented with RDFLib https://github.com/RDFLib/rdflib

    :param l: CasContent dictionary
    :return:
    """

    g = Graph()
    g.bind("skos", SKOS)
    g.bind("dgf", NS_BASE)

    # new classes
    # class_cat_doc = URIRef(ONT_BASE + 'CatalogueDocument')
    class_cat_doc = URIRef(base=ONT_BASE, value='CatalogueDocument')
    class_rep_obl = URIRef(base=ONT_BASE, value='ReportingObligation')
    has_rep_obl = URIRef(base=ONT_BASE, value='hasReportingObligation')

    # TODO in a test keys should be checked with what comes out of cas!
    # FROM https://github.com/CrossLangNV/DGFISMA_reporting_obligations
    d_entities = {'ARG0': URIRef(base=ONT_BASE, value='hasReporter'),
                  'ARG1': URIRef(base=ONT_BASE, value='hasReport'),
                  'ARG2': URIRef(base=ONT_BASE, value='hasRegulatoryBody'),
                  'ARG3': URIRef(base=ONT_BASE, value='hasDetails'),

                  'V': URIRef(base=ONT_BASE, value='hasVerb'),  # TODO

                  'ARGM-TMP': URIRef(base=ONT_BASE, value='hasPropTmp'),
                  'ARGM-LOC': URIRef(base=ONT_BASE, value='hasPropLoc'),
                  'ARGM-CAU': URIRef(base=ONT_BASE, value='hasPropCau'),
                  'ARGM-EXT': URIRef(base=ONT_BASE, value='hasPropExt'),
                  'ARGM-MNR': URIRef(base=ONT_BASE, value='hasPropMnr'),
                  'ARGM-PNC': URIRef(base=ONT_BASE, value='hasPropPnc'),
                  'ARGM-ADV': URIRef(base=ONT_BASE, value='hasPropAdv'),
                  'ARGM-DIR': URIRef(base=ONT_BASE, value='hasPropDir'),
                  'ARGM-NEG': URIRef(base=ONT_BASE, value='hasPropNeg'),
                  'ARGM-MOD': URIRef(base=ONT_BASE, value='hasPropMod'),
                  'ARGM-DIS': URIRef(base=ONT_BASE, value='hasPropDis'),
                  }

    # add a document
    # TODO get rid of BNodes
    # cat_doc = URIRef(base=RO_BASE + 'catalogue_document/', value=_serial_number_generator()())
    cat_doc = BNode()

    g.add((cat_doc, RDF.type, class_cat_doc))

    # iterate over reporting obligations (RO's)
    list_ro = l[KEY_CHILD]
    for ro_i in list_ro:

        # TODO get rid of BNodes # rep_obl_i = BNode(_prefix=RO_BASE + 'reporting_obligation/')
        rep_obl_i = BNode()
        g.add((rep_obl_i, RDF.type, class_rep_obl))
        # link to catalog document
        g.add((cat_doc, has_rep_obl, rep_obl_i))

        # iterate over different entities of RO
        for ent_i in ro_i:
            # TODO instead of saving everything as skos, make distinctions?

            # TODO get rid of BNodes # concept_i = BNode(_prefix=RO_BASE + 'entity/')
            concept_i = BNode()
            # type definition
            g.add((concept_i, RDF.type, SKOS.Concept))
            # Add the string representation
            value_i = Literal(ent_i[KEY_CHILD], lang='en')
            g.add((concept_i, SKOS.prefLabel, value_i))

            # TODO
            # The link with RO defines the class of the entity

            pred_i = d_entities.get(ent_i[KEY_SENTENCE_FRAG_CLASS])

            if pred_i is None:
                # Unknown property/entity class
                # TODO catch in an other way?

                pred_i = URIRef(base=ONT_BASE, value='hasEntity')

            g.add((rep_obl_i, pred_i, concept_i))

    # XML = RDF
    print(g.serialize(format="pretty-xml").decode("utf-8"))
    if 1:  # save
        g.serialize(destination=MOCKUP_FILENAME, format="pretty-xml")

    return g


def example_querying():
    g = Graph()

    # ... add some triples to g somehow ...
    g.parse(MOCKUP_FILENAME)

    if 1:
        get_all(g)

    if 1:
        entity_classes = get_different_entities(g)

        for entity_class in entity_classes:
            l_values = get_all_from_class(g, entity_class)
            print(f'class: {entity_class}')
            print('\t', l_values)

    return


def get_all(g: Graph):
    q = """
        SELECT ?subject ?predicate ?object
        WHERE {

             {  {?subject ?predicate ?object .}
           }
        }
    """

    qres = g.query(q)
    for row in qres:
        print(*row)


def get_different_entities(g: Graph):
    q = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dgf: <http:/dgfisma.com/>
        PREFIX dgfo: <http:/dgfisma.com/ontology/>

        SELECT DISTINCT ?predicate 

        WHERE {
            ?subject ?predicate ?object ;
            rdf:type dgfo:ReportingObligation .
            ?object rdf:type skos:Concept
        }

    """

    qres = g.query(q)

    for row in qres:
        a, *_ = row
        print(*row)

    entity_classes = [ent_class for ent_class, *_ in qres]
    return entity_classes


def get_all_from_class(g: Graph, sentence_segment_class):
    q = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dgfo: <http:/dgfisma.com/ontology/>

        SELECT DISTINCT ?value

        WHERE {{
            ?reOb <{sentence_segment_class}> ?seg .
            ?seg rdf:type skos:Concept ;
                skos:prefLabel ?value
        }}
    """

    qres = g.query(q)

    l_values = [v for v, *_ in qres]

    return l_values


if __name__ == '__main__':
    # TODO start from cas
    folder_cas = 'reporting_obligations/output_reporting_obligations'
    # filename_cas = 'cas_laurens.xml'
    filename_cas = 'ro + html2text.xml'  # 17 RO's0
    rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'

    # from ROOT
    path_cas = os.path.join(os.path.dirname(__file__), '..', folder_cas, filename_cas)
    path_typesystem = os.path.join(os.path.dirname(__file__), '..', rel_path_typesystem)

    l = CasContent.from_cas(path_cas, path_typesystem)

    b = 1
    if b:  # already processed
        main(l)

    example_querying()
