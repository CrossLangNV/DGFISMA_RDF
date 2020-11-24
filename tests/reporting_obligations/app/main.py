import base64
import os
import unittest

import requests
from cassis import load_typesystem, load_cas_from_xmi

from reporting_obligations import cas_parser
from reporting_obligations.app.main import update_rdf_from_cas_content

ROOT = os.path.join(os.path.dirname(__file__), '../../..')

"""
See <ROOT>/reporting_obligations/README.md OR 
<ROOT>/reporting_obligations/DockerDebugging/README.md + run_uvicorn.py
"""
LOCAL_URL = 'http://127.0.0.1:8080'
URL_CAS_UPLOAD = LOCAL_URL + '/ro_cas/upload'
URL_CAS_B64 = LOCAL_URL + '/ro_cas/base64'

FILENAMES = ('ro_cas_1.xml',  # non-empty
             'ro_cas_2.xml',  # empty
             'cas_ro_plus_html2text.xml'
             )


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
        path = os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', 'ro_cas_1.xml')

        rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'
        path_typesystem = os.path.join(ROOT, rel_path_typesystem)

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
                    update_rdf_from_cas_content(cas_content_i)
                except Exception as e:
                    self.fail((e, cas_content_i))


class TestUploadCas(unittest.TestCase):
    def test_upload_file(self):
        path = os.path.join(ROOT, 'reporting_obligations/output_reporting_obligations/ro + html2text.xml')
        with open(path, 'rb') as f:
            files = {'file': f}

            r = requests.post(URL_CAS_UPLOAD, files=files)

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
            with self.subTest(filename):
                path = os.path.join(ROOT, 'tests/reporting_obligations/app/data_test', filename)

                with open(path, 'rb') as f:
                    files = {'file': f}

                    r = requests.post(URL_CAS_UPLOAD, files=files)

                self.assertLess(r.status_code, 300, "Status code should indicate a proper connection.")

                with self.subTest('cas content'):
                    cas_content = r.json()

                    s_cls = set([child['class'] for chldrn in cas_content['children'] if
                                 chldrn['children'] for child in chldrn['children']])

                    for cls in s_cls:
                        self.assertTrue('arg' in cls.lower() or 'v' == cls.lower(),
                                        f'Not one of expected entity classes: {cls}')


class TestUploadCasB64(unittest.TestCase):
    """
    Upload Base 64 cas
    """

    def test_upload_file(self):
        path = os.path.join(ROOT, 'reporting_obligations/output_reporting_obligations/ro + html2text.xml')

        rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'
        path_typesystem = os.path.join(ROOT, rel_path_typesystem)

        with open(path, 'rb') as f:
            with open(path_typesystem, 'rb') as f_ts:
                typesystem = load_typesystem(f_ts)

            cas = load_cas_from_xmi(f, typesystem=typesystem)

            encoded_cas = base64.b64encode(bytes(cas.to_xmi(), 'utf-8')).decode()

            values = {'content': encoded_cas}

            r = requests.post(URL_CAS_B64, json=values)

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
                r = requests.post(URL_CAS_UPLOAD, files=files)

            if r.status_code >= 300:  # uploading failed
                continue

            cas_content = r.json()

            with self.subTest('Catalogue document'):
                self.assertTrue(cas_content.get('id'),
                                f'cas_content should contain ID for the catalogue document: {cas_content.keys()}')

            l_ro = cas_content.get('children')
            with self.subTest('Reporting obligations'):

                self.assertTrue(len(l_ro), f'Sanity check: should return reporting obligations. {l_ro}')
                self.assertTrue(all(l_ro_i.get('id') for l_ro_i in l_ro),
                                f'cas_content should contain ID for each reporting obligation')

            l_ent = [ent_j for l_ro_i in l_ro for ent_j in l_ro_i.get('children')]
            with self.subTest('Entities'):

                self.assertTrue(len(l_ent), f'Sanity check: should return entities. {l_ent}')
                self.assertTrue(all(l_ent_j.get('id') for l_ent_j in l_ent),
                                f'cas content should contain ID for each reporting obligation entity')

    def test_id_to_every_node(self):
        """ Every node should have an unique id to

        Returns:

        """

        with self.subTest('Uniqueness'):
            # TODO
            pass

        with self.subTest('ID for every node'):
            # TODO
            pass

    def test_retrieve_info_based_on_id(self):
        """ After filling the RDF and retrieving the ID's, the same information should be able to be extracted based on this ID.

        Returns:

        """

        # TODO


if __name__ == '__main__':
    unittest.main()
