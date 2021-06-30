import unittest

from dgfisma_rdf.reporting_obligations.rdf_parser import SPARQLReportingObligationProvider, SPARQLGraphWrapper

# You might have to change this
URL_FUSEKI = "http://gpu1.crosslang.com:3030/RO_test/query"
URL_STAGING = "http://gpu1.crosslang.com:3030/RO_staging/query"
URL_FUSEKI_PRD = "http://gpu1.crosslang.com:3030/RO_prd_clone/query"


class TestGetDocIDs(unittest.TestCase):
    """
    While not needed, adding this functionality will make it easier for the tests below
    """

    def setUp(self) -> None:
        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_get_all(self):
        l_uri = self.prov.get_all_doc_uri()

        with self.subTest("Non-emtpy"):
            self.assertTrue(len(l_uri))

        with self.subTest("less docs then RO's"):
            self.assertLessEqual(len(l_uri), len(self.prov.get_all_ro_uri()))

    def test_test_amount_docs(self):
        for name, url in {"test": URL_FUSEKI, "staging": URL_STAGING, "production": URL_FUSEKI_PRD}.items():
            with self.subTest(name):
                graph_wrapper = SPARQLGraphWrapper(url)
                prov = SPARQLReportingObligationProvider(graph_wrapper)

                l_uri = prov.get_all_doc_uri()

                print(f"Set {name} has {len(l_uri)} doc id's")


class TestGetROFilterDocIDs(unittest.TestCase):
    """
    E.g. filter on bookmarked documents: only return RO's that are bookmarked.
    Probably most needed for the filter items.
    """

    def setUp(self) -> None:
        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

        self.l_doc_uri = self.prov.get_all_doc_uri()
        self.l_doc_uri_subset = self.l_doc_uri[: (len(self.l_doc_uri) // 2)] + [
            "www.some_test.com",
            "http://doc_uri_s.io",
        ]

    def test_filter_entities_from_type(self):
        uri_type_has = next(
            filter(lambda s: "RegulatoryBody".lower() in s.lower(), self.prov.get_different_entity_types())
        )

        l_ent_all_baseline = self.prov.get_filter_entities_from_type_lazy_loading(uri_type_has)

        l_ent_all = self.prov.get_filter_entities_from_type_lazy_loading(uri_type_has, l_doc_uri=self.l_doc_uri)

        l_ent_subset = self.prov.get_filter_entities_from_type_lazy_loading(
            uri_type_has, l_doc_uri=self.l_doc_uri_subset
        )

        l_ent_none = self.prov.get_filter_entities_from_type_lazy_loading(
            uri_type_has, l_doc_uri=["https://no_document_with_this_uri_should_exist.be"]
        )

        with self.subTest("empty"):
            self.assertEqual(len(l_ent_none), 0, "Should give no results/filter all RO's")
        with self.subTest("empty"):
            self.assertListEqual(l_ent_none, [], "Should give no results/filter all RO's")

        with self.subTest("all"):
            self.assertEqual(len(l_ent_all), len(l_ent_all_baseline), "Should return all RO's")
        with self.subTest("all"):
            self.assertListEqual(l_ent_all, l_ent_all_baseline, "Should return all RO's")

        with self.subTest("subset"):
            self.assertGreater(len(l_ent_subset), 0, "Should give some results")
        with self.subTest("subset"):
            self.assertLess(len(l_ent_subset), len(l_ent_all_baseline), "Should not return all results")

        set_ent_subset = set(l_ent_subset)

        with self.subTest("subset"):
            self.assertTrue(set().issubset(set_ent_subset), "Should give some results")
        with self.subTest("subset"):
            self.assertTrue(set_ent_subset.issubset(set(l_ent_all_baseline)), "Should give some results")

    def test_filter_ro_id_multiple(self):
        l_ro_all_baseline = self.prov.get_filter_ro_id_multiple()

        l_ro_all = self.prov.get_filter_ro_id_multiple(l_doc_uri=self.l_doc_uri)

        l_ro_subset = self.prov.get_filter_ro_id_multiple(l_doc_uri=self.l_doc_uri_subset)

        l_ro_none = self.prov.get_filter_ro_id_multiple(
            l_doc_uri=["https://no_document_with_this_uri_should_exist.be"]
        )

        with self.subTest("empty"):
            self.assertEqual(len(l_ro_none), 0, "Should give no results/filter all RO's")
        with self.subTest("empty"):
            self.assertListEqual(l_ro_none, [], "Should give no results/filter all RO's")

        with self.subTest("all"):
            self.assertEqual(len(l_ro_all), len(l_ro_all_baseline), "Should return all RO's")
        with self.subTest("all"):
            self.assertListEqual(l_ro_all, l_ro_all_baseline, "Should return all RO's")

        with self.subTest("subset"):
            self.assertGreater(len(l_ro_subset), 0, "Should give some results")
        with self.subTest("subset"):
            self.assertLess(len(l_ro_subset), len(l_ro_all_baseline), "Should not return all results")

        set_ro_subset = set(l_ro_subset)

        with self.subTest("subset"):
            self.assertTrue(set().issubset(set_ro_subset), "Should give some results")
        with self.subTest("subset"):
            self.assertTrue(set_ro_subset.issubset(set(l_ro_all_baseline)), "Should give some results")


if __name__ == "__main__":
    unittest.main()
