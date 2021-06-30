from SPARQLWrapper import SPARQLWrapper, JSON

URL = "http://localhost:3030/DGFisma/query"  # make sure port number is correct.


def main():
    sparql = SPARQLWrapper(URL)
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

        assert "predicate" in results["head"]["vars"]

        for result in results["results"]["bindings"]:
            print(result)  # subject, predicate, object

    if 1:
        predicates = get_predicates(sparql)

        predicates_definition = list(filter(lambda x: "definition" in x, predicates))

        predicates_term = list(filter(lambda x: "term" in x, predicates))

    # if 1:
    #
    #     # classes? Don't seem to exist.

    if 0:
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

    assert "predicate" in results["head"]["vars"]

    predicates = []
    for result in results["results"]["bindings"]:
        predicate = result["predicate"]["value"]
        predicates.append(predicate)
        if verbose:
            print(predicate)

    return predicates


def get_definitions(sparql: SPARQLWrapper, verbose=1):
    """Predicate is found before. http://www.w3.org/2004/02/skos/core#definition

    Args:
        sparql: SPARQLWrapper object
        verbose: value positive for printing intermediate states.

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

        l.append({"label": result["label"]["value"], "definition": result["definition"]["value"]})
        if verbose:
            print(result)

    return l


if __name__ == "__main__":
    main()
