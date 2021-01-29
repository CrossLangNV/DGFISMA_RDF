import os
import unittest

from dgfisma_rdf.reporting_obligations import build_rdf
from dgfisma_rdf.reporting_obligations import cas_parser

ROOT = os.path.join(os.path.dirname(__file__), '../..')
# fixed example.
REL_PATH_CAS = 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/cas_laurens.xml'
REL_PATH_TYPESYSTEM = 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'

# from ROOT
path_cas = os.path.join(ROOT, REL_PATH_CAS)
path_typesystem = os.path.join(ROOT, REL_PATH_TYPESYSTEM)

KEY_CHILDREN = 'children'
KEY_VALUE = 'value'
KEY_SENTENCE_FRAG_CLASS = 'class'

NUM_RO = 17  # number of Reporting Obligations from test file


class TestExample(unittest.TestCase):
    def test_NUM_RO(self):
        cas_content = build_rdf.ExampleCasContent.build()
        self.assertEqual(cas_content.get_NUM_RO(), NUM_RO, 'Double check that test file still matches expectations.')


class TestSentenceFragment(unittest.TestCase):

    def test_return(self):
        v = 'v'
        c = 'c'
        sentence_fragment = cas_parser.SentenceFragment.from_value_class(v=v, c=c)

        self.assertEqual(set((KEY_SENTENCE_FRAG_CLASS, KEY_VALUE)), set(sentence_fragment.keys()))
        self.assertEqual(v, sentence_fragment[KEY_VALUE])
        self.assertEqual(c, sentence_fragment[KEY_SENTENCE_FRAG_CLASS])


class TestCasContent(unittest.TestCase):

    def test_return(self):
        l = [{KEY_CHILDREN: [{KEY_VALUE: 'v',
                              KEY_SENTENCE_FRAG_CLASS: 'g'
                              }
                             ],
              KEY_VALUE: 'full v.'
              }
             ]

        cas_content = cas_parser.CasContent.from_list(l)

        with self.subTest("cas content"):
            self.assertIsInstance(cas_content, dict, 'cas content should be a dictionary-like object')

            reporting_obligation_list = cas_content[KEY_CHILDREN]
            self.assertIsInstance(reporting_obligation_list, list, 'reporting obligations should be list.')
            self.assertTrue(len(reporting_obligation_list), 'Should be non-empty')

        reporting_obligation_content = reporting_obligation_list[0]
        sentence_fragments = reporting_obligation_content[KEY_CHILDREN]
        with self.subTest("reporting obligation"):
            self.assertIsInstance(reporting_obligation_content, dict, 'reporting obligation should be a dictionary.')

        sentence_fragment = sentence_fragments[0]
        with self.subTest("sentence fragment"):
            self.assertIsInstance(sentence_fragment, dict, 'sentence fragment should be a dictionary.')
            # Sentence Fragment class is tested separately.
            self.assertIsInstance(sentence_fragment, cas_parser.SentenceFragment,
                                  'Should be a SentenceFragment instance in order to be sure its content is correct')


class TestMain(unittest.TestCase):

    def test_keys(self):
        self.assertEqual(KEY_CHILDREN, cas_parser.KEY_CHILDREN, 'key value should match')
        self.assertEqual(KEY_VALUE, cas_parser.KEY_VALUE, 'key value should match')
        self.assertEqual(KEY_SENTENCE_FRAG_CLASS, cas_parser.KEY_SENTENCE_FRAG_CLASS, 'key value should match')

    def test_return(self):
        cas_content = cas_parser.CasContent.from_cas_file(path_cas, path_typesystem)

        self.assertIsInstance(cas_content, cas_parser.CasContent, 'CasContent is tested separately')

    def test_content(self):
        """ Get string representation of reporting obligation

        Returns:
            None
        """

        cas_content = cas_parser.CasContent.from_cas_file(path_cas, path_typesystem)

        ro0 = cas_content[KEY_CHILDREN][0]

        self.assertIsInstance(ro0, dict, 'all reporting obligation data should be contained in dictionary.')

        s = ro0[KEY_VALUE]

        self.assertIsInstance(s, str, 'reporting obligation is represented as string')

        with self.subTest("Segments contained in full reporting obligation."):
            for seg in ro0[KEY_CHILDREN]:
                self.assertIn(seg[KEY_VALUE], s)


if __name__ == '__main__':
    unittest.main()
