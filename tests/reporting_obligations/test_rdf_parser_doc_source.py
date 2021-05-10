"""
On 31/04/2021 it was decided that the document source (the website) should be added to the RDF for easier querying.

In this file, we test the ability to filter based on the website.
"""
import io
import unittest

import numpy as np

from dgfisma_rdf.reporting_obligations.build_rdf import ExampleCasContent, ROGraph
from dgfisma_rdf.reporting_obligations.rdf_parser import SPARQLReportingObligationProvider, RDFLibGraphWrapper, \
    SPARQLGraphWrapper

if 0:
    # Oan's localhost
    ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_oan/query'
elif 0:
    # Staging
    ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_staging/query'
else:
    # Production
    ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_prd_clone/query'
    ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_prd/query'


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

    def test_filter(self):
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

    def test_all_ro_doc(self):
        """
        Test if every reporting obligation document has a document source.
        :return:
        """

        l_doc_src = self.prov.get_document_and_source_pairs()

        frac_src = np.mean(list(map(lambda d_s: bool(d_s[-1]), l_doc_src)))
        print(f'Percentage of = {frac_src:.1%}')

        self.assertGreater(frac_src, 0, 'Should have at least some document sources')

        if 0:
            for doc, src in l_doc_src:
                with self.subTest('Doc %s' % doc):
                    self.assertTrue(src, 'Expected a document source.')


class TestRemoteGraph(unittest.TestCase):
    def setUp(self) -> None:

        graph_wrapper = SPARQLGraphWrapper(ENDPOINT)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_filter(self):
        l_ent_types = self.prov.get_different_entity_types()

        l_doc_src = self.prov.get_document_and_source_pairs()
        try:
            source_id = next(src_i for _, src_i in l_doc_src if src_i)
        except Exception as e:
            self.fail("Sanity check: couldn't find a single document source.")

        with self.subTest("RO's"):
            r = self.prov.get_filter_ro_id_multiple(doc_src=source_id)['uris']
            self.assertTrue(len(r))

        with self.subTest("Drop down elements"):
            l_ent_type_i = next(filter(lambda ent_type_i: 'verb' in ent_type_i.lower(), l_ent_types))
            r_all = self.prov.get_filter_entities_from_type_lazy_loading(l_ent_type_i)

            r_doc_src = self.prov.get_filter_entities_from_type_lazy_loading(l_ent_type_i,
                                                                             doc_src=source_id)

            self.assertGreaterEqual(len(r_doc_src), 1)
            self.assertLessEqual(len(r_doc_src), len(r_all))

    def test_all_ro_doc(self):
        """
        Test if every reporting obligation document has a document source.
        :return:
        """

        l_doc_src = self.prov.get_document_and_source_pairs()

        frac_src = np.mean(list(map(lambda d_s: bool(d_s[-1]), l_doc_src)))
        print(f'Percentage of = {frac_src:.1%}')

        for doc, src in l_doc_src:
            # with self.subTest('Doc %s' % doc):
            self.assertTrue(src, 'Expected a document source.')
