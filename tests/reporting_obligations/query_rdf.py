"""
We should be able to run some basic queries on our constructed RDF.
"""

import json
import os
import unittest
from reporting_obligations import build_rdf
from reporting_obligations import cas_parser

ROOT = os.path.join(os.path.dirname(__file__), '../..')


class TestFilterEntries(unittest.TestCase):
    """
    For reporting obligations it is desired to easily filter or search based on the different sentence segment classes.
    These have to be extracted to build up a dictionary of a labels and predicates
    """

    def __init__(self, *args, **kwargs):
        folder_cas = 'reporting_obligations/output_reporting_obligations'
        # filename_cas = 'cas_laurens.xml'
        filename_cas = 'ro + html2text.xml'  # 17 RO's0
        rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'

        # from ROOT
        path_cas = os.path.join(ROOT, folder_cas, filename_cas)
        path_typesystem = os.path.join(ROOT, rel_path_typesystem)

        l = cas_parser.CasContent.from_cas(path_cas, path_typesystem)
        self.g = build_rdf.main(l)

        super(TestFilterEntries, self).__init__(*args, **kwargs)

    def test_different_entities(self):
        entities = build_rdf.get_different_entities(self.g)
        self.assertIsInstance(entities, list)
        self.assertTrue(len(entities))

        with open(os.path.join(ROOT, 'reporting_obligations/sentence_segments_predicate2label.json')) as json_file:
            data = json.load(json_file)

        for entity in map(str, entities):
            with self.subTest(f'Entity: {entity}'):
                self.assertTrue((entity) in data.keys(), 'No label found for entity class')


if __name__ == '__main__':
    unittest.main()
