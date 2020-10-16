from typing import List

from SPARQLWrapper import SPARQLWrapper, JSON

URL = 'http://localhost:8080/fuseki/DGFisma'  # make sure port number is correct.


class EuroVocRDFWrapper:
    def __init__(self):
        self.sparql = SPARQLWrapper(URL)
        self.sparql.setReturnFormat(JSON)

    def get_definitions(self) -> dict:

        k_subject = 'subject'
        k_label = 'label'
        k_definition = 'definition'

        # only check english labels and definitions
        query_string = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    
            SELECT ?{k_label} ?{k_definition} ?{k_subject} ?language
                    WHERE {{
                    ?{k_subject} skos:prefLabel ?{k_label} .
                    BIND (lang(?{k_label}) AS ?language)
                    OPTIONAL {{
                        ?{k_subject} skos:definition ?{k_definition} .
                    
                        FILTER (
                        lang(?{k_definition}) = 'en'
            
                        )
                    }}
                
                    FILTER (
                        lang(?{k_label}) = 'en'
            
                        )
                    }}
                    ORDER BY ?{k_label}
        """

        results = self.getter(query_string)

        assert k_subject in results['head']['vars']

        # Types of values: Can be either uri or literal
        l_types = set()
        for result in results["results"]["bindings"]:

            for _, v in result.items():
                l_types.add(v['type'])

        d = {}
        for result in results["results"]["bindings"]:
            # Should be unique. If not it's problem for who made the database
            id = result[k_subject]['value']  # should be a uri (as it's a subject)
            label = result[k_label]['value']  # should be a literal

            d[id] = label

        return d

    def getter(self, query_string, *args, **kwargs):

        if self.sparql.method != 'GET':
            self.sparql.method = 'GET'
        self.sparql.setQuery(query_string)

        results = self.sparql.query().convert()

        return results

    def poster(self, query_string):

        if self.sparql.method != 'POST':
            self.sparql.method = 'POST'
        self.sparql.setQuery(query_string)

        results = self.sparql.query().convert()

        return results

    def add_triplets(self, l_triple: List[tuple]):

        # TODO group per subject

        # Crazy slow to make the strings!
        if 0:
            for s in set(s for s, *_ in l_triple):
                _, l_p, l_o = (zip(*filter(lambda t: t[0] == s, l_triple)))

                s_query = ''
                for i, (p, o) in enumerate(zip(l_p, l_o)):

                    if i == 0:
                        s_query += f'<{s}> '
                    else:
                        s_query += f'\t'

                    s_query += f'<{p}>'

                    # object:
                    try:
                        float(o)
                    except ValueError:
                        s_query += f' <{o}>'
                    else:
                        o_num = float(o)
                        if o_num.is_integer():
                            s_query += f' "{int(o_num)}"'
                        else:
                            s_query += f' "{o_num}"'

                    if i != len(l_p) - 1:
                        s_query += ' ;'
                    else:
                        s_query += ' .'

                    s_query += '\n'

                query_string = f"""
                INSERT DATA
                {{
                {s_query}
                }}
                """

                self.poster(query_string)

        elif 0:
            for triple in l_triple:
                s, p, o = triple

                query_string = f"""
                INSERT {{ <{s}> <{p}> <{o}> }}
                """

                self.getter(query_string)

        elif 1:
            # In batches:
            n_batch = 2 ** 10

            n_done = 0
            for i_start in range(0, len(l_triple), n_batch):
                l_triple_batch = l_triple[i_start:i_start + n_batch]

                l_query = []

                for s, p, o in l_triple_batch:

                    s_query_i = f'<{s}> <{p}>'
                    # object:
                    try:
                        float(o)
                    except ValueError:
                        s_query_i += f' <{o}>'
                    else:
                        o_num = float(o)
                        if o_num.is_integer():
                            s_query_i += f' "{int(o_num)}"'
                        else:
                            s_query_i += f' "{o_num}"'

                    s_query_i += f' .'

                    l_query.append(s_query_i)

                n_done += len(l_query)

                s_query = '\n'.join(l_query)

                query_string = f"""
                INSERT DATA {{ {s_query} }}
                """

                self.poster(query_string)

            assert n_done == len(l_triple), 'Something missed in batch loader'

        return


def main(k_sim=25  # to limit amount of pairs!
         ):
    """
    * [ ] Get terms/definitions or something
    save both the subjects and values/label as to be able to add in the end!

    * [ ] find their closest match
    * [ ] Inference: if term1 and term2 lead to a high score, save as close match with a score.
    Other option is to link k nearest neighbours, then you can order words, but there is a one to many relationship.

    * [ ] Add to RDF (ideally temporarily)

    Returns:

    """

    # get definitions

    eurovoc_rdf_wrapper = EuroVocRDFWrapper()
    defs = eurovoc_rdf_wrapper.get_definitions()  # labels/terms is something for later.

    # TODO non-local!!!
    path = 'C:/Users/laure/PycharmProjects/crosslang/DGFISMA_term_extraction'

    import sys
    # the mock-0.3.1 dir contains testcase.py, testutils.py & mock.py
    sys.path.append(path)
    from similar_terms.methods import SimilarWordsRetriever

    # load model
    sim_word_retriever = SimilarWordsRetriever(defs.values())

    triplets = []
    id_close_match = 0
    for k, v in defs.items():
        # sims = sim_word_retriever.get_similar_thresh(v,thresh)
        sims = sim_word_retriever.get_similar_k(v, k_sim)

        for i, (orig_term, score) in enumerate(zip(sims['original terms'], sims['score'])):
            # build triplets
            # TODO use better names for predicates and subjects
            # TODO now contains everything twice! But I'll save order, even if it doesn't make sense
            uri_orig_term = [k_j for k_j, v_j in defs.items() if v_j == orig_term][0]

            # Should be like an abstract subject
            l_close_match = [
                (f'close_match:{id_close_match}', 'word', k),
                (f'close_match:{id_close_match}', 'word', uri_orig_term),
                (f'close_match:{id_close_match}', 'score', score),
                (f'close_match:{id_close_match}', 'order', i),
            ]

            triplets += l_close_match

            id_close_match += 1

    if 0:  # TODO set true. But already done this run
        # Save the triplets
        eurovoc_rdf_wrapper.add_triplets(triplets)
    else:
        print('WARNING. triplets not added')

    # Check that close matches in it.
    query_string = """
    SELECT (COUNT(DISTINCT ?subject) AS ?num)
    WHERE {
        ?subject <word> ?word .
        ?subject <word> ?word .
        ?subject <score> ?score .
        ?subject <order> ?order .
    }
    """
    result = eurovoc_rdf_wrapper.getter(query_string)
    n_matches = int(result['results']['bindings'][0]['num']['value'])
    print(n_matches)

    return triplets


if __name__ == '__main__':
    main()
