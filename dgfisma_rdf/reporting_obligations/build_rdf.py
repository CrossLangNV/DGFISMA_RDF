import os

from rdflib import BNode, Literal, Namespace, Graph
from rdflib.namespace import SKOS, RDF, RDFS, OWL, URIRef, DC
from rdflib.term import _serial_number_generator

from .cas_parser import CasContent, KEY_CHILDREN, KEY_SENTENCE_FRAG_CLASS, KEY_VALUE
from ..shared.rdf_dgfisma import NS_BASE

RO_BASE = Namespace(NS_BASE + 'reporting_obligations/')

ROOT = os.path.join(os.path.dirname(__file__), '../..')
MOCKUP_FILENAME = os.path.join(ROOT, 'data/examples', 'reporting_obligations_mockup.rdf')
folder_cas = 'dgfisma_rdf/reporting_obligations/output_reporting_obligations'
# filename_cas = 'cas_laurens.xml'
PATH_CAS = os.path.join(ROOT, folder_cas, 'ro + html2text.xml')  # 17 RO's0
PATH_TYPESYSTEM = os.path.join(ROOT, folder_cas, 'typesystem_tmp.xml')
for PATH in (MOCKUP_FILENAME, PATH_CAS, PATH_TYPESYSTEM):
    assert os.path.exists(PATH), os.path.abspath(PATH)

# FROM https://github.com/CrossLangNV/DGFISMA_reporting_obligations
D_ENTITIES = {'ARG0': (RO_BASE['hasReporter'], RO_BASE['Reporter']),
              'ARG1': (RO_BASE['hasReport'], RO_BASE['Report']),
              'ARG2': (RO_BASE['hasRegulatoryBody'], RO_BASE['RegulatoryBody']),
              'ARG3': (RO_BASE['hasDetails'], RO_BASE['Details']),

              'V': (RO_BASE['hasVerb'], RO_BASE['Verb']),  # Pivot verb

              # http://clear.colorado.edu/compsem/documents/propbank_guidelines.pdf
              'ARGM-TMP': (RO_BASE['hasPropTmp'], RO_BASE['PropTmp']),
              'ARGM-LOC': (RO_BASE['hasPropLoc'], RO_BASE['PropLoc']),  # Locatives
              'ARGM-CAU': (RO_BASE['hasPropCau'], RO_BASE['PropCau']),
              'ARGM-EXT': (RO_BASE['hasPropExt'], RO_BASE['PropExt']),
              'ARGM-MNR': (RO_BASE['hasPropMnr'], RO_BASE['PropMnr']),
              'ARGM-PNC': (RO_BASE['hasPropPnc'], RO_BASE['PropPnc']),
              'ARGM-ADV': (RO_BASE['hasPropAdv'], RO_BASE['PropAdv']),
              'ARGM-DIR': (RO_BASE['hasPropDir'], RO_BASE['PropDir']),  # Directional
              'ARGM-NEG': (RO_BASE['hasPropNeg'], RO_BASE['PropNeg']),
              'ARGM-MOD': (RO_BASE['hasPropMod'], RO_BASE['PropMod']),  # Modals
              'ARGM-DIS': (RO_BASE['hasPropDis'], RO_BASE['PropDis']),  # Discourse
              'ARGM-PRP': (RO_BASE['hasPropPrp'], RO_BASE['PropPrp']),  # Purpose
              'ARGM-PRD': (RO_BASE['hasPropPrd'], RO_BASE['PropPrd']),  # Secondary Predication
              # Unused until proven, added for completeness
              'ARGM-COM': (RO_BASE['hasPropCom'], RO_BASE['PropCom']),  # Comitatives
              'ARGM-GOL': (RO_BASE['hasPropGol'], RO_BASE['PropGol']),  # Goal
              'ARGM-REC': (RO_BASE['hasPropRec'], RO_BASE['PropRec']),  # Reciprocals
              'ARGM-DSP': (RO_BASE['hasPropDsp'], RO_BASE['PropDsp']),  # Direct Speech
              'ARGM-LVB': (RO_BASE['hasPropLVB'], RO_BASE['PropLvb']),  # Light Verb
              }

PROP_HAS_ENTITY = RO_BASE.hasEntity


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

        self._add_property(PROP_HAS_ENTITY, self.class_rep_obl, SKOS.Concept)

        for prop, cls in D_ENTITIES.values():
            self._add_property(prop, self.class_rep_obl, cls)
            # Sub property
            self.add((prop,
                      RDFS.subPropertyOf,
                      PROP_HAS_ENTITY
                      ))
            self._add_sub_class(cls, SKOS.Concept)

    def add_cas_content(self, cas_content: CasContent):
        """ Build the RDF from cas content.
        """

        # add a document
        cat_doc = get_UID_node(info='cat_doc_')

        self.add((cat_doc, RDF.type, self.class_cat_doc))
        cas_content['id'] = cat_doc.toPython()  # adding ID to cas

        # iterate over reporting obligations (RO's)
        list_ro = cas_content[KEY_CHILDREN]
        for i, ro_i in enumerate(list_ro):

            rep_obl_i = get_UID_node(info='rep_obl_')

            self.add((rep_obl_i, RDF.type, self.class_rep_obl))
            # link to catalog document + ontology
            self.add((cat_doc, self.prop_has_rep_obl, rep_obl_i))
            # add whole reporting obligation
            self.add((rep_obl_i, RDF.value, Literal(ro_i[KEY_VALUE])))
            cas_content[KEY_CHILDREN][i]['id'] = rep_obl_i.toPython()  # adding ID to cas

            # iterate over different entities of RO
            for j, ent_j in enumerate(ro_i[KEY_CHILDREN]):

                concept_j = get_UID_node(info='entity_')

                t_pred_cls = D_ENTITIES.get(ent_j[KEY_SENTENCE_FRAG_CLASS])
                if t_pred_cls is None:
                    # Unknown property/entity class
                    # TODO how to handle unknown entities?

                    print(f'Unknown sentence entity class: {ent_j[KEY_SENTENCE_FRAG_CLASS]}')

                    pred_i = PROP_HAS_ENTITY
                    cls = SKOS.Concept

                else:
                    pred_i, cls = t_pred_cls

                # type definition
                self.add((concept_j, RDF.type, cls))
                # Add the string representation
                value_i = Literal(ent_j[KEY_VALUE], lang='en')
                self.add((concept_j, SKOS.prefLabel, value_i))

                # connect entity with RO
                self.add((rep_obl_i, pred_i, concept_j))

                cas_content[KEY_CHILDREN][i][KEY_CHILDREN][j]['id'] = concept_j.toPython()  # adding ID to cas

        return cas_content

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

        return cls.from_cas_file(PATH_CAS, PATH_TYPESYSTEM)


def get_UID_node(base=RO_BASE, info=None):
    """ Shared function to generate nodes that need a unique ID.
    ID is randomly generated.

    Args:
        base: used namespace
        info: info to add to the ID.

    Returns:
        a URI or BNode
    """
    if 1:
        node = base[info + _serial_number_generator()()]
    elif 0:  # blank nodes
        node = BNode()
    else:  # https://github.com/RDFLib/rdflib/pull/512#issuecomment-133857982
        node = BNode().skolemize()

    return node
