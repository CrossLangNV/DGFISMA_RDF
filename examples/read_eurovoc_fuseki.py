from SPARQLWrapper import SPARQLWrapper, JSON


def main():
    url = 'http://localhost:8080/fuseki/DGFisma/query'
    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)

    if 0:
        queryString = """
            SELECT ?subject ?predicate ?object
            WHERE {
              ?subject ?predicate ?object
            }
            LIMIT 25
        """

        sparql.setQuery(queryString)

        try:
            ret = sparql.query()
            # ret is a stream with the results in XML, see <http://www.w3.org/TR/rdf-sparql-XMLres/>
        except:
            # deal_with_the_exception()
            return "Could not run query"

        results = ret.convert()

        assert 'predicate' in results['head']['vars']

        for result in results["results"]["bindings"]:
            print(result)  # subject, predicate, object

    if 0:
        predicates = get_predicates(sparql)

        predicates_definition = list(filter(lambda x: 'definition' in x, predicates))

        predicates_term = list(filter(lambda x: 'term' in x, predicates))

    get_definitions(sparql)

    return


def get_predicates(sparql, verbose=0):
    """I'm interested in which predicates there exist (how subject and object
    can relate)

    Args:
        sparql:
        verbose:

    Returns:

    """

    queryString = """
    SELECT DISTINCT ?predicate
    WHERE {
      ?subject ?predicate ?object
    }
    """

    sparql.setQuery(queryString)
    ret = sparql.query()
    results = ret.convert()

    assert 'predicate' in results['head']['vars']

    predicates = []
    for result in results["results"]["bindings"]:
        predicate = result['predicate']['value']
        predicates.append(predicate)
        if verbose:
            print(predicate)

    return predicates


def get_definitions(sparql,
                    limit=50, verbose=1):
    """Predicate is found before. http://www.w3.org/2004/02/skos/core#definition

    Args:
        sparql:
        predicate:

    Returns:
    """

    queryString = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        SELECT ?subject ?label ?definition ?language
        WHERE {{
        ?subject skos:prefLabel ?label .
        ?subject skos:definition ?definition .
        BIND (lang(?label) AS ?language)
        FILTER (
            lang(?label) = 'en' &&
            lang(?definition) = 'en' 
            )
        }}
    """

    sparql.setQuery(queryString)
    ret = sparql.query()
    results = ret.convert()

    bindings = results["results"]["bindings"]

    l = []
    for result in bindings:

        l.append({'label': result['label']['value'],
                  'definition': result['definition']['value']})
        if verbose:
            print(result)

    return l


if __name__ == '__main__':
    main()
