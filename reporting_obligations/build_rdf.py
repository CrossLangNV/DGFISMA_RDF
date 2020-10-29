import os

from rdflib import BNode, Literal, Namespace, Graph
from rdflib.namespace import SKOS, RDF, RDFS, OWL, URIRef, DC

from reporting_obligations.cas_parser import CasContent, KEY_CHILD, KEY_SENTENCE_FRAG_CLASS

NS_BASE = Namespace("http://dgfisma.com/")
RO_BASE = Namespace(NS_BASE + 'reporting_obligation#')

ROOT = os.path.join(os.path.dirname(__file__), '..')
MOCKUP_FILENAME = os.path.join(ROOT, 'data/examples', 'reporting_obligations_mockup.rdf')

# FROM https://github.com/CrossLangNV/DGFISMA_reporting_obligations
D_ENTITIES = {'ARG0': (RO_BASE['hasReporter'], RO_BASE['Reporter']),
              'ARG1': (RO_BASE['hasReport'], RO_BASE['Report']),
              'ARG2': (RO_BASE['hasRegulatoryBody'], RO_BASE['RegulatoryBody']),
              'ARG3': (RO_BASE['hasDetails'], RO_BASE['Details']),

              'V': (RO_BASE['hasVerb'], RO_BASE['Verb']),

              'ARGM-TMP': (RO_BASE['hasPropTmp'], RO_BASE['PropTmp']),
              'ARGM-LOC': (RO_BASE['hasPropLoc'], RO_BASE['PropLoc']),
              'ARGM-CAU': (RO_BASE['hasPropCau'], RO_BASE['PropCau']),
              'ARGM-EXT': (RO_BASE['hasPropExt'], RO_BASE['PropExt']),
              'ARGM-MNR': (RO_BASE['hasPropMnr'], RO_BASE['PropMnr']),
              'ARGM-PNC': (RO_BASE['hasPropPnc'], RO_BASE['PropPnc']),
              'ARGM-ADV': (RO_BASE['hasPropAdv'], RO_BASE['PropAdv']),
              'ARGM-DIR': (RO_BASE['hasPropDir'], RO_BASE['PropDir']),
              'ARGM-NEG': (RO_BASE['hasPropNeg'], RO_BASE['PropNeg']),
              'ARGM-MOD': (RO_BASE['hasPropMod'], RO_BASE['PropMod']),
              'ARGM-DIS': (RO_BASE['hasPropDis'], RO_BASE['PropDis']),
              }


class ROGraph(Graph):
    """
    Reporting Obligation Graph
    """

    # Final
    # Init classes & connections
    # Classes
    class_cat_doc = RO_BASE.CatalogueDocument
    class_rep_obl = RO_BASE['ReportingObligation']
    # Connections
    prop_has_rep_obl = RO_BASE['hasReportingObligation']
    prop_has_entity = RO_BASE['hasEntity']

    def __init__(self, *args, **kwargs):
        """ Looks quite clean if implemented with RDFLib https://github.com/RDFLib/rdflib
        Ontology can be visualised with http://www.visualdataweb.de/webvowl/

        Args:
            *args:
            **kwargs:
        """
        super(ROGraph, self).__init__(*args, **kwargs)

        self.bind("skos", SKOS)
        self.bind("owl", OWL)
        self.bind("dgf", NS_BASE)
        self.bind("dgfro", RO_BASE)
        self.bind("dc", DC)

        """
        describe ontology
        """
        # header info
        ont = OWL.Ontology
        self.add((RO_BASE[''],
                  RDF.type,
                  ont
                  ))
        self.add((RO_BASE[''],
                  DC.title,
                  Literal("Reporting obligations (RO) vocabulary")))

        # OWL classes
        self.add((self.class_cat_doc,
                  RDF.type,
                  RDFS.Class
                  ))
        self.add((self.class_cat_doc,
                  RDF.type,
                  OWL.Class
                  ))

        # OWL properties
        self.add((self.prop_has_rep_obl,
                  RDF.type,
                  RDF.Property
                  ))
        self.add((self.prop_has_rep_obl,
                  RDFS.domain,
                  self.class_cat_doc
                  ))
        self.add((self.prop_has_rep_obl,
                  RDFS.range,
                  self.class_rep_obl
                  ))

        self.add_property(self.prop_has_rep_obl, self.class_cat_doc, self.class_rep_obl)

        self.add_property(self.prop_has_entity, self.class_rep_obl, SKOS.Concept)

        for prop, cls in D_ENTITIES.values():
            self.add_property(prop, self.class_rep_obl, cls)
            # Sub property
            self.add((prop,
                      RDFS.subPropertyOf,
                      self.prop_has_entity
                      ))
            self.add_sub_class(cls, SKOS.Concept)

    def add_cas_content(self, l: CasContent):
        """ Build the RDF from cas content.
        """

        # add a document
        if 0:
            cat_doc = RO_BASE['catalogue_document/' + _serial_number_generator()()]
        else:
            cat_doc = BNode()

        self.add((cat_doc, RDF.type, self.class_cat_doc))

        # iterate over reporting obligations (RO's)
        list_ro = l[KEY_CHILD]
        for ro_i in list_ro:

            if 0:
                rep_obl_i = BNode(_prefix=RO_BASE + 'reporting_obligation/')
            else:
                rep_obl_i = BNode()

            self.add((rep_obl_i, RDF.type, self.class_rep_obl))
            # link to catalog document + ontology
            self.add((cat_doc, self.prop_has_rep_obl, rep_obl_i))

            # iterate over different entities of RO
            for ent_i in ro_i:

                if 0:
                    concept_i = BNode(_prefix=RO_BASE + 'entity/')
                else:
                    concept_i = BNode()

                t_pred_cls = D_ENTITIES.get(ent_i[KEY_SENTENCE_FRAG_CLASS])
                if t_pred_cls is None:
                    # Unknown property/entity class
                    # TODO catch in an other way?

                    print(f'Unknown sentence entitity class: {ent_i[KEY_SENTENCE_FRAG_CLASS]}')

                    pred_i = RO_BASE['hasEntity']
                    cls = SKOS.Concept

                else:
                    pred_i, cls = t_pred_cls

                # type definition
                self.add((concept_i, RDF.type, cls))
                # Add the string representation
                value_i = Literal(ent_i[KEY_CHILD], lang='en')
                self.add((concept_i, SKOS.prefLabel, value_i))

                # connect entity with RO
                self.add((rep_obl_i, pred_i, concept_i))

    def add_property(self, property: URIRef, domain: URIRef, ran: URIRef) -> None:
        """ shared function to build all necessary triples for a property in the ontology.

        Args:
            g:
            property:
            domain:
            ran:

        Returns:
            None
        """
        self.add((property,
                  RDF.type,
                  RDF.Property
                  ))
        self.add((property,
                  RDFS.domain,
                  domain
                  ))
        self.add((property,
                  RDFS.range,
                  ran
                  ))

    def add_sub_class(self,
                      child_cls: URIRef,
                      parent_cls: URIRef
                      ) -> None:
        self.add((child_cls,
                  RDFS.subClassOf,
                  parent_cls
                  ))

    def get_graph(self):
        return self.g


def example_querying(filename):

    # Immediately test if parsing works
    g = Graph()
    g.parse(filename)

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

    b_build = 1
    if b_build:  # already processed
        b_save = True
        b_print = False

        g = ROGraph()

        folder_cas = 'reporting_obligations/output_reporting_obligations'
        # filename_cas = 'cas_laurens.xml'
        filename_cas = 'ro + html2text.xml'  # 17 RO's0
        rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'

        # from ROOT
        path_cas = os.path.join(ROOT, folder_cas, filename_cas)
        path_typesystem = os.path.join(ROOT, rel_path_typesystem)
        l = CasContent.from_cas(path_cas, path_typesystem)

        g.add_cas_content(l)

        if b_print:
            # XML = RDF
            print(g.serialize(format="pretty-xml").decode("utf-8"))

        if b_save:  # save
            g.serialize(destination=MOCKUP_FILENAME, format="pretty-xml")

    example_querying(MOCKUP_FILENAME)
