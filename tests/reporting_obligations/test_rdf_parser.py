import os
import random
import string
import tempfile
import time
import unittest
from typing import Iterable

import numpy as np
from rdflib.term import URIRef

from dgfisma_rdf.reporting_obligations import build_rdf, rdf_parser
from dgfisma_rdf.reporting_obligations.build_rdf import D_ENTITIES, ExampleCasContent, ROGraph, MOCKUP_FILENAME
from dgfisma_rdf.reporting_obligations.rdf_parser import SPARQLReportingObligationProvider, RDFLibGraphWrapper, \
    SPARQLGraphWrapper

ROOT = os.path.join(os.path.dirname(__file__), '../..')

# You might have to change this
# URL_FUSEKI = "http://localhost:8080/fuseki/sandbox/sparql"
# URL_FUSEKI = "http://fuseki_RO:3030/RO"
URL_FUSEKI = "http://gpu1.crosslang.com:3030/RO_test"
URL_STAGING = "http://gpu1.crosslang.com:3030/RO_staging"
URL_FUSEKI_PRD = "http://gpu1.crosslang.com:3030/RO_prd_clone"


class TestRDFLibGraphWrapper(unittest.TestCase):
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
        graph_wrapper = RDFLibGraphWrapper(MOCKUP_FILENAME)

        l = graph_wrapper.query(q)

        with self.subTest("type"):
            self.assertIsInstance(l, Iterable, 'Expected to return an Iterable')

        with self.subTest("non-empty"):
            self.assertTrue(len(l), 'Expected non empty list')

        with self.subTest("keys"):
            self.assertEqual({'subject', 'predicate', 'object'}, set(l[0].keys()),
                             'keys per row should contain O R S.')

        with self.subTest("keys of value"):
            v = l[0]['subject']
            self.assertTrue({'value', 'type'}.issubset(set(v.keys())),
                            f'Value and type should be contained in {v.keys()}')


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
            self.assertIsInstance(l, Iterable, 'Expected to return an Iterable')

        with self.subTest("non-empty"):
            self.assertTrue(len(l), 'Expected non empty list')

        with self.subTest("keys"):
            self.assertEqual({'subject', 'predicate', 'object'}, set(l[0].keys()),
                             'keys per row should contain O R S.')

        with self.subTest("keys of value"):
            v = l[0]['subject']
            self.assertTrue({'value', 'type'}.issubset(set(v.keys())),
                            f'Value and type should be contained in {v.keys()}')


class TestGraphWrapper(unittest.TestCase):
    """
    All GraphWrappers should be equivalent
    """

    def test_query_identical_pref_labels(self):
        """ For the different GraphWrapper, check that they all give back the same SKOS:prefLabel

        Returns:
            None
        """

        q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT ?subject ?object
        WHERE {
          ?subject skos:prefLabel ?object
        }
        ORDER BY ?object ?subject
        """

        graph_wrapper_RDFLib = RDFLibGraphWrapper(MOCKUP_FILENAME)
        l_RDFLib = graph_wrapper_RDFLib.query(q)

        graph_wrapper_SPARQLWrapper = SPARQLGraphWrapper(URL_FUSEKI)
        l_SPARQLWrapper = graph_wrapper_SPARQLWrapper.query(q)

        with self.subTest('Type return value'):
            self.assertEqual(type(l_RDFLib),
                             type(l_SPARQLWrapper),
                             'Should return same type')

        RDFLib_0 = l_RDFLib[0]
        SPARQLWrapper_0 = l_SPARQLWrapper[0]

        with self.subTest('Type list element'):
            self.assertEqual(type(RDFLib_0),
                             type(SPARQLWrapper_0),
                             'Both list elements should be of same type')

        with self.subTest('List element keys'):
            self.assertEqual(RDFLib_0.keys(),
                             SPARQLWrapper_0.keys(),
                             'Both list elements should have the same dictionary keys')

        with self.subTest('Sub dictionary keys'):
            # Assumes previous test was successful.
            for key, value_RDFLib_0 in RDFLib_0.items():
                value_SPARQLWrapper_0 = SPARQLWrapper_0.get(key)

                self.assertEqual(value_RDFLib_0.keys(), value_SPARQLWrapper_0.keys())


class TestSPARQLReportingObligationProvider(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.graph_wrapper = RDFLibGraphWrapper(MOCKUP_FILENAME)

    def test_get_ro_provider(self):

        try:
            self.ro_provider
        except AttributeError:
            self.ro_provider = SPARQLReportingObligationProvider(self.graph_wrapper)

        return self.ro_provider

    def test_different_entities(self):

        ro_provider = self.test_get_ro_provider()
        l = ro_provider.get_different_entity_types()

        with self.subTest("Type checking"):
            self.assertIsInstance(l, Iterable)

        l = list(l)
        with self.subTest("Checking for string compatible elements of the list"):
            for _ in map(str, l):
                pass

        with self.subTest("Length of list"):
            self.assertEqual(len(D_ENTITIES) + 1, len(l), 'amount of RO sentence entities are defined beforehand. '
                                                          'One extra is from general entity')

    def test_get_all_from_type(self):
        ro_provider = self.test_get_ro_provider()

        # from self.test_different_entities
        l_types = [D_ENTITIES['V'][0],
                   D_ENTITIES['ARG2'][0],
                   D_ENTITIES['ARG0'][0],
                   D_ENTITIES['ARG1'][0],
                   D_ENTITIES['ARG2'][0],
                   # D_ENTITIES['ARG3'][0],
                   # build_rdf.PROP_HAS_ENTITY,  # This one might get deprecated in the future
                   ]

        for type_uri in l_types:
            basename = os.path.basename(type_uri)
            with self.subTest(f'{basename}'):
                l_labels = ro_provider.get_all_from_type(type_uri)

                self.assertIsInstance(l_labels, Iterable, 'Sanity check output type')
                l_labels = list(l_labels)  # convert to list to get info

                with self.subTest('Non-emtpy'):
                    self.assertGreater(len(l_labels), 0, 'Should be more than one element')

                with self.subTest('Uniqueness'):
                    # Casing is NOT ignored
                    set_labels = set(l_labels)  # map(str.lower, l_labels)
                    self.assertEqual(len(l_labels), len(set_labels), 'Should contain no duplicates')

    def test_distinctness(self):

        type_uri = D_ENTITIES['V'][0]

        ro_provider = self.test_get_ro_provider()

        l_labels = ro_provider.get_all_from_type(type_uri, distinct=False)
        l_labels_distinct = ro_provider.get_all_from_type(type_uri, distinct=True)

        self.assertEqual(len(list(l_labels_distinct)), len(set(l_labels_distinct)),
                         'distinct should contain no value twice.')

        self.assertEqual(set(l_labels), (set(l_labels_distinct)),
                         'distinct should contain the same values, just no doubles.')
        self.assertLess(len(list(l_labels_distinct)), len(list(l_labels)), 'distinct should contain less values.')


class TestGetAllFromType(unittest.TestCase):

    def setUp(self) -> None:

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI_PRD)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_equivalence(self):
        """
        While trying to optimize the query it is important to check if they are able to give all the same results.

        Returns:
            None
        """

        # work on faster
        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)  # URL_STAGING, URL_FUSEKI_PRD
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

        distinct = True
        VALUE = 'value_ent'

        l_has = self.prov.get_different_entity_types()

        def check_equivalence(d0, d1,
                              b_subtest=False):

            for has_type_uri in l_has:

                if b_subtest:
                    with self.subTest(has_type_uri):
                        self.assertEqual(d0.get(has_type_uri),
                                         d1.get(has_type_uri),
                                         'Output should be the same.')
                else:
                    self.assertEqual(d0.get(has_type_uri),
                                     d1.get(has_type_uri),
                                     'Output should be the same.')

        def get_d_correct():

            d = {}
            for has_type_uri in l_has:
                q = f"""
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                    SELECT {'DISTINCT' if distinct else ''} ?{VALUE}

                    WHERE {{
                        ?ro a {build_rdf.ROGraph.class_rep_obl.n3()} ;
                            {URIRef(has_type_uri).n3()} ?ent .
                        ?ent skos:prefLabel ?{VALUE}
                    }}
                    ORDER BY (LCASE(?{VALUE}))
                """

                r = self.prov.graph_wrapper.query(q)
                l = self.prov.graph_wrapper.get_column(r, VALUE)

                d[has_type_uri] = l

            return d

        def get_d_implementation():
            d = {}
            for has_type_uri in l_has:
                d[has_type_uri] = self.prov.get_all_from_type(has_type_uri)

            return d

        def get_d_simple():
            d = {}

            for has_type_uri in l_has:
                q = f"""
                                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                                SELECT {'DISTINCT' if distinct else ''} ?{VALUE}

                                WHERE {{
                                    ?ro {URIRef(has_type_uri).n3()} ?ent .
                                    ?ent skos:prefLabel ?{VALUE}
                                }}

                                # ORDER BY (LCASE(?{VALUE}))
                            """

                r = self.prov.graph_wrapper.query(q)
                l = self.prov.graph_wrapper.get_column(r, VALUE)

                d[has_type_uri] = l

            return d

        d0 = get_d_correct()

        with self.subTest('-- Implementation --'):

            d = get_d_implementation()
            check_equivalence(d0, d)

        if 0:  # This simple Query sometimes give too much data back
            with self.subTest('-- Simple --'):
                d = get_d_simple()
                check_equivalence(d0, d)

        return

    def test_speed(self):
        """ Dropdown menu's seem to be the

        Returns:

        """

        n_samples = 3

        distinct = True

        VALUE = 'value_ent'

        l_has_types = self.prov.get_different_entity_types()

        if 1:
            s_subtest = 'Implemented query'
            with self.subTest(s_subtest):
                print(s_subtest)

                l_T = []
                for _ in range(n_samples):

                    t0 = time.time()
                    for has_type_uri in l_has_types:
                        self.prov.get_all_from_type(has_type_uri)
                    t1 = time.time()

                    l_T.append(t1 - t0)

                print(f'T query = {np.mean(l_T):.2f} +- {np.std(l_T):.2f} s')

        if 1:
            s_subtest = 'minimal query'
            with self.subTest(s_subtest):
                print(s_subtest)

                l_T = []
                for _ in range(n_samples):

                    t0 = time.time()
                    for has_type_uri in l_has_types:
                        q = f"""
                                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
                                    SELECT {'DISTINCT' if distinct else ''} ?{VALUE}
            
                                    WHERE {{
                                        ?ro    {URIRef(has_type_uri).n3()} ?ent .
                                        ?ent skos:prefLabel ?{VALUE}
                                    }}
                                """

                        self.prov.graph_wrapper.query(q)
                    t1 = time.time()

                    l_T.append(t1 - t0)

                print(f'T query = {np.mean(l_T):.2f} +- {np.std(l_T):.2f} s')

        if 1:
            s_subtest = 'Type based:'
            with self.subTest(s_subtest):
                print(s_subtest)

                l_T = []

                def get_type(has_uri):

                    for has_i, type_i in build_rdf.D_ENTITIES.values():
                        if URIRef(has_i) == URIRef(has_uri):
                            return type_i

                    return build_rdf.SKOS.Concept

                for _ in range(n_samples):

                    t0 = time.time()
                    for has_type_uri in l_has_types:
                        type_uri = get_type(has_type_uri)

                        q = f"""
                                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
                                    SELECT {'DISTINCT' if distinct else ''} ?{VALUE}
        
                                    WHERE {{
                                        ?ent a {URIRef(type_uri).n3()};
                                            skos:prefLabel ?{VALUE}
                                    }}
                                """

                        r = self.prov.graph_wrapper.query(q)

                    t1 = time.time()
                    l_T.append(t1 - t0)

                print(f'T query = {np.mean(l_T):.2f} +- {np.std(l_T):.2f} s')

        if 1:
            s_subtest = 'Single query:'
            with self.subTest(s_subtest):
                print(s_subtest)

                l_T = []

                L_TYPE = [type_i for has_i, type_i in build_rdf.D_ENTITIES.values()]

                for _ in range(n_samples):
                    t0 = time.time()

                    q_value = f"""
                        VALUES ?type {{{' '.join(map(lambda x: x.n3(), L_TYPE))}}}
                    """

                    q = f"""
                        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                        SELECT DISTINCT ?type ?value_ent
                    
                        WHERE {{
                        
                            {q_value}
                                           
                            ?ent a ?type;
                                skos:prefLabel ?value_ent ;
                        }}
                    """

                    r = self.prov.graph_wrapper.query(q)

                    t1 = time.time()
                    l_T.append(t1 - t0)

                print(f'T query = {np.mean(l_T):.2f} +- {np.std(l_T):.2f} s')

        return


class TestGetRO(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        b_locally = True
        if b_locally:  # Locally
            graph_wrapper = RDFLibGraphWrapper(MOCKUP_FILENAME)

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

        self.assertGreater(self.cas_content_example.get_NUM_RO(), 0,
                           'Sanity check: Cas content example should not be empty!')
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

        l_ent_types = self.get_ro_provider().get_different_entity_types()

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

        l_ent_types = self.get_ro_provider().get_different_entity_types()

        pred0 = list(filter(lambda s: 'hasVerb' in s, l_ent_types))[0]
        pred1 = list(filter(lambda s: 'hasRegulatoryBody' in s, l_ent_types))[0]

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

    def test_filter_case_insensitive(self):

        l_ent_types = self.get_ro_provider().get_different_entity_types()

        pred0 = list(filter(lambda s: 'hasVerb' in s, l_ent_types))[0]
        pred1 = list(filter(lambda s: 'hasRegulatoryBody' in s, l_ent_types))[0]

        l_ent_type0 = self.get_ro_provider().get_all_from_type(pred0)
        l_ent_type1 = self.get_ro_provider().get_all_from_type(pred1)

        value0 = 'provide'
        value1 = 'the Board'

        self.assertIn(value0, l_ent_type0, 'Sanity check')
        self.assertIn(value1, l_ent_type1, 'Sanity check')

        l_ro = self.get_ro_provider().get_filter_multiple([(pred0, value0), (pred1, value1)])

        self.assertTrue(len(l_ro), 'Sanity check, should be non-emtpy')

        with self.subTest('Uppercase'):
            l_ro_upper = self.get_ro_provider().get_filter_multiple([(pred0, value0.upper()), (pred1, value1.upper())])
            self.assertEqual(set(l_ro), set(l_ro_upper), 'Output should be identical')

        with self.subTest('Lowercase'):
            l_ro_lower = self.get_ro_provider().get_filter_multiple([(pred0, value0.lower()), (pred1, value1.lower())])
            self.assertEqual(set(l_ro), set(l_ro_lower), 'Output should be identical')


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

    g = ROGraph(include_schema=True)
    g.add_cas_content(l, 'test_doc')
    # Building the Reporting Obligation Provider
    with tempfile.TemporaryDirectory() as d:
        filename = os.path.join(d, 'tmp.rdf')
        g.serialize(destination=filename, format="pretty-xml")
        graph_wrapper = RDFLibGraphWrapper(filename)
    ro_provider = SPARQLReportingObligationProvider(graph_wrapper)

    def __init__(self, *args, **kwargs):
        super(TestSPARQLReportingObligationProviderGetFilterMultiple, self).__init__(*args, **kwargs)

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
            self.assertEqual(set([self.S0, self.S1, self.S2]), set(l_ro),
                             "Should return these specific reporting obligations")

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

            list_filters_dup = [(D_ENTITIES[self.L_ENT1][0], 'a1')] * 3 + \
                               [(D_ENTITIES[self.L_ENT2][0], 'a2')] * 2

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

    def test_multiple_filters_ro_id(self):
        """Retrieving reporting obligation UID's based on multiple filters

        :return: None
        """

        with self.subTest("test 1"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                            (D_ENTITIES[self.L_ENT2][0], 'a2')
                            ]
            l_ro = self.ro_provider.get_filter_ro_id_multiple(list_filters)

            l_ro_GT = [a.get('id') for a in self.l.get(build_rdf.KEY_CHILDREN) if
                       a.get(build_rdf.KEY_VALUE) in [self.S0, self.S2]]

            self.assertEqual(set(l_ro_GT), set(l_ro), "Should return these specific reporting obligations")

            del list_filters, l_ro

        with self.subTest("test 2"):
            list_filters = [(D_ENTITIES[self.L_ENT1][0], 'a1'),
                            (D_ENTITIES[self.L_ENT2][0], 'b2')
                            ]
            l_ro = self.ro_provider.get_filter_ro_id_multiple(list_filters)

            l_ro_GT = [a.get('id') for a in self.l.get(build_rdf.KEY_CHILDREN) if
                       a.get(build_rdf.KEY_VALUE) in [self.S1]]

            self.assertEqual(set(l_ro_GT), set(l_ro), "Should return these specific reporting obligations")

            del list_filters, l_ro


class TestSPARQLPagination(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #     b_locally = True
        #     if b_locally:  # Locally
        #         graph_wrapper = RDFLibGraphWrapper(MOCKUP_FILENAME)

        #     else:  # Through fuseki endpoint
        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)

        self.ro_provider = SPARQLReportingObligationProvider(graph_wrapper)

    #     self.cas_content_example = ExampleCasContent.build()

    def get_ro_provider(self):
        return self.ro_provider

    def test_foo(self):
        """ Query all reporting obligations

        Returns:

        """

        limit = 10
        l_ro_uri = self.get_ro_provider().get_filter_ro_id_multiple(limit=limit,
                                                                    offset=0)
        with self.subTest("Limit"):
            self.assertEqual(len(l_ro_uri), limit, 'Should return less than limit')

        with self.subTest("Next batch"):
            l_ro_uri_next = self.get_ro_provider().get_filter_ro_id_multiple(limit=limit, offset=limit)

            self.assertFalse(set(l_ro_uri).intersection(set(l_ro_uri_next)), 'There should be no overlap.')

        return


class TestFilterDropdown(unittest.TestCase):
    """
    When applying a filter, the the options for the other entities should be updated such that only valid options are shown.
    """

    def setUp(self) -> None:
        """
        Make the connection to the rdf.

        This can be:
        - Offline
        - Staging fuseki
        - Production fuseki

        Returns:

        """

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_return(self):
        """ Test if something can be returned

        Returns:

        """

        l_types_ent = self.prov.get_different_entity_types()

        type_ent0 = l_types_ent[0]
        type_ent1 = l_types_ent[1]

        l_types_ent

        l_ent_0 = self.prov.get_all_from_type(type_ent0)
        l_ent_1 = self.prov.get_all_from_type(type_ent1)

        ent_0_0 = l_ent_0[0]
        ent_1_0 = l_ent_1[0]

        l_ro = self.prov.get_filter_ro_id_multiple([(type_ent0, ent_0_0)])

        with self.subTest("Sanity check: some RO's"):
            self.assertGreater(len(l_ro), 0, 'Sanity check, should return some reporting obligations')

        l_ro_multiple = self.prov.get_filter_ro_id_multiple([(type_ent0, ent_0_0), (type_ent1, ent_1_0)])
        with self.subTest("Unlikely to get results with multiple filters"):
            self.assertEqual(len(l_ro_multiple), 0, 'If lucky, this could give results, but most likely not')

        for ent_0_i in l_ent_0:
            with self.subTest(f'Should return itself. "{ent_0_i}"'):
                l_ent_1_filtered = self.prov.get_filter_entities_from_type(
                    type_ent0,
                    [(type_ent0, ent_0_i)]
                )

                if len(l_ent_1_filtered) == 1:
                    self.assertEqual(l_ent_1_filtered[0], ent_0_i, 'Expect same value')
                else:
                    self.assertIn(ent_0_i, l_ent_1_filtered, 'Expect same value')

        return

    def test_no_filters_return_all(self):
        """ When no filters are applied, it's should probably still work and return everything

        Returns:

        """

        l_types_ent = self.prov.get_different_entity_types()

        for type_ent_i in l_types_ent:
            with self.subTest(f'{type_ent_i}'):
                l_ent_i = self.prov.get_all_from_type(type_ent_i)

                l_ent_no_filter_i = self.prov.get_filter_entities_from_type(type_ent_i)

                self.assertSetEqual(set(l_ent_i), set(l_ent_no_filter_i), 'Should contain same entities')

                self.assertEqual(l_ent_i, l_ent_no_filter_i, 'Order should be the same.')

    def test_if_updated_filters_give_results(self):
        """ The returned filters should give results if also adding to the filter

        Returns:

        """

        l_types_ent = self.prov.get_different_entity_types()

        n_test_count = 0
        n_test_max = 2

        for type_ent_i in l_types_ent:

            # HasReport/HasReporter has the most matches
            # if 'hasReport' not in type_ent_i:
            #     continue

            l_ent_i = self.prov.get_all_from_type(type_ent_i)

            for ent_i_i in l_ent_i:

                l_ro_filter_i_i = self.prov.get_filter_ro_id_multiple([(type_ent_i, ent_i_i)])

                for type_ent_j in l_types_ent:
                    if type_ent_i == type_ent_j:
                        continue
                    #
                    # if 'hasReporter' not in type_ent_j:
                    #     continue

                    l_ent_j = self.prov.get_all_from_type(type_ent_j)

                    for ent_j_j in l_ent_j:

                        l_ro_filter_j_j = self.prov.get_filter_ro_id_multiple([(type_ent_j, ent_j_j)])

                        l_ro_filter_intersection = set(l_ro_filter_i_i).intersection(l_ro_filter_j_j)

                        if len(l_ro_filter_intersection) == 0:
                            continue

                        # TODO Finding a match

                        l_ent_filter_j = self.prov.get_filter_entities_from_type(type_ent_j, [(type_ent_i, ent_i_i)])

                        with self.subTest(f'{ent_i_i} x {ent_j_j}'):
                            self.assertIn(ent_j_j, l_ent_filter_j, 'Should return this entity.')

                        n_test_count += 1
                        if n_test_count >= n_test_max:  # Enough tests done
                            return

        self.fail('This test should have stopped before!')

    def test_multiple_filters(self):
        """ It should be possible to apply multiple filters at once.

        Returns:

        """
        l_types_ent = self.prov.get_different_entity_types()

        # n_test_count = 0
        # n_test_max = 2

        for type_ent_i in l_types_ent:

            l_ent_i = self.prov.get_all_from_type(type_ent_i)

            for ent_i_i in l_ent_i:

                # l_ro_filter_i_i = self.prov.get_filter_ro_id_multiple([(type_ent_i, ent_i_i)])

                for type_ent_j in l_types_ent:
                    if type_ent_i == type_ent_j:
                        continue

                    l_ent_filter_j = self.prov.get_filter_entities_from_type(type_ent_j, [(type_ent_i, ent_i_i)])

                    if len(l_ent_filter_j):

                        for type_ent_k in l_types_ent:
                            if type_ent_k in (type_ent_i, type_ent_j):
                                continue

                            for ent_j_j in l_ent_filter_j:

                                l_ent_filter_k = self.prov.get_filter_entities_from_type(type_ent_k,
                                                                                         [(type_ent_i, ent_i_i),
                                                                                          (type_ent_j, ent_j_j),
                                                                                          ])

                                if len(l_ent_filter_k):
                                    l_ro = self.prov.get_filter_ro_id_multiple([(type_ent_i, ent_i_i),
                                                                                (type_ent_j, ent_j_j),
                                                                                (type_ent_k, l_ent_filter_k[0]),
                                                                                ])

                                    self.assertTrue(len(l_ro), 'Should return at least one RO.')

                                    return  # Done

    def test_multiple_filters_and_if_updated_filters_give_results(self):
        """ The returned filters should give results if also adding to the filter even if already applying multiple filters.

        Returns:

        """
        l_types_ent = self.prov.get_different_entity_types()

        # n_test_count = 0
        # n_test_max = 2

        for type_ent_i in l_types_ent:

            l_ent_i = self.prov.get_all_from_type(type_ent_i)

            for ent_i_i in l_ent_i:

                # l_ro_filter_i_i = self.prov.get_filter_ro_id_multiple([(type_ent_i, ent_i_i)])

                for type_ent_j in l_types_ent:
                    if type_ent_i == type_ent_j:
                        continue

                    l_ent_filter_j = self.prov.get_filter_entities_from_type(type_ent_j, [(type_ent_i, ent_i_i)])

                    if len(l_ent_filter_j):

                        for type_ent_k in l_types_ent:
                            if type_ent_k in (type_ent_i, type_ent_j):
                                continue

                            for ent_j_j in l_ent_filter_j:

                                l_ent_filter_k = self.prov.get_filter_entities_from_type(type_ent_k,
                                                                                         [(type_ent_i, ent_i_i),
                                                                                          (type_ent_j, ent_j_j),
                                                                                          ])

                                if len(l_ent_filter_k):
                                    l_ro = self.prov.get_filter_ro_id_multiple([(type_ent_i, ent_i_i),
                                                                                (type_ent_j, ent_j_j),
                                                                                (type_ent_k, l_ent_filter_k[0]),
                                                                                ])

                                    self.assertTrue(len(l_ro), 'Should return at least one RO.')

                                    return  # Done

    def test_equivalence(self):

        l_uri_has = self.prov.get_different_entity_types()

        def check_equivalence(d0, d1,
                              b_subtest=False
                              ):

            for has_type_uri in l_uri_has:

                if b_subtest:
                    with self.subTest(has_type_uri):
                        self.assertEqual(d0.get(has_type_uri),
                                         d1.get(has_type_uri),
                                         'Output should be the same.')
                else:
                    self.assertEqual(d0.get(has_type_uri),
                                     d1.get(has_type_uri),
                                     'Output should be the same.')

        def get_d_correct():
            #
            # d = {}
            # for has_type_uri in l_has:
            #     q = f"""
            #         PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            #
            #         SELECT {'DISTINCT' if distinct else ''} ?{VALUE}
            #
            #         WHERE {{
            #             ?ro a {build_rdf.ROGraph.class_rep_obl.n3()} ;
            #                 {URIRef(has_type_uri).n3()} ?ent .
            #             ?ent skos:prefLabel ?{VALUE}
            #         }}
            #         ORDER BY (LCASE(?{VALUE}))
            #     """
            #
            #     r = self.prov.graph_wrapper.query(q)
            #     l = self.prov.graph_wrapper.get_column(r, VALUE)
            #
            #     d[has_type_uri] = l

            return d_base

        def get0():
            d = self.prov.get_filter_entities()

            for uri_has in l_uri_has:
                if d.get(uri_has) is None:
                    d[uri_has] = []

                else:
                    d[uri_has] = [l_i.get('value_ent') for l_i in d[uri_has]]

            return d

        def get_filtered_entities():
            d1 = {}
            for uri_has in l_uri_has:
                l = self.prov.get_filter_entities_from_type(uri_has)
                d1[uri_has] = l

            return d1

        d_base = get0()

        with self.subTest('Filtered entities'):

            d1 = get_filtered_entities()

            check_equivalence(d_base, d1)

        return

    def test_speed(self):

        n_samples = 10

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI_PRD)
        prov = SPARQLReportingObligationProvider(graph_wrapper)

        l_types_ent = prov.get_different_entity_types()

        s_test = 'querying without filter'
        with self.subTest(s_test):
            print(s_test)

            l_T = []
            for type_ent_i in random.sample(l_types_ent, n_samples):
                t0 = time.time()
                prov.get_filter_entities_from_type(type_ent_i)
                t1 = time.time()

                l_T.append(t1 - t0)

            print(f'T query = {np.mean(l_T):.2f} +- {np.std(l_T):.2f} s')

        s_test = 'querying with filter'
        with self.subTest(s_test):
            print(s_test)

            l_T = []
            for type_ent_i in random.sample(l_types_ent, n_samples):
                type_ent_j = _sample_single(l_types_ent)
                l_ent_j = prov.get_all_from_type(type_ent_j)
                if len(l_ent_j) == 0:
                    continue  # Could be empty
                ent_j = _sample_single(l_ent_j)

                t0 = time.time()
                r = prov.get_filter_entities_from_type(type_ent_i,
                                                       [(type_ent_j, ent_j)])
                t1 = time.time()

                l_T.append(t1 - t0)

            print(f'T query = {np.mean(l_T):.2f} +- {np.std(l_T):.2f} s')


class TestGetEntities(unittest.TestCase):
    def setUp(self) -> None:

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_result(self):

        r = self.prov.get_entities()

        r_backup = self.prov.get_filter_entities()

        with self.subTest('Non-empty'):
            self.assertTrue(r)

        with self.subTest('Equivalent'):
            self.assertEqual(r, r_backup)

        for has_uri in self.prov.get_different_entity_types():
            with self.subTest(f'URI {has_uri}:'):
                self.assertEqual(r.get(has_uri), r_backup.get(has_uri))

    def test_speed(self):
        n_samples = 1

        # "Overwrite" for this test
        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI_PRD)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

        PRED = 'pred'
        TYPE = 'type'
        VALUE = 'value_ent'

        L_HAS = [has_i for has_i, type_i in build_rdf.D_ENTITIES.values()]
        L_TYPE = [type_i for has_i, type_i in build_rdf.D_ENTITIES.values()]

        if 1:
            s_subtest = 'Baseline'
            with self.subTest(s_subtest):
                print(s_subtest)

                l_T = []
                for _ in range(n_samples):
                    t0 = time.time()
                    l_types = self.prov.get_different_entity_types()
                    for type_i in l_types:
                        r = self.prov.get_all_from_type(type_i)
                    t1 = time.time()

                    l_T.append(t1 - t0)

                print(f'delta T = {np.mean(l_T)}')

        if 0:
            s_subtest = 'Simple'
            with self.subTest(s_subtest):
                print(s_subtest)
                q = """
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    PREFIX dgfro: <http://dgfisma.com/reporting_obligations/>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    SELECT DISTINCT ?pred ?value_ent (count(?ro_id) as ?count)
                    WHERE {
                        ?ro_id rdf:type <http://dgfisma.com/reporting_obligations/ReportingObligation> ;
                            ?pred ?ent .
                        ?ent skos:prefLabel ?value_ent .       
                    }
                    
                    GROUPBY ?pred ?value_ent
            
                    ORDER BY (LCASE(?pred)) (LCASE(?value_ent))
                """

                l_T = []
                for _ in range(n_samples):
                    t0 = time.time()
                    r = self.prov.graph_wrapper.query(q)
                    t1 = time.time()

                    l_T.append(t1 - t0)

                print(f'delta T = {np.mean(l_T)}')

        if 0:
            s_subtest = 'Filter the HAS predicates'
            with self.subTest(s_subtest):
                print(s_subtest)

                q_values = f"""
                VALUES ?{PRED} {{{' '.join(map(lambda x: x.n3(), L_HAS))}}}
                """

                q = f"""
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    PREFIX dgfro: <http://dgfisma.com/reporting_obligations/>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    SELECT DISTINCT ?pred ?value_ent (count(?ro_id) as ?count)
                    WHERE {{        
                        {q_values}
                
                        ?ro_id rdf:type <http://dgfisma.com/reporting_obligations/ReportingObligation> ;
                            ?pred ?ent .
                        ?ent skos:prefLabel ?value_ent .       
                    }}
    
                    GROUPBY ?pred ?value_ent
    
                    ORDER BY (LCASE(?pred)) (LCASE(?value_ent))
                """

                l_T = []
                for _ in range(n_samples):
                    t0 = time.time()
                    r = self.prov.graph_wrapper.query(q)
                    t1 = time.time()

                    l_T.append(t1 - t0)

                print(f'delta T = {np.mean(l_T)}')

        if 0:
            s_subtest = "Ignore RO's"
            with self.subTest(s_subtest):
                print(s_subtest)

                q_values = f"""
                VALUES ?{PRED} {{{' '.join(map(lambda x: x.n3(), L_HAS))}}}
                """

                q = f"""
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    PREFIX dgfro: <http://dgfisma.com/reporting_obligations/>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    SELECT DISTINCT ?pred ?value_ent # (count(?ro_id) as ?count)
                    WHERE {{        
                        {q_values}
    
                        ?ro_id ?pred ?ent .
                        ?ent skos:prefLabel ?value_ent .       
                    }}
    
                    GROUPBY ?pred ?value_ent
    
                    ORDER BY (LCASE(?pred)) (LCASE(?value_ent))
                """

                l_T = []
                for _ in range(n_samples):
                    t0 = time.time()
                    r = self.prov.graph_wrapper.query(q)
                    t1 = time.time()

                    l_T.append(t1 - t0)

                print(f'delta T = {np.mean(l_T)}')

        s_subtest = "Ignore RO's V2"
        with self.subTest(s_subtest):
            print(s_subtest)

            q_values = f"""
                    VALUES ?{TYPE} {{{' '.join(map(lambda x: x.n3(), L_TYPE))}}}
                    """

            q = f"""
                        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                        PREFIX dgfro: <http://dgfisma.com/reporting_obligations/>
                        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        SELECT DISTINCT ?{TYPE} ?{VALUE} # (count(?ro_id) as ?count)
                        WHERE {{        
                            {q_values}

                            ?ent a ?{TYPE} ;
                                skos:prefLabel ?{VALUE} .       
                        }}

                        GROUPBY ?{TYPE} ?{VALUE}

                        ORDER BY (LCASE(?pred)) (LCASE(?{VALUE}))
                    """

            l_T = []
            for _ in range(n_samples):
                t0 = time.time()
                r = self.prov.graph_wrapper.query(q)
                t1 = time.time()

                l_T.append(t1 - t0)

            print(f'delta T = {np.mean(l_T)}')


class TestFilterDropdownAllAtOnce(unittest.TestCase):

    def setUp(self) -> None:
        """
        Make the connection to the rdf.

        This can be:
        - Offline
        - Staging fuseki
        - Production fuseki

        Returns:

        """

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_no_filters_return_all(self):
        """ When no filters are applied, it's should probably still work and return everything

        Returns:

        """

        l_types_ent = self.prov.get_different_entity_types()

        d_filtered_ents = self.prov.get_filter_entities()

        for ent_type, l_ent_filtered in d_filtered_ents.items():
            with self.subTest(f'Type {ent_type}'):
                self.assertIn(ent_type, l_types_ent)

            with self.subTest(f'Non-empty {ent_type}'):
                self.assertTrue(len(l_ent_filtered), 'Should return at least one element')

    def test_speed(self):
        n_samples = 10

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI_PRD)
        prov = SPARQLReportingObligationProvider(graph_wrapper)

        l_types_ent = prov.get_different_entity_types()

        if 0:  # Bad idea as this is incredibly slow!
            s_test = 'querying without filter'
            with self.subTest(s_test):
                print(s_test)

                l_T = []
                for _ in range(n_samples):
                    t0 = time.time()
                    r = prov.get_filter_entities()
                    t1 = time.time()

                    l_T.append(t1 - t0)

                print(f'T query = {np.mean(l_T):.2f} s')

        s_test = 'querying with filter'
        with self.subTest(s_test):
            print(s_test)

            l_T = []
            for type_ent_i in random.sample(l_types_ent, n_samples):
                l_ent_i = prov.get_all_from_type(type_ent_i)
                if len(l_ent_i) == 0:
                    # Entity type without entities. E.g. hasPropGol
                    continue

                ent_i = _sample_single(l_ent_i)

                t0 = time.time()
                r = prov.get_filter_entities([(type_ent_i, ent_i)])
                t1 = time.time()

                l_T.append(t1 - t0)

            print(f'T query = {np.mean(l_T):.2f} s')


class TestFilterEntitiesFromTypeLazyLoading(unittest.TestCase):

    def setUp(self) -> None:

        graph_wrapper = SPARQLGraphWrapper(URL_STAGING)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_starts_with(self):
        l_uri_has = self.prov.get_different_entity_types()

        for uri_type_has in l_uri_has:

            with self.subTest(uri_type_has):

                l_no_filter = self.prov.get_filter_entities_from_type_lazy_loading(uri_type_has)

                if len(l_no_filter) == 0:
                    continue

                l = []
                for c in string.ascii_lowercase:
                    l += self.prov.get_filter_entities_from_type_lazy_loading(uri_type_has,
                                                                              str_match=c,
                                                                              type_match=rdf_parser.STARTS_WITH)

                self.assertTrue(len(l), 'Should return something')

                self.assertTrue(set(l).issubset(l_no_filter))

                self.assertEqual(len(l), len(set(l)), "There shouldn't be any duplicates")

        return

    def test_starts_with(self):
        l_uri_has = self.prov.get_different_entity_types()

        for uri_type_has in l_uri_has:

            with self.subTest(uri_type_has):

                l_no_filter = self.prov.get_filter_entities_from_type_lazy_loading(uri_type_has)

                if len(l_no_filter) == 0:
                    continue

                v0_i = l_no_filter[0]

                for uri_type_has_j in l_uri_has:
                    # Filter

                    l_no_filter_j = self.prov.get_filter_entities_from_type_lazy_loading(uri_type_has_j,
                                                                                         list_pred_value=[
                                                                                             (uri_type_has, v0_i)]
                                                                                         )
                    if len(l_no_filter_j) == 0:
                        continue

                    print()

                # l = []
                # for c in string.ascii_lowercase:
                #     l += self.prov.get_filter_entities_from_type_lazy_loading(uri_type_has,
                #                                                               starts_with=c)
                #
                # self.assertTrue(len(l), 'Should return something')
                #
                # self.assertTrue(set(l).issubset(l_no_filter))
                #
                # self.assertEqual(len(l), len(set(l)), "There shouldn't be any duplicates")

        return


def _sample_single(l):
    return list(random.sample(l, 1))[0]


if __name__ == '__main__':
    unittest.main()
