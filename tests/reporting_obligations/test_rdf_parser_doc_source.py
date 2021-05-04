"""
On 31/04/2021 it was decided that the document source (the website) should be added to the RDF for easier querying.

In this file, we test the ability to filter based on the website.
"""
import io
import unittest

from dgfisma_rdf.reporting_obligations.build_rdf import ExampleCasContent, ROGraph
from dgfisma_rdf.reporting_obligations.rdf_parser import SPARQLReportingObligationProvider, RDFLibGraphWrapper


# TODO test if every RO has a doc source


class TestLocalGraph(unittest.TestCase):
    def setUp(self) -> None:
        g = ROGraph(include_schema=True,
                    )

        doc_id = 'https://example.com/doc1'

        cas_content = ExampleCasContent.build()

        source_name = 'EBA'
        self.source_id = 'https://eba.europa.eu/'

        g.add_cas_content(cas_content,
                          doc_id=doc_id)

        # Some extra data
        doc_id2 = 'https://example.com/doc2'
        g.add_cas_content(cas_content,
                          doc_id=doc_id2)

        g.add_doc_source(doc_id,
                         self.source_id,
                         source_name,
                         # query_endpoint=query_endpoint
                         )

        with io.BytesIO(g.serialize()) as f:
            graph_wrapper = RDFLibGraphWrapper(f)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

        # TODO build local graph.

    def test_foo(self):
        l_ent_types = self.prov.get_different_entity_types()

        with self.subTest("RO's"):
            r = self.prov.get_filter_ro_id_multiple(doc_src=self.source_id)['uris']
            self.assertTrue(len(r))

        with self.subTest("Drop down elements"):
            l_ent_type_i = next(filter(lambda ent_type_i: 'verb' in ent_type_i.lower(), l_ent_types))
            r_all = self.prov.get_filter_entities_from_type_lazy_loading(l_ent_type_i)

            r_doc_src = self.prov.get_filter_entities_from_type_lazy_loading(l_ent_type_i,
                                                                             doc_src=self.source_id)

            self.assertGreaterEqual(len(r_doc_src), 1)
            self.assertLessEqual(len(r_doc_src), len(r_all))
