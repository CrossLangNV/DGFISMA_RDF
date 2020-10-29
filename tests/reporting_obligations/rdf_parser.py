import os
import unittest
from typing import Iterable

from reporting_obligations.build_rdf import D_ENTITIES
from reporting_obligations.rdf_parser import SPARQLReportingObligationProvider, RDFLibGraphWrapper

ROOT = os.path.join(os.path.dirname(__file__), '../..')


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


if __name__ == '__main__':
    unittest.main()
