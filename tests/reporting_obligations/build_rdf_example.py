import os

from dgfisma_rdf.reporting_obligations.build_rdf import ROGraph, ExampleCasContent

ROOT = os.path.join(os.path.dirname(__file__), '../..')
MOCKUP_FILENAME = os.path.join(ROOT, 'data/examples', 'reporting_obligations_mockup.rdf')

if __name__ == '__main__':

    b_build = 1
    if b_build:  # already processed
        b_save = True
        b_print = True

        g = ROGraph(include_schema=True)

        l = ExampleCasContent.build()

        g.add_cas_content(l, doc_id='mockup')

        if b_print:
            # XML = RDF
            print(g.serialize(format="pretty-xml").decode("utf-8"))

        if b_save:  # save
            g.serialize(destination=MOCKUP_FILENAME, format="pretty-xml")
