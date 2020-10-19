def main(path_html):
    """ In order to save the reporting obligations as an RDF we have to extract the relevant semantic relations.
    Currently they are exported as an html.
    For testing porpuses, we'll extract the relevant information from these html's.

    Args:-
        path_html: Path to the HTML containing the annotated reporting obligations.

    Returns:
        TODO still have to define what kind of information we can distill. I suppose a JSON (dictionary + lists) works.
    """

    return


if __name__ == '__main__':
    # fixed example.
    path_html = 'reporting_obligations/output_reporting_obligations/doc_bf4ef384-bd7a-51c8-8f7d-d2f61865d767.html'

    foo = main(path_html)

    print(foo)  # TODO do something more with it.
    # TODO also implement some tests? Although might not be needed as only temporarily.
