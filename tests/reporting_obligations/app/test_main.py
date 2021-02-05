import base64
import os
import unittest

import requests
from cassis import load_typesystem, load_cas_from_xmi
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from rdflib import Graph, Namespace
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID
from rdflib.plugins.stores.auditable import AuditableStore
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.store import Store

from dgfisma_rdf.reporting_obligations import cas_parser
from dgfisma_rdf.reporting_obligations.app.main import update_rdf_from_cas_content, app
from dgfisma_rdf.reporting_obligations.build_rdf import ROGraph

ROOT = os.path.join(os.path.dirname(__file__), '../../..')

load_dotenv(os.path.join(ROOT, 'secrets/dgfisma.env'))
SECRET_USER = os.getenv("FUSEKI_ADMIN_USERNAME")
SECRET_PASS = os.getenv("FUSEKI_ADMIN_PASSWORD")

"""
See <ROOT>/reporting_obligations/README.md OR 
<ROOT>/reporting_obligations/DockerDebugging/README.md + run_uvicorn.py
"""
if 0:
    LOCAL_URL = 'http://127.0.0.1:8081'
    URL_ENDPOINT = 'http://127.0.0.1:8080/fuseki/RO_test'  # Make sure to run fusek locally!
else:
    LOCAL_URL = 'http://gpu1.crosslang.com:10080'
    URL_ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_test'  # Make sure to run fusek locally!

URL_CAS_UPLOAD = LOCAL_URL + '/ro_cas/upload'
URL_CAS_B64 = LOCAL_URL + '/ro_cas/base64'

FILENAMES = (
    'cas_ro_plus_html2text.xml',
    'ro_cas_1.xml',  # non-empty
    'ro_cas_2.xml',  # empty
)

FILENAMES_FRANCOIS_ATTRIBUTES = (
    # 'oan_2021_01_18_N01.xml', # Bad xml
    # 'oan_2021_01_18_N02.xml', # Bad xml
    'oan_2021_01_18_N03.xml',  # Good xml
)

TEST_CLIENT = TestClient(app)


class TestApp(unittest.TestCase):
    def test_root(self):
        """ Test if root url can be accessed
        """
        r = requests.get(LOCAL_URL)

        self.assertLess(r.status_code, 300, "Status code should indicate a proper connection.")

    def test_docs(self):
        """ Test if open docs can be accessed
        """
        r = requests.get(LOCAL_URL + '/docs')

        self.assertLess(r.status_code, 300, "Status code should indicate a proper connection.")


class TestUpdateRDFFromCasContent(unittest.TestCase):

    def test_send_cas_without_reporting_obligations(self):
        path = os.path.abspath(os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', 'ro_cas_1.xml'))

        rel_path_typesystem = 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'
        path_typesystem = os.path.abspath(os.path.join(ROOT, rel_path_typesystem))

        cas_content = cas_parser.CasContent.from_cas_file(path, path_typesystem)

        # break up cas_content:

        def cas_content_iterator(cas_content):
            for cas_content_ro in cas_content['children']:
                cas_content_i = {'meta': cas_content['meta']}
                cas_content_i['children'] = [cas_content_ro]  # single RO

                yield cas_content_i

        for i, cas_content_i in enumerate(cas_content_iterator(cas_content)):
            with self.subTest(f'RO {i}'):
                try:
                    update_rdf_from_cas_content(cas_content_i, endpoint=URL_ENDPOINT, doc_id='example.com/doc/1')
                except Exception as e:
                    self.fail((e, cas_content_i))


class TestUploadCas(unittest.TestCase):
    def test_upload_file(self):
        path = os.path.join(ROOT, 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/ro + html2text.xml')
        with open(path, 'rb') as f:
            files = {'file': f}

            headers = {'endpoint': URL_ENDPOINT,
                       'docid': os.path.basename(path)}

            r = TEST_CLIENT.post(URL_CAS_UPLOAD, files=files, headers=headers)

        with self.subTest('status code'):
            self.assertLess(r.status_code, 300, "Status code should indicate a proper connection.")

        with self.subTest('cas content'):
            cas_content = r.json()

            s_cls = set([child['class'] for chldrn in cas_content['children'] if
                         chldrn['children'] for child in chldrn['children']])

            self.assertTrue(len(s_cls), 'Sanity check: reporting obligations should not be empty')

            for cls in s_cls:
                self.assertTrue('arg' in cls.lower() or 'v' == cls.lower(), 'Not one of expected entity classes')

    def test_upload_example_files(self):

        for filename in FILENAMES:
            path = os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', filename)

            with open(path, 'rb') as f:
                files = {'file': f}

                headers = {'endpoint': URL_ENDPOINT,
                           'docid': filename}

                r = TEST_CLIENT.post(URL_CAS_UPLOAD, files=files, headers=headers)

            self.assertLess(r.status_code, 300, "Status code should indicate a proper connection.")

            with self.subTest(f'cas content: {filename}'):
                cas_content = r.json()

                s_cls = set([child['class'] for chldrn in cas_content['children'] if
                             chldrn['children'] for child in chldrn['children']])

                if 'ro_cas_1' not in filename:  # This CAS has the wrong view
                    for cls in s_cls:
                        self.assertTrue('arg' in cls.lower() or 'v' == cls.lower(),
                                        f'Not one of expected entity classes: {cls}')

            with self.subTest(f'Entities: {filename}'):

                if 'ro_cas_2' in filename:
                    self.assertFalse(s_cls, 'There should be no entities in this CAS.')
                else:
                    self.assertTrue(s_cls, 'We expected some entities to be found.')

    def test_upload_example_files_v2(self):
        """ New attributes have been added that seem to cause issues.

        Returns:

        """

        for filename in FILENAMES_FRANCOIS_ATTRIBUTES:
            path = os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', filename)

            with open(path, 'rb') as f:
                files = {'file': f}

                values = {'docid': str(filename),
                          'endpoint': URL_ENDPOINT,
                          }

                r = TEST_CLIENT.post(URL_CAS_UPLOAD,
                                     files=files,
                                     headers=values
                                     )

            with self.subTest(f'Status code: {filename}'):
                self.assertLess(r.status_code, 300, r.text)
            if r.status_code >= 300:
                continue

            with self.subTest(f'cas content: {filename}'):
                cas_content = r.json()

                s_cls = set([child['class'] for chldrn in cas_content['children'] if
                             chldrn['children'] for child in chldrn['children']])

                for cls in s_cls:
                    self.assertTrue('arg' in cls.lower() or 'v' == cls.lower(),
                                    f'Not one of expected entity classes: {cls}')

            with self.subTest(f'Entities: {filename}'):
                self.assertTrue(s_cls, 'COULD BE FALSE ALARM, but we expected some entities to be found')


class TestUploadCasB64(unittest.TestCase):
    """
    Upload Base 64 cas
    """

    def test_upload_file(self):
        path = os.path.join(ROOT, 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/ro + html2text.xml')

        rel_path_typesystem = 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'
        path_typesystem = os.path.join(ROOT, rel_path_typesystem)

        with open(path, 'rb') as f:
            with open(path_typesystem, 'rb') as f_ts:
                typesystem = load_typesystem(f_ts)

            cas = load_cas_from_xmi(f, typesystem=typesystem)

            encoded_cas = base64.b64encode(bytes(cas.to_xmi(), 'utf-8')).decode()

            values = {'content': encoded_cas,
                      }
            headers = {'endpoint': URL_ENDPOINT,
                       'docid': os.path.basename(path)}

            r = TEST_CLIENT.post(URL_CAS_B64, json=values,
                                 headers=headers
                                 )

        with self.subTest('status code'):
            self.assertLess(r.status_code, 300, "Status code should indicate a proper connection.")

        with self.subTest('cas content'):
            cas_content = r.json()

            s_cls = set([child['class'] for chldrn in cas_content['children'] if
                         chldrn['children'] for child in chldrn['children']])

            for cls in s_cls:
                self.assertTrue('arg' in cls.lower() or 'v' == cls.lower(),
                                'Not one of expected entity classes')

        return r


class TestUID(unittest.TestCase):
    """ Unique identifiers should be added and retrieved by the RDF to get the different catalogue documents and reporting obligations.
    """

    def test_retrieve_ids(self):
        for filename in FILENAMES:

            path = os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', filename)

            with open(path, 'rb') as f:
                files = {'file': f}
                headers = {'endpoint': URL_ENDPOINT,
                           'docid': 'f6e61f10-d970-5b20-83ca-cb3a76d74eaf'}  # Example doc_id
                r = TEST_CLIENT.post(URL_CAS_UPLOAD, files=files,
                                     headers=headers)

            if r.status_code >= 300:  # uploading failed
                with self.subTest('POST request'):
                    self.fail('Uploading failed')
                continue

            cas_content = r.json()

            with self.subTest('Catalogue document'):
                self.assertTrue(cas_content.get('id'),
                                f'cas_content should contain ID for the catalogue document: {cas_content.keys()}')

            l_ro = cas_content.get('children')
            with self.subTest('Reporting obligations'):

                if 'cas_2' in filename:  # empty cas
                    self.assertFalse(len(l_ro), f"CAS shouldn't contain any reporting obligations.")
                    continue

                else:
                    self.assertTrue(len(l_ro), f'Sanity check: should return reporting obligations. {l_ro}')
                    self.assertTrue(all(l_ro_i.get('id') for l_ro_i in l_ro),
                                    f'cas_content should contain ID for each reporting obligation')

            l_ent = [ent_j for l_ro_i in l_ro for ent_j in l_ro_i.get('children')]
            with self.subTest('Entities'):

                self.assertTrue(len(l_ent), f'Sanity check: should return entities. {l_ent}')
                self.assertTrue(all(l_ent_j.get('id') for l_ent_j in l_ent),
                                f'cas content should contain ID for each reporting obligation entity')


class UpdateReportingObligations(unittest.TestCase):
    def test_add_2_similar(self):
        l0 = [{cas_parser.KEY_CHILDREN: [{cas_parser.KEY_VALUE: 'v',
                                          cas_parser.KEY_SENTENCE_FRAG_CLASS: 'g'
                                          }
                                         ],
               cas_parser.KEY_VALUE: 'full v!!'
               }
              ]

        l1 = [{cas_parser.KEY_CHILDREN: [{cas_parser.KEY_VALUE: 'v_other',
                                          cas_parser.KEY_SENTENCE_FRAG_CLASS: 'g_other'
                                          },
                                         {cas_parser.KEY_VALUE: 'some other v',
                                          cas_parser.KEY_SENTENCE_FRAG_CLASS: 'and g'
                                          },
                                         ],
               cas_parser.KEY_VALUE: 'full v!!'  # Same string representation
               }
              ]

        cas_content0 = cas_parser.CasContent.from_list(l0)

        cas_content1 = cas_parser.CasContent.from_list(l1)

        cas_content0_update = update_rdf_from_cas_content(cas_content0,
                                                          endpoint=URL_ENDPOINT,
                                                          doc_id='test123')

        # TODO check if CAS_content0 is correctly updated

        # TODO check if ENDPOINT contains correct data

        cas_content1_update = update_rdf_from_cas_content(cas_content1,
                                                          endpoint=URL_ENDPOINT,
                                                          doc_id='test123')

        # TODO check if CAS_content1 is correctly updated

        # TODO check if ENDPOINT is updated: old data gone, new data there.

        return

    def test_files(self):
        rel_path_typesystem = 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'
        path_typesystem = os.path.abspath(os.path.join(ROOT, rel_path_typesystem))

        for filename in FILENAMES:
            path = os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', filename)

            # with open(path, 'rb') as f:
            #     files = {'file': f}
            #
            #     headers = {'endpoint': URL_ENDPOINT,
            #                'docid': filename}
            #
            #     r = TEST_CLIENT.post(URL_CAS_UPLOAD, files=files, headers=headers)

            cas_content0 = cas_parser.CasContent.from_cas_file(path,
                                                               path_typesystem)

            cas_content0_update = update_rdf_from_cas_content(cas_content0,
                                                              endpoint=URL_ENDPOINT,
                                                              doc_id='test123')

            self.assertTrue(cas_content0_update)

        return


class TestRDFStore(unittest.TestCase):
    EX = Namespace("http://example.org/")

    def test_foo(self):

        sparql_update_store = SPARQLUpdateStore(  # queryEndpoint=endpoint,
            # update_endpoint=endpoint + '/update',  # Might have to add "/update"
            autocommit=False)

        auditable_store = AuditableStore(sparql_update_store)

        # r = auditable_store.query("""select ?a where {?a ?b ?c}""")

        default_graph = None  # RO_BASE[None]

        g_without_store = ROGraph(  # store=auditable_store,
            # identifier=default_graph
        )

        print('#Triples graph without a store =', len(g_without_store))

        # p_rdf = os.path.join(ROOT, 'data/examples/reporting_obligations_mockup.rdf')

        if 0:
            store = Store()

            g_store = ROGraph(store=store,
                              # identifier=default_graph

                              )

            print('#Triples graph =', len(g_store))

        g_base = Graph()
        # self.g.add((EX.s0, EX.p0, EX.o0))
        # self.g.add((EX.s0, EX.p0, EX.o0bis))

        with self.subTest('AuditableStore'):
            g_base_RO = ROGraph()

            t_base_RO = ROGraph(AuditableStore(g_base_RO.store),
                                g_base_RO.identifier)

    def test_rollback(self):
        """
        Test how to implement a rollback
        Returns:

        """

        g_base = Graph()

        with self.subTest('init'):
            self.assertEqual(len(g_base), 0, 'Should be empty')

        t_base = ROGraph(AuditableStore(g_base.store),
                         g_base.identifier)

        n_g = len(t_base)

        t_base.add((self.EX.s0, self.EX.p0, self.EX.o0))
        t_base.add((self.EX.s0, self.EX.p0, self.EX.o0bis))

        with self.subTest('add'):
            self.assertGreater(len(t_base), n_g, 'graph should increase in size')

        t_base.rollback()

        with self.subTest('rollback'):
            self.assertEqual(len(t_base), n_g, 'graph size should be restored in size')

        return

    def test_flush_the_stack(self):
        """
        By commiting you can't do a rollback anymore

        Returns:

        """

        g_base = Graph()

        with self.subTest('init'):
            self.assertEqual(len(g_base), 0, 'Should be empty')

        t_base = ROGraph(AuditableStore(g_base.store),
                         g_base.identifier)

        n_g = len(t_base)

        t_base.add((self.EX.s0, self.EX.p0, self.EX.o0))
        t_base.add((self.EX.s0, self.EX.p0, self.EX.o0bis))

        with self.subTest('add'):
            self.assertGreater(len(t_base), n_g, 'graph should increase in size')

        t_base.commit()

        t_base.rollback()

        with self.subTest("rollback shouldn't work"):
            self.assertGreater(len(t_base), n_g, 'graph size should be restored in size')

        return

    def setUp(self) -> None:
        self.g = ROGraph()
        self.t = Graph(AuditableStore(self.g.store),
                       self.g.identifier)

    def test_rollback_if_crash(self):
        """ Rollback should only occur when it crashes. Example on how to implement this.

        Returns:

        """

        try:

            n_t = len(self.t)

            self.t.add((self.EX.s0, self.EX.p0, self.EX.o0))

            n_t_new = len(self.t)

            self.assertNotEqual(n_t, n_t_new, 'Sanity check. Size should increase')

            raise ValueError('Let it crash.')

        except ValueError as e:

            self.t.rollback()

            self.assertEqual(len(self.t), n_t, 'Graph should be restored')

        else:
            # If it doesn't crash, flush the saved changes.
            # TOOD to be used in other test.
            self.t.commit()

            n_before = len(self.t)

            self.t.rollback()

            self.assertEqual(len(self.t), n_before, "Rollback shouldn't do anything.")

        return

    def test_no_rollback_if_no_crash(self):
        """ Rollback should only occur when it crashes. Example on how to implement this.

        Returns:

        """

        try:

            n_t = len(self.t)

            self.t.add((self.EX.s0, self.EX.p0, self.EX.o0))

            n_t_new = len(self.t)

            self.assertNotEqual(n_t, n_t_new, 'Sanity check. Size should increase')

        except Exception as e:

            raise self.fail(f"Shouldn't crash!\n{e}")

        else:
            # If it doesn't crash, flush the saved changes.
            self.t.commit()
            n_before = len(self.t)
            self.assertEqual(n_before, n_t_new, "Sanity check. Commit shouldn't do anything.")

            self.t.rollback()
            self.assertEqual(len(self.t), n_before, "Rollback shouldn't do anything anymore.")

        return

    def test_rollback_with_endpoint(self):

        sparql_update_store = SPARQLUpdateStore(queryEndpoint=URL_ENDPOINT,
                                                update_endpoint=URL_ENDPOINT + '/update',  # Might have to add "/update"
                                                auth=(SECRET_USER, SECRET_PASS)
                                                )

        # Init with schema
        g = ROGraph(sparql_update_store,
                    DATASET_DEFAULT_GRAPH_ID,
                    include_schema=True)

        # Without an identifier it won't work.
        t = Graph(AuditableStore(g.store),
                  DATASET_DEFAULT_GRAPH_ID,
                  )

        # Make sure this triple doesn't exist before.
        t.remove((self.EX.s0, self.EX.p0, self.EX.o0))
        t.commit()

        try:

            n_t = len(t)

            t.add((self.EX.s0, self.EX.p0, self.EX.o0))

            n_t_new = len(t)

            with self.subTest('Sanity check'):
                self.assertNotEqual(n_t, n_t_new, 'Sanity check. Size should increase')

            raise InterruptedError('Let it crash.')

        except InterruptedError as e:

            t.rollback()

            with self.subTest('Rollback'):
                self.assertEqual(len(t), n_t, 'Graph should be restored')

        return


if __name__ == '__main__':
    unittest.main()
