"""
Tests for accessing create RDF API, with focus on adding document source info
"""

import os
import unittest

from dotenv import load_dotenv
from fastapi.testclient import TestClient

from dgfisma_rdf.reporting_obligations.app.main import app, get_sparql_update_graph

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

load_dotenv(os.path.join(ROOT, 'secrets/dgfisma.env'))
SECRET_USER = os.getenv("FUSEKI_ADMIN_USERNAME")
SECRET_PASS = os.getenv("FUSEKI_ADMIN_PASSWORD")

"""
See <ROOT>/reporting_obligations/README.md OR
<ROOT>/reporting_obligations/DockerDebugging/README.md + run_uvicorn.py
"""
b_local = False
if b_local:
    LOCAL_URL = 'http://127.0.0.1:8081'
    URL_ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_test/query'  # /query'
    UPDATE_ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_test/update'

else:
    LOCAL_URL = 'http://gpu1.crosslang.com:10080'
    URL_ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_test/query'
    UPDATE_ENDPOINT = 'http://gpu1.crosslang.com:3030/RO_test/update'

# # Make sure this a test version of production!
# ENDPOINT_PRD = 'http://gpu1.crosslang.com:3030/RO_prd_clone/query'
# UPDATE_ENDPOINT_PRD = 'http://gpu1.crosslang.com:3030/RO_prd_clone/update'
#
# URL_CAS_UPLOAD = LOCAL_URL + '/ro_cas/upload'
# URL_CAS_B64 = LOCAL_URL + '/ro_cas/base64'
#
# FILENAMES = (
#     'cas_ro_plus_html2text.xml',
#     'ro_cas_1.xml',  # non-empty
#     'ro_cas_2.xml',  # empty
# )
#
# FILENAMES_FRANCOIS_ATTRIBUTES = (
#     # 'oan_2021_01_18_N01.xml', # Bad xml
#     # 'oan_2021_01_18_N02.xml', # Bad xml
#     'oan_2021_01_18_N03.xml',  # Good xml
# )

TEST_CLIENT = TestClient(app)


class TestAddDocSource(unittest.TestCase):
    URL_DOC_SOURCE_ADD = "/doc_source/add"

    def test_add_doc_source(self):
        g_base = get_sparql_update_graph(URL_ENDPOINT,
                                         UPDATE_ENDPOINT)

        #     path = os.path.join(ROOT, 'dgfisma_rdf/reporting_obligations/output_reporting_obligations/ro + html2text.xml')
        #     with open(path, 'rb') as f:
        #         files = {'file': f}

        # TODO continue working on in other test
        # g_base.remove_doc_source(doc_id=doc_id)

        headers = {
            'source-name': '#todo test',
            'docid': '#todo test',
            'endpoint': URL_ENDPOINT,
            'updateendpoint': UPDATE_ENDPOINT,
            # 'docid': os.path.basename(path)
        }

        r = TEST_CLIENT.post(self.URL_DOC_SOURCE_ADD,
                             headers=headers)

        with self.subTest('status code'):
            s = f'Status code: {r.status_code}\n{r.content}'
            self.assertLess(r.status_code, 300,
                            f"Status code should indicate a proper connection.\n{s}")

    #     with self.subTest('cas content'):
    #         cas_content = r.json()
    #
    #         s_cls = set([child['class'] for chldrn in cas_content['children'] if
    #                      chldrn['children'] for child in chldrn['children']])
    #
    #         self.assertTrue(len(s_cls), 'Sanity check: reporting obligations should not be empty')
    #
    #         for cls in s_cls:
    #             self.assertTrue('arg' in cls.lower() or 'v' == cls.lower(), 'Not one of expected entity classes')
    #
    # def test_upload_example_files(self):
    #
    #     for filename in FILENAMES:
    #         path = os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', filename)
    #
    #         with open(path, 'rb') as f:
    #             files = {'file': f}
    #
    #             headers = {'endpoint': URL_ENDPOINT,
    #                        'updateendpoint': UPDATE_ENDPOINT,
    #                        'docid': filename}
    #
    #             r = TEST_CLIENT.post(URL_CAS_UPLOAD, files=files, headers=headers)
    #
    #         s = f'Status code: {r.status_code}\n{r.content}'
    #         self.assertLess(r.status_code, 300, f"Status code should indicate a proper connection.\n{s}")
    #
    #         with self.subTest(f'cas content: {filename}'):
    #             cas_content = r.json()
    #
    #             s_cls = set([child['class'] for chldrn in cas_content['children'] if
    #                          chldrn['children'] for child in chldrn['children']])
    #
    #             if 'ro_cas_1' not in filename:  # This CAS has the wrong view
    #                 for cls in s_cls:
    #                     self.assertTrue('arg' in cls.lower() or 'v' == cls.lower(),
    #                                     f'Not one of expected entity classes: {cls}')
    #
    #         with self.subTest(f'Entities: {filename}'):
    #
    #             if 'ro_cas_2' in filename:
    #                 self.assertFalse(s_cls, 'There should be no entities in this CAS.')
    #             else:
    #                 self.assertTrue(s_cls, 'We expected some entities to be found.')
    #
    # def test_upload_example_files_v2(self):
    #     """ New attributes have been added that seem to cause issues.
    #
    #     Returns:
    #
    #     """
    #
    #     for filename in FILENAMES_FRANCOIS_ATTRIBUTES:
    #         path = os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', filename)
    #
    #         with open(path, 'rb') as f:
    #             files = {'file': f}
    #
    #             values = {'docid': str(filename),
    #                       'endpoint': URL_ENDPOINT,
    #                       'updateendpoint': UPDATE_ENDPOINT,
    #                       }
    #
    #             r = TEST_CLIENT.post(URL_CAS_UPLOAD,
    #                                  files=files,
    #                                  headers=values
    #                                  )
    #
    #         with self.subTest(f'Status code: {filename}'):
    #             s = f'Status code: {r.status_code}\n{r.content}'
    #             self.assertLess(r.status_code, 300, s)
    #         if r.status_code >= 300:
    #             continue
    #
    #         with self.subTest(f'cas content: {filename}'):
    #             cas_content = r.json()
    #
    #             s_cls = set([child['class'] for chldrn in cas_content['children'] if
    #                          chldrn['children'] for child in chldrn['children']])
    #
    #             for cls in s_cls:
    #                 self.assertTrue('arg' in cls.lower() or 'v' == cls.lower(),
    #                                 f'Not one of expected entity classes: {cls}')
    #
    #         with self.subTest(f'Entities: {filename}'):
    #             self.assertTrue(s_cls, 'COULD BE FALSE ALARM, but we expected some entities to be found')
