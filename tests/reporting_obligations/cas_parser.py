import os
import unittest

from reporting_obligations import cas_parser

ROOT = os.path.join(os.path.dirname(__file__), '../..')
# fixed example.
rel_path_cas = 'reporting_obligations/output_reporting_obligations/cas_laurens.xml'
rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'

# from ROOT
path_cas = os.path.join(ROOT, rel_path_cas)
path_typesystem = os.path.join(ROOT, rel_path_typesystem)

KEY_CHILD = 'value'
KEY_SENTENCE_FRAG_CLASS = 'class'


class TestSentenceFragment(unittest.TestCase):

    def test_return(self):
        v = 'v'
        c = 'c'
        sentence_fragment = cas_parser.SentenceFragment.from_value_class(v=v, c=c)

        self.assertEqual(set((KEY_SENTENCE_FRAG_CLASS, KEY_CHILD)), set(sentence_fragment.keys()))
        self.assertEqual(v, sentence_fragment[KEY_CHILD])
        self.assertEqual(c, sentence_fragment[KEY_SENTENCE_FRAG_CLASS])


class TestCasContent(unittest.TestCase):

    def test_return(self):
        l = [[{KEY_CHILD: 'v',
               KEY_SENTENCE_FRAG_CLASS: 'g'
               }
              ]
             ]

        cas_content = cas_parser.CasContent.from_list(l)

        self.assertIsInstance(cas_content, dict, 'cas content should be a dictionary-like object')

        reporting_obligation_list = cas_content[KEY_CHILD]
        self.assertIsInstance(reporting_obligation_list, list, 'reporting obligations should be list.')
        self.assertTrue(len(reporting_obligation_list), 'Should be non-empty')

        reporting_obligation_content = reporting_obligation_list[0]
        self.assertIsInstance(reporting_obligation_content, list, 'reporting obligation should be a list.')

        sentence_fragment = reporting_obligation_content[0]

        self.assertIsInstance(sentence_fragment, dict, 'sentence fragment should be a dictionary.')
        # Sentence Fragment class is tested separately.
        self.assertIsInstance(sentence_fragment, cas_parser.SentenceFragment,
                              'Should be a SentenceFragment instance in order to be sure its content is correct')


class TestMain(unittest.TestCase):

    def test_key(self):
        self.assertEqual(KEY_CHILD, cas_parser.KEY_CHILD, 'key value should match')

    def test_return(self):
        cas_content = cas_parser.main(path_cas, path_typesystem)

        self.assertIsInstance(cas_content, cas_parser.CasContent, 'CasContent is tested separately')


if __name__ == '__main__':
    unittest.main()
