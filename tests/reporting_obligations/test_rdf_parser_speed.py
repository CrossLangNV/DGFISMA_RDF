"""
For the production server it became clear that speed becomes an issue.

These tests are aimed to test the speed of different components and as such will take much longer to complete.
"""

import os
import random
import time
import unittest

import numpy as np
from rdflib.term import URIRef

from dgfisma_rdf.reporting_obligations import build_rdf
from dgfisma_rdf.reporting_obligations.rdf_parser import SPARQLReportingObligationProvider, SPARQLGraphWrapper

ROOT = os.path.join(os.path.dirname(__file__), '../..')

# You might have to change this
URL_FUSEKI_PRD = "http://gpu1.crosslang.com:3030/RO_prd_clone"


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

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI_PRD)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_speed(self):

        n_samples = 10

        l_types_ent = self.prov.get_different_entity_types()

        s_test = 'querying without filter'
        with self.subTest(s_test):
            print(s_test)

            l_T = []
            for type_ent_i in random.sample(l_types_ent, n_samples):
                t0 = time.time()
                self.prov.get_filter_entities_from_type(type_ent_i)
                t1 = time.time()

                l_T.append(t1 - t0)

            print(f'T query = {np.mean(l_T):.2f} +- {np.std(l_T):.2f} s')

        s_test = 'querying with filter'
        with self.subTest(s_test):
            print(s_test)

            l_T = []
            for type_ent_i in random.sample(l_types_ent, n_samples):
                type_ent_j = _sample_single(l_types_ent)
                l_ent_j = self.prov.get_all_from_type(type_ent_j)
                if len(l_ent_j) == 0:
                    continue  # Could be empty
                ent_j = _sample_single(l_ent_j)

                t0 = time.time()
                r = self.prov.get_filter_entities_from_type(type_ent_i,
                                                            [(type_ent_j, ent_j)])
                t1 = time.time()

                l_T.append(t1 - t0)

            print(f'T query = {np.mean(l_T):.2f} +- {np.std(l_T):.2f} s')


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

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI_PRD)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_speed(self):
        n_samples = 10

        l_types_ent = self.prov.get_different_entity_types()

        if 0:  # Bad idea as this is incredibly slow!
            s_test = 'querying without filter'
            with self.subTest(s_test):
                print(s_test)

                l_T = []
                for _ in range(n_samples):
                    t0 = time.time()
                    r = self.prov.get_filter_entities()
                    t1 = time.time()

                    l_T.append(t1 - t0)

                print(f'T query = {np.mean(l_T):.2f} s')

        s_test = 'querying with filter'
        with self.subTest(s_test):
            print(s_test)

            l_T = []
            for type_ent_i in random.sample(l_types_ent, n_samples):
                l_ent_i = self.prov.get_all_from_type(type_ent_i)
                if len(l_ent_i) == 0:
                    # Entity type without entities. E.g. hasPropGol
                    continue

                ent_i = _sample_single(l_ent_i)

                t0 = time.time()
                r = self.prov.get_filter_entities([(type_ent_i, ent_i)])
                t1 = time.time()

                l_T.append(t1 - t0)

            print(f'T query = {np.mean(l_T):.2f} s')


class TestGetAllFromType(unittest.TestCase):

    def setUp(self) -> None:

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI_PRD)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

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


class TestGetEntities(unittest.TestCase):
    def setUp(self) -> None:

        graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI_PRD)
        self.prov = SPARQLReportingObligationProvider(graph_wrapper)

    def test_speed(self):
        n_samples = 1

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


def _sample_single(l):
    return list(random.sample(l, 1))[0]
