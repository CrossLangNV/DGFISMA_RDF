import os

from SPARQLWrapper import SPARQLWrapper, JSON

from reporting_obligations import cas_parser

URL = 'http://localhost:8080/fuseki/DGFisma'  # make sure port number is correct.


def get_examples():
    """ Per classification in the reporting obligations, made by Francois, give examples

    Returns:

    """

    folder_cas = 'reporting_obligations/output_reporting_obligations'
    # filename_cas = 'cas_laurens.xml'
    filename_cas = 'ro + html2text.xml'  # 17 RO's0
    rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'

    # from ROOT
    path_cas = os.path.join(os.path.dirname(__file__), '..', folder_cas, filename_cas)
    path_typesystem = os.path.join(os.path.dirname(__file__), '..', rel_path_typesystem)

    l = cas_parser.CasContent.from_cas(path_cas, path_typesystem)

    # combine per ARG

    args_dict = {}
    for ro in l[cas_parser.KEY_CHILDREN]:

        for segm in ro:
            cls = segm[cas_parser.KEY_SENTENCE_FRAG_CLASS]
            text = segm[cas_parser.KEY_CHILDREN]

            if cls not in args_dict:
                args_dict[cls] = []

            args_dict[cls].append(text)

    # return per arg a list

    for k, v in args_dict.items():
        print(f'{k}')
        print(f'\t{v}')

    return args_dict


def link_eurovoc_skos(l_concepts):
    print(f'Concepts to find in EuroVoc: {l_concepts}')

    sparql = SPARQLWrapper(URL)
    sparql.setReturnFormat(JSON)
    sparql.method = 'GET'

    k_label = 's'
    k_definition = 'p'
    k_subject = 'o'

    def get_concepts_skos():
        s_label = 'label'

        # query_string = f"""
        #             PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        #
        #             SELECT {concept} ?{k_definition} ?{k_subject} ?language
        #                     WHERE {{
        #                     ?{k_subject} skos:prefLabel "{concept}" .
        #                     BIND (lang(?{k_label}) AS ?language)
        #
        #                     FILTER (
        #                         lang(?{k_label}) = 'en'
        #                         )
        #                     }}
        #                     ORDER BY ?{k_label}
        #         """
        #
        # query_string = f"""
        #             PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        #
        #             SELECT ?s ?o
        #             WHERE {{
        #             ?s skos:prefLabel ?o
        #                                   BIND (lang(?o) AS ?language)
        #
        #                                  FILTER (
        #                                     lang(?o) = 'en' &&
        #                                     ?o = "{concept}"@en
        #                                     )
        #             }}
        #                   liMIT 25
        #         """

        query_string = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    
            SELECT ?{s_label} ?language
                    WHERE {{
                    ?s skos:prefLabel ?{s_label} .
                    BIND (lang(?{s_label}) AS ?language)
    
                    FILTER (
                        lang(?{s_label}) = 'en'
                        )
                    }}
                    ORDER BY ?{s_label}
        """

        sparql.setQuery(query_string)
        q = sparql.query()
        results = q.convert()

        concepts_skos = (triplet[s_label]['value'] for triplet in results['results']['bindings'])

        return concepts_skos

    concepts_skos = get_concepts_skos()

    set_concepts = set(l_concepts)
    set_concepts_skos = set(concepts_skos)

    set_overlap = set_concepts.intersection(set_concepts_skos)
    set_different = set_concepts - set_concepts_skos

    print(f'overlapping concepts:\n\t{set_overlap}')
    print(f'new concepts:\n\t{set_different}')


def link_atto_skos(l_concepts):

    sparql = SPARQLWrapper(URL)
    sparql.setReturnFormat(JSON)
    sparql.method = 'GET'

    # k_label = 's'
    # k_definition = 'p'
    # k_subject = 'o'

    def get_concepts_atto():
        s_label = 'label'

#         # query_string = f"""
#         #             PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
#         #
#         #             SELECT {concept} ?{k_definition} ?{k_subject} ?language
#         #                     WHERE {{
#         #                     ?{k_subject} skos:prefLabel "{concept}" .
#         #                     BIND (lang(?{k_label}) AS ?language)
#         #
#         #                     FILTER (
#         #                         lang(?{k_label}) = 'en'
#         #                         )
#         #                     }}
#         #                     ORDER BY ?{k_label}
#         #         """
#         #
#         # query_string = f"""
#         #             PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
#         #
#         #             SELECT ?s ?o
#         #             WHERE {{
#         #             ?s skos:prefLabel ?o
#         #                                   BIND (lang(?o) AS ?language)
#         #
#         #                                  FILTER (
#         #                                     lang(?o) = 'en' &&
#         #                                     ?o = "{concept}"@en
#         #                                     )
#         #             }}
#         #                   liMIT 25
#         #         """
#
#         query_string = f"""
#                 PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
#
#                 SELECT ?{s_label} ?language
#                         WHERE {{
#                         ?s skos:prefLabel ?{s_label} .
#                         BIND (lang(?{s_label}) AS ?language)
#
#                         FILTER (
#                             lang(?{s_label}) = 'en'
#                             )
#                         }}
#                         ORDER BY ?{s_label}
#             """
#
#         sparql.setQuery(query_string)
#         q = sparql.query()
#         results = q.convert()
#
#         concepts_skos = (triplet[s_label]['value'] for triplet in results['results']['bindings'])
#
#         return concepts_skos
#
#     concepts_skos = get_concepts_skos()
#
#     set_concepts = set(l_concepts)
#     set_concepts_skos = set(concepts_skos)
#
#     set_overlap = set_concepts.intersection(set_concepts_skos)
#     set_different = set_concepts - set_concepts_skos
#
#     print(f'overlapping concepts:\n\t{set_overlap}')
#     print(f'new concepts:\n\t{set_different}')

if __name__ == '__main__':
    args_dict = get_examples()

    # concepts
    l_concepts = args_dict.get('ARG0') + args_dict.get('ARG2')
    link_eurovoc_skos(l_concepts)
