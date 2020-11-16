import os

from rdflib import BNode, Literal, Namespace, Graph
from rdflib.namespace import SKOS, RDF, RDFS, OWL, URIRef, DC

from reporting_obligations.cas_parser import CasContent, KEY_CHILDREN, KEY_SENTENCE_FRAG_CLASS, KEY_VALUE

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
    class_rep_obl = RO_BASE.ReportingObligation
    # Connections
    prop_has_rep_obl = RO_BASE.hasReportingObligation
    prop_has_entity = RO_BASE.hasEntity

    def __init__(self, *args, **kwargs):
        """ Looks quite clean if implemented with RDFLib https://github.com/RDFLib/rdflib
        Ontology can be visualised with http://www.visualdataweb.de/webvowl/

        Args:
            *args:
            **kwargs:
        """
        super(ROGraph, self).__init__(
            # identifier=RO_BASE,  # Not needed at the moment
            *args, **kwargs)

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
        def add_owl_class(cls):
            self.add((cls,
                      RDF.type,
                      RDFS.Class
                      ))
            self.add((cls,
                      RDF.type,
                      OWL.Class
                      ))

        add_owl_class(self.class_cat_doc)
        add_owl_class(self.class_rep_obl)

        # OWL properties
        self._add_property(self.prop_has_rep_obl, self.class_cat_doc, self.class_rep_obl)

        self._add_property(RDF.value,
                           self.class_rep_obl,
                           RDFS.Literal)

        self._add_property(self.prop_has_entity, self.class_rep_obl, SKOS.Concept)

        for prop, cls in D_ENTITIES.values():
            self._add_property(prop, self.class_rep_obl, cls)
            # Sub property
            self.add((prop,
                      RDFS.subPropertyOf,
                      self.prop_has_entity
                      ))
            self._add_sub_class(cls, SKOS.Concept)

    def add_cas_content(self, cas_content: CasContent):
        """ Build the RDF from cas content.
        """

        # add a document
        if 0:
            cat_doc = RO_BASE['catalogue_document/' + _serial_number_generator()()]
        elif 0:
            cat_doc = BNode()
        else:  # https://github.com/RDFLib/rdflib/pull/512#issuecomment-133857982
            cat_doc = BNode().skolemize()

        self.add((cat_doc, RDF.type, self.class_cat_doc))

        # iterate over reporting obligations (RO's)
        list_ro = cas_content[KEY_CHILDREN]
        for ro_i in list_ro:

            if 0:
                rep_obl_i = BNode(_prefix=RO_BASE + 'reporting_obligation/')
            elif 0:
                rep_obl_i = BNode()
            else:  # https://github.com/RDFLib/rdflib/pull/512#issuecomment-133857982
                rep_obl_i = BNode().skolemize()

            self.add((rep_obl_i, RDF.type, self.class_rep_obl))
            # link to catalog document + ontology
            self.add((cat_doc, self.prop_has_rep_obl, rep_obl_i))
            # add whole reporting obligation
            self.add((rep_obl_i, RDF.value, Literal(ro_i[KEY_VALUE])))

            # iterate over different entities of RO
            for ent_i in ro_i[KEY_CHILDREN]:

                if 0:
                    concept_i = BNode(_prefix=RO_BASE + 'entity/')
                elif 0:
                    concept_i = BNode()
                else:  # https://github.com/RDFLib/rdflib/pull/512#issuecomment-133857982
                    concept_i = BNode().skolemize()

                t_pred_cls = D_ENTITIES.get(ent_i[KEY_SENTENCE_FRAG_CLASS])
                if t_pred_cls is None:
                    # Unknown property/entity class
                    # TODO how to handle unknown entities?

                    print(f'Unknown sentence entity class: {ent_i[KEY_SENTENCE_FRAG_CLASS]}')

                    pred_i = self.prop_has_entity
                    cls = SKOS.Concept

                else:
                    pred_i, cls = t_pred_cls

                # type definition
                self.add((concept_i, RDF.type, cls))
                # Add the string representation
                value_i = Literal(ent_i[KEY_VALUE], lang='en')
                self.add((concept_i, SKOS.prefLabel, value_i))

                # connect entity with RO
                self.add((rep_obl_i, pred_i, concept_i))

    def _add_property(self, prop: URIRef, domain: URIRef, ran: URIRef) -> None:
        """ shared function to build all necessary triples for a property in the ontology.

        Args:
            prop:
            domain:
            ran:

        Returns:
            None
        """
        self.add((prop,
                  RDF.type,
                  RDF.Property
                  ))
        self.add((prop,
                  RDFS.domain,
                  domain
                  ))
        self.add((prop,
                  RDFS.range,
                  ran
                  ))

    def _add_sub_class(self,
                       child_cls: URIRef,
                       parent_cls: URIRef
                       ) -> None:
        self.add((child_cls,
                  RDFS.subClassOf,
                  parent_cls
                  ))


class ExampleCasContent(CasContent):
    """
    A preconfigured cas content for testing.
    """
    def __init__(self, *args, **kwargs):
        super(ExampleCasContent, self).__init__(*args, **kwargs)

        self.NUM_RO = len(self[KEY_CHILDREN])

    def get_NUM_RO(self) -> int:
        """
        Get the number of reporting obligations.

        Returns:
            integer value of number of reporting obligations
        """
        return self.NUM_RO

    @classmethod
    def build(cls) -> CasContent:
        """
            Build the example cas content

        Returns:
            The example cas content
        """
        folder_cas = 'reporting_obligations/output_reporting_obligations'
        # filename_cas = 'cas_laurens.xml'
        filename_cas = 'ro + html2text.xml'  # 17 RO's0
        rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'

        # from ROOT
        path_cas = os.path.join(ROOT, folder_cas, filename_cas)
        path_typesystem = os.path.join(ROOT, rel_path_typesystem)
        return cls.from_cas_file(path_cas, path_typesystem)


if __name__ == '__main__':

    b_build = 1
    if b_build:  # already processed
        b_save = True
        b_print = False

        g = ROGraph()

        l = ExampleCasContent.build()

        g.add_cas_content(l)

        if b_print:
            # XML = RDF
            print(g.serialize(format="pretty-xml").decode("utf-8"))

        if b_save:  # save
            g.serialize(destination=MOCKUP_FILENAME, format="pretty-xml")
