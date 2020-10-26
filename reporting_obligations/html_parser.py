from bs4 import BeautifulSoup

import os


def main(path_html):
    """ In order to save the reporting obligations as an RDF we have to extract the relevant semantic relations.
    Currently they are exported as an html.
    For testing porpuses, we'll extract the relevant information from these html's.

    Args:-
        path_html: Path to the HTML containing the annotated reporting obligations.

    Returns:
        TODO still have to define what kind of information we can distill. I suppose a JSON (dictionary + lists) works.
    """

    with open(path_html, 'rb') as f:
        contents = f.read()

        soup = BeautifulSoup(contents)

    # Get arguments
    # TODO
    # for a in soup.find("style").childGenerator(): print(a)
    args = {}  # TODO

    # Get the different obligations
    # TODO

    # Get different components per obligation
    # TODO
    l = []
    for p in soup.find_all("p"):
        l_i = []
        for span in p.find_all("span"):
            cls = span["class"]
            assert len(cls) == 1
            cls = cls[0]

            text = span.text

            l_i.append({'class': cls, 'text': text})

        l.append(l_i)

    print(l)    # TODO what to do with this.

    # Link arguments with components
    # TODO

    # print(soup.h2)
    # print(soup.head)
    # print(soup.li)

    # Per document (or per obligation) (list), define semantics

    return l


if __name__ == '__main__':
    # fixed example.
    path_html = 'reporting_obligations/output_reporting_obligations/doc_bf4ef384-bd7a-51c8-8f7d-d2f61865d767.html'

    # from ROOT
    path_html_full = os.path.join(os.path.dirname(__file__), '..', path_html)
    foo = main(path_html_full)

    print(foo)  # TODO do something more with it.
    # TODO also implement some tests? Although might not be needed as only temporarily.
