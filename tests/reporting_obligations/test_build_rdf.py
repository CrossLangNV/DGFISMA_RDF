import os
import tempfile
import unittest

from dgfisma_rdf.reporting_obligations.build_rdf import ROGraph, RO_BASE, OWL, RDFS, RDF
from tests.reporting_obligations.build_rdf_example import ExampleCasContent

HAS_DOC_SRC = RO_BASE.hasDocumentSource


class TestBuild(unittest.TestCase):
    def test_build(self):
        """Test is we can build and export the RDF

        Returns:

        """
        l = ExampleCasContent.build()

        g = ROGraph()

        g.add_cas_content(l, doc_id="abcd-123")

        with self.subTest("Save RDF"):
            with tempfile.TemporaryDirectory() as d:
                filename = os.path.join(d, "tmp.rdf")
                g.serialize(destination=filename, format="pretty-xml")

    def test_init_graph(self):
        """
        Check if it contains all the expected schema elements
        """

        g = ROGraph(include_schema=True)

        q = f"""
        PREFIX skos: {RO_BASE[''].n3()}
        PREFIX owl: {OWL[''].n3()}
        PREFIX rdfs: {RDFS.uri.n3()}
        
        SELECT distinct ?c
        
        WHERE {{            
              
              VALUES (?class) {{ ({OWL.Class.n3()}) ({RDFS.Class.n3()}) }} 
              
              ?c a ?class .
        }}
        """

        q = f"""
        PREFIX skos: {RO_BASE[''].n3()}
        PREFIX owl: {OWL[''].n3()}
        PREFIX rdfs: {RDFS.uri.n3()}

        SELECT distinct ?c

        WHERE {{            

              VALUES (?class) {{ ({OWL.Class.n3()}) ({RDFS.Class.n3()}) }} 

              ?c a ?class .
        }}
        """

        q_property = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT DISTINCT ?s ?r ?o
            WHERE {       
              ?s a rdf:Property
            }
        """

        q_domain = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?s ?p ?o
            WHERE {       
                BIND (rdfs:domain as ?p) 
                ?s ?p ?o.
            }
        """

        q_range = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?s ?p ?o
            WHERE {       
                BIND (rdfs:range as ?p) 
                ?s ?p ?o.
            }
        """

        l_cls = list(map(lambda x: x[0], g.query(q)))

        l_prop = list(map(lambda x: x[0], g.query(q_property)))

        l_domain_spo = list(g.query(q_domain))
        l_range_spo = list(g.query(q_range))

        l_domain_s = list(map(lambda spo: spo[0], l_domain_spo))
        l_domain_o = list(map(lambda spo: spo[2], l_domain_spo))
        l_range_s = list(map(lambda spo: spo[0], l_range_spo))
        l_range_o = list(map(lambda spo: spo[2], l_range_spo))

        with self.subTest("Has Catalogue Document"):
            self.assertIn(RO_BASE.CatalogueDocument, l_cls)

        with self.subTest("Has Reporting obligations"):
            self.assertIn(RO_BASE.ReportingObligation, l_cls)

        with self.subTest("Has (website) source"):
            self.assertIn(RO_BASE.DocumentSource, l_cls)

        with self.subTest("Has has_doc_source"):
            self.assertIn(HAS_DOC_SRC, l_prop)

            self.assertIn(HAS_DOC_SRC, l_domain_s)
            self.assertTrue(
                list(
                    filter(
                        lambda xy: (xy[0] == HAS_DOC_SRC) and (xy[1] == RO_BASE.CatalogueDocument),
                        zip(l_domain_s, l_domain_o),
                    )
                )
            )

            self.assertIn(HAS_DOC_SRC, l_range_s)
            self.assertTrue(
                list(
                    filter(
                        lambda xy: (xy[0] == HAS_DOC_SRC) and (xy[1] == RO_BASE.DocumentSource),
                        zip(l_range_s, l_range_o),
                    )
                )
            )

        with self.subTest("Doc source label"):
            has_i = RDF.value

            self.assertIn(has_i, l_prop)

            self.assertIn(has_i, l_domain_s)
            self.assertTrue(
                list(
                    filter(
                        lambda xy: (xy[0] == has_i) and (xy[1] == RO_BASE.DocumentSource), zip(l_domain_s, l_domain_o)
                    )
                )
            )

            self.assertIn(has_i, l_range_s)
            self.assertTrue(
                list(filter(lambda xy: (xy[0] == has_i) and (xy[1] == RDFS.Literal), zip(l_range_s, l_range_o)))
            )


class TestAddDocSource(unittest.TestCase):
    def setUp(self) -> None:
        self.g = ROGraph(include_schema=True)

    def test_add_doc_source(self):
        doc_id = "https://example.com/doc1"

        source_name = "EBA"
        source_id = "https://eba.europa.eu/"

        self.g.add_doc_source(
            doc_id,
            source_id,
            source_name,
            # query_endpoint=query_endpoint
        )

        q = f"""
        SELECT DISTINCT ?s ?r ?o
        WHERE {{       
            ?s {HAS_DOC_SRC.n3()} ?o
        }}
        """

        q_get_source_name = f"""
        SELECT DISTINCT ?n
        WHERE {{       
            ?s {HAS_DOC_SRC.n3()} ?o .
            ?o {RDF.value.n3()} ?n .
        }}
        """

        l_sro = list(self.g.query(q))
        l_name = list(map(lambda x: str(x[0]), self.g.query(q_get_source_name)))

        with self.subTest("Subject"):
            self.assertTrue(list(filter(lambda sro: doc_id in sro[0], l_sro)), "subject should contain doc_id")

        with self.subTest("Object"):
            self.assertTrue(list(filter(lambda sro: source_id in sro[2], l_sro)), "object should be source id")

        with self.subTest("Name"):
            self.assertIn(source_name, l_name, "Trying to find the source name.")

    def test_remove_doc_source(self):
        n_g_start = len(self.g)

        doc_id = "https://example.com/doc1"
        source_id = "https://eba.europa.eu/"

        self.g.add_doc_source(
            doc_id,
            source_id,
        )

        self.g.remove_doc_source(doc_id, b_link_only=False)

        self.assertEqual(n_g_start, len(self.g), "Graph should be restored to previous state.")

    def test_remove_doc_source_with_source_name(self):
        n_g_start = len(self.g)

        doc_id = "https://example.com/doc1"
        source_name = "EBA"
        source_id = "https://eba.europa.eu/"

        self.g.add_doc_source(doc_id, source_id, source_name=source_name)

        self.g.remove_doc_source(doc_id, b_link_only=False)

        self.assertEqual(n_g_start, len(self.g), "Graph should be restored to previous state.")

    def test_remove_single_doc_source(self):
        n_g_start = len(self.g)

        doc_id_base = "https://example.com/doc0"

        doc_id = "https://example.com/doc1"
        source_name = "EBA"
        source_id = "https://eba.europa.eu/"

        self.g.add_doc_source(doc_id_base, source_id, source_name=source_name)
        n_g_update = len(self.g)

        self.assertLess(n_g_start, n_g_update, "Sanity check, graph should have grown.")
        self.g.add_doc_source(doc_id, source_id, source_name=source_name)

        self.assertLess(n_g_start, len(self.g), "Sanity check 2, graph should have grown.")

        self.g.remove_doc_source(doc_id)

        self.assertEqual(n_g_update, len(self.g), "Graph should be restored to previous state.")


class TestGetDocSource(unittest.TestCase):
    def setUp(self) -> None:
        self.g = ROGraph(include_schema=True)

    def test_get_one(self):
        doc_id = "https://example.com/doc1"

        source_name = "EBA"
        source_id = "https://eba.europa.eu/"

        l = self.g.get_doc_source(doc_id=doc_id)
        self.assertFalse(l)

        self.g.add_doc_source(
            doc_id,
            source_id,
            source_name,
            # query_endpoint=query_endpoint
        )

        l = self.g.get_doc_source(doc_id=doc_id)
        self.assertTrue(l)
