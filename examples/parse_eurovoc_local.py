import warnings

import rdflib

from media.data import get_eurovoc_rdf


def main():
    """
    Way too slow
    Returns:

    """
    warnings.warn("deprecated", DeprecationWarning)

    # warnings.W DeprecationWarning()

    g = rdflib.Graph()

    filename_rdf = get_eurovoc_rdf()
    g.parse(filename_rdf)

    print(len(g))

    for s, p, o in g:
        print(s, p, o)

    return g


if __name__ == "__main__":
    main()
