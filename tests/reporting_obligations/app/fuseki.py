"""
By added a (network) fridge to Fuseki, it should be possible to query now to fuseki jena container
"""

import os
import unittest

import requests
from SPARQLWrapper import SPARQLWrapper, JSON

ROOT = os.path.join(os.path.dirname(__file__), '../../..')

if 0:  # Running local and connect through ssh tunneling
    LOCAL_URL = 'http://localhost:3030/'
else:
    # From >> docker inspect ROnetwork
    # LOCAL_URL = 'http://172.18.0.2:3030/'

    # Easier to just use the name
    LOCAL_URL = 'http://fuseki_RO:3030/'


class TestApp(unittest.TestCase):
    def test_root(self):
        """ Test if root url can be accessed
        """

        r = requests.get(LOCAL_URL)

        with self.subTest('Status code'):
            self.assertLess(r.status_code, 300, "Status code should indicate a proper connection.")
        with self.subTest('Content'):
            self.assertTrue(r.content, "Should be non-empty")

    def test_dataset(self):
        r = requests.get(LOCAL_URL + 'dataset.html')

        with self.subTest('Status code'):
            self.assertLess(r.status_code, 300, "Status code should indicate a proper connection.")
        with self.subTest('Content'):
            self.assertTrue(r.content, "Should be non-empty")

    def test_endpoint(self):
        # RO is the dataset name
        sparql = SPARQLWrapper(LOCAL_URL + 'RO')
        sparql.setQuery("""
            SELECT ?subject ?predicate ?object
            WHERE {
              ?subject ?predicate ?object
            }
            LIMIT 25
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        with self.subTest("non-empty"):
            self.assertTrue(results, "Should be non-emtpy")

        with self.subTest("bindings"):
            bindings = results['results']['bindings']
            self.assertTrue(bindings, "Should be non-emtpy")
