import os
import tempfile
import unittest
from typing import Iterable

from reporting_obligations import build_rdf
from reporting_obligations.build_rdf import D_ENTITIES, ExampleCasContent, ROGraph
from reporting_obligations.rdf_parser import SPARQLReportingObligationProvider, RDFLibGraphWrapper, SPARQLGraphWrapper

ROOT = os.path.join(os.path.dirname(__file__), '../..')

# You might have to change this
URL_FUSEKI = "http://localhost:8080/fuseki/sandbox/sparql"


class TestSPARQLGraphWrapper(unittest.TestCase):
    def test_query_get_triples(self):
        """ Test for non empty query results.

        Returns:

        """

        q = """
        SELECT ?subject ?predicate ?object
        WHERE {
          ?subject ?predicate ?object
        }
        LIMIT 25
        """

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)
        l = graph_wrapper.query(q)

        with self.subTest("type"):
            self.assertIsInstance(l, list, 'Expected to return a list')

        with self.subTest("non-empty"):
            self.assertTrue(len(l), 'Expected non empty list')


class TestSPARQLReportingObligationProvider(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.graph_wrapper = RDFLibGraphWrapper(os.path.join(ROOT, 'data/examples/reporting_obligations_mockup.rdf'))

    def test_get_ro_provider(self):

        try:
            self.ro_provider
        except AttributeError:
            self.ro_provider = SPARQLReportingObligationProvider(self.graph_wrapper)

        return self.ro_provider

    def test_different_entities(self):

        ro_provider = self.test_get_ro_provider()
        l = ro_provider.get_different_entities()

        with self.subTest("Type checking"):
            self.assertIsInstance(l, Iterable)

        l = list(l)
        with self.subTest("Checking for string compatible elements of the list"):
            for _ in map(str, l): pass

        with self.subTest("Length of list"):
            self.assertEqual(len(D_ENTITIES) + 1, len(l), 'amount of RO sentence entities are defined beforehand. '
                                                          'One extra is from general entity')

    def test_get_all_from_type(self):
        ro_provider = self.test_get_ro_provider()

        # from self.test_different_entities
        l_types = ['http://dgfisma.com/reporting_obligation#hasVerb',
                   'http://dgfisma.com/reporting_obligation#hasRegulatoryBody',
                   'http://dgfisma.com/reporting_obligation#hasEntity'  # This one might get deprecated in the future
                   ]

        for type_uri in l_types:
            basename = os.path.basename(type_uri)
            with self.subTest(f'{basename}'):
                l_labels = ro_provider.get_all_from_type(type_uri)

                self.assertIsInstance(l_labels, Iterable)
                l_labels = list(l_labels)  # convert to list to get info
                self.assertGreater(len(l_labels), 0, 'Should be more than one element')
                for _ in map(str, l_labels): pass  # should contain string-like objects

                print(f'class: {basename}')
                print('\t', l_labels)

    def test_distinct(self):
        type_uri = 'http://dgfisma.com/reporting_obligation#hasVerb'

        ro_provider = self.test_get_ro_provider()

        l_labels = ro_provider.get_all_from_type(type_uri, distinct=False)
        l_labels_distinct = ro_provider.get_all_from_type(type_uri, distinct=True)

        self.assertEqual(len(list(l_labels_distinct)), len(set(l_labels_distinct)),
                         'distinct should contain no value twice.')

        self.assertEqual(set(l_labels), (set(l_labels_distinct)),
                         'distinct should contain the same values, just no doubles.')
        self.assertLess(len(list(l_labels_distinct)), len(list(l_labels)), 'distinct should contain less values.')


class TestGetRO(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        b_locally = True
        if b_locally:  # Locally
            graph_wrapper = RDFLibGraphWrapper(os.path.join(ROOT, 'data/examples/reporting_obligations_mockup.rdf'))

        else:  # Through fuseki endpoint
            graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)

        self.ro_provider = SPARQLReportingObligationProvider(graph_wrapper)

        self.cas_content_example = ExampleCasContent.build()

    def get_ro_provider(self):
        return self.ro_provider

    def test_get_all(self):
        """ Query all reporting obligations

        Returns:

        """
        l_ro_uri = self.get_ro_provider().get_all_ro_uri()

        self.assertEqual(self.cas_content_example.get_NUM_RO(), len(l_ro_uri),
                         'Amount of reporting obligations do not seem to match.')

    def test_get_ro_str(self):
        """ Possible to get the string representation of a reporting obligation

        Returns:

        """

        l_to_find = ['a final system should provide for the determination',
                     'contribution debtor shall upon request provide the Board',
                     'of outsourcing tasks shall clearly state the'
                     ]

        l_ro = self.get_ro_provider().get_all_ro_str()

        for s_to_find in l_to_find:
            with self.subTest(s_to_find):
                self.assertTrue(any((s_to_find in ro_i) for ro_i in l_ro), "couldn't find string")

    def test_get_ro_str_context(self):
        """ We suppose it is necessary that the the context around a RO should be retrieved too.

        Returns:

        """

        l_to_find = ['belonging to the provisional period , the Board shall use the data collected',
                     'Board shall use the data collected',
                     ' tasks that are outsourced and establish a framework',
                     'previous financial year in accordance with Regulation ( EU )',
                     'members of the same group shall be collected from the',  # gap in between
                     ]

        l_ro = self.get_ro_provider().get_all_ro_str()

        for s_to_find in l_to_find:
            with self.subTest(s_to_find):
                self.assertTrue(any(s_to_find in ro_i for ro_i in l_ro), "couldn't find string")

    def test_get_filter_single(self):

        l_ent_types = self.get_ro_provider().get_different_entities()

        # Get verb predicate
        pred = list(filter(lambda x: 'Verb' in x, l_ent_types))[0]

        l_ent_type0 = self.get_ro_provider().get_all_from_type(pred)

        value = l_ent_type0[0]
        l_ro = self.get_ro_provider().get_filter_single(pred, value)

        self.assertTrue(l_ro, 'Should return a non-empty object')

        with self.subTest("Filter value should be contained in reporting obligation"):
            for ro_i in l_ro:
                self.assertIn(value, ro_i, 'Value should be contained in reporting obligation')

    def test_get_filter_nothing(self):

        l_ro = self.get_ro_provider().get_filter_multiple()

        self.assertTrue(l_ro, "Should return all RO's")

    def test_get_filter_multiple(self):

        l_ent_types = self.get_ro_provider().get_different_entities()

        pred0 = list(filter(lambda s: 'hasVerb' in s, l_ent_types))[0]
        pred1 = list(filter(lambda s: 'hasRegulatoryBody' in s, l_ent_types))[0]

        #
        l_ent_type0 = self.get_ro_provider().get_all_from_type(pred0)
        l_ent_type1 = self.get_ro_provider().get_all_from_type(pred1)

        # value0 = l_ent_type0[0]
        # value1 = l_ent_type1[0]

        value0 = 'provide'
        value1 = 'the Board'

        assert value0 in l_ent_type0
        assert value1 in l_ent_type1

        l_ro = self.get_ro_provider().get_filter_multiple([(pred0, value0), (pred1, value1)])

        self.assertTrue(l_ro, 'Should return a non-empty object')


class TestSPARQLReportingObligationProviderGetFilterMultiple(unittest.TestCase):
    L_ENTITIES = list(D_ENTITIES.keys())
    L_ENT1 = L_ENTITIES[1]
    L_ENT2 = L_ENTITIES[2]
    L_ENT3 = L_ENTITIES[3]

    S0 = 'a0 a1 a2 a0 a0'
    S1 = 'b2 a0 a3 a1 a0 a0 a0'
    S2 = 'b0 c0 a2 a2, a1, a0.'
    l = {build_rdf.KEY_CHILDREN: [
        # Base sentence
        {build_rdf.KEY_VALUE: S0,
         build_rdf.KEY_CHILDREN: [
             {build_rdf.KEY_VALUE: 'a1',
              build_rdf.KEY_SENTENCE_FRAG_CLASS: L_ENT1},
             {build_rdf.KEY_VALUE: 'a2',
              build_rdf.KEY_SENTENCE_FRAG_CLASS: L_ENT2},
         ]
         },
        # 1 key matching
        {build_rdf.KEY_VALUE: S1,
         build_rdf.KEY_CHILDREN: [
             {build_rdf.KEY_VALUE: 'a1',
              build_rdf.KEY_SENTENCE_FRAG_CLASS: L_ENT1},
             {build_rdf.KEY_VALUE: 'b2',
              build_rdf.KEY_SENTENCE_FRAG_CLASS: L_ENT2},
             {build_rdf.KEY_VALUE: 'a3',
              build_rdf.KEY_SENTENCE_FRAG_CLASS: L_ENT3},
         ]
         },
        # 2 same but different order
        {build_rdf.KEY_VALUE: S2,
         build_rdf.KEY_CHILDREN: [
             {build_rdf.KEY_VALUE: 'a1',
              build_rdf.KEY_SENTENCE_FRAG_CLASS: L_ENT1},
             {build_rdf.KEY_VALUE: 'a2',
              build_rdf.KEY_SENTENCE_FRAG_CLASS: L_ENT2},
         ]
         },
    ]}

    def __init__(self, *args, **kwargs):
        super(TestSPARQLReportingObligationProviderGetFilterMultiple, self).__init__(*args, **kwargs)

        # Building the Reporting Obligation Provider
        g = ROGraph()
        g.add_cas_content(self.l)
        with tempfile.TemporaryDirectory() as d:
            filename = os.path.join(d, 'tmp.rdf')
            g.serialize(destination=filename, format="pretty-xml")
            graph_wrapper = RDFLibGraphWrapper(filename)
        self.ro_provider = SPARQLReportingObligationProvider(graph_wrapper)

    def test_no_filter(self):
        """ Without a filter, all reporting obligations should be returned

        :return:
        None
        """
        l_ro = self.ro_provider.get_filter_multiple()

        l = [ro_i[build_rdf.KEY_VALUE] for ro_i in self.l[build_rdf.KEY_CHILDREN]]
        self.assertEqual(set(l), set(l_ro), "Should return ALL reporting obligations")

    def test_single_filter(self):
        """Finding reporting obligations based on single filter"""

        with self.subTest("In all"):
            l_ro = self.ro_provider.get_filter_multiple([(D_ENTITIES[self.L_ENT1][0], 'a1')])
            self.assertEqual(set([self.S0, self.S1, self.S2]), set(l_ro), "Should return these specific reporting obligations")

        with self.subTest("In some"):
            l_ro = self.ro_provider.get_filter_multiple([(D_ENTITIES[self.L_ENT2][0], 'a2')])
            self.assertEqual(set([self.S0, self.S2]), set(l_ro), "Should return these specific reporting obligations")

    def test_multiple_filters(self):
        """Retrieving reporting obligations based on multiple filter

        :return: None
        """

        with self.subTest("test 1"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                            (D_ENTITIES[self.L_ENT2][0], 'a2')
                            ]
            l_ro = self.ro_provider.get_filter_multiple(list_filters)

            self.assertEqual(set([self.S0, self.S2]), set(l_ro), "Should return these specific reporting obligations")

            del list_filters, l_ro

        with self.subTest("test 2"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                            (D_ENTITIES[self.L_ENT2][0], 'b2')
                            ]
            l_ro = self.ro_provider.get_filter_multiple(list_filters)

            self.assertEqual(set([self.S1]), set(l_ro), "Should return these specific reporting obligations")

            del list_filters, l_ro

    def test_duplicates(self):
        """ Should not complain if duplicates in key-value pairs.
        """

        with self.subTest("matching duplicate 1"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                            ]
            l_ro = self.ro_provider.get_filter_multiple(list_filters)

            list_filters_dup = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                                (D_ENTITIES[self.L_ENT1][0], 'a1'),
                                ]
            l_ro_dup = self.ro_provider.get_filter_multiple(list_filters_dup)

            self.assertEqual(set(l_ro), set(l_ro_dup), "Should return same as with single filter")

        with self.subTest("different values for same key"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                            (D_ENTITIES[self.L_ENT1][0], 'a2'),
                            ]
            l_ro = self.ro_provider.get_filter_multiple(list_filters)

            self.assertEqual(set(), set(l_ro), "Should return nothing")

        with self.subTest("Lot of duplicates"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                               (D_ENTITIES[self.L_ENT2][0], 'a2')]
            l_ro = self.ro_provider.get_filter_multiple(list_filters)

            list_filters_dup = [(D_ENTITIES[self.L_ENT1][0], 'a1')]*3 + \
                               [(D_ENTITIES[self.L_ENT2][0], 'a2')]*2

            l_ro_dup = self.ro_provider.get_filter_multiple(list_filters_dup)

            self.assertEqual(set(l_ro), set(l_ro_dup), "Should return same as with single filter")


    def test_no_matches(self):
        """Try to receive reporting obligations that don't exist

        :return: None
        """

        with self.subTest("two different values for same key"):
            list_filters = [(D_ENTITIES[self.L_ENT2][0], 'a2'),
                            (D_ENTITIES[self.L_ENT2][0], 'b2')
                            ]
            l_ro = self.ro_provider.get_filter_multiple(list_filters)

            self.assertEqual(set(), set(l_ro), "Should return nothing")

        with self.subTest("Value not in data"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'z1'),
                            ]
            l_ro = self.ro_provider.get_filter_multiple(list_filters)

            self.assertEqual(set(), set(l_ro), "Should return nothing")

        with self.subTest("Value not in data and existing key-value"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                            (D_ENTITIES[self.L_ENT2][0], 'z2')
                            ]
            l_ro = self.ro_provider.get_filter_multiple(list_filters)

            self.assertEqual(set(), set(l_ro), "Should return nothing")


if __name__ == '__main__':
    unittest.main()
