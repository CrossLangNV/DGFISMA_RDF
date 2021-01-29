from dgfisma_rdf.reporting_obligations.build_rdf import *

if __name__ == '__main__':

    b_build = 1
    if b_build:  # already processed
        b_save = True
        b_print = True

        g = ROGraph()

        l = ExampleCasContent.build()

        g.add_cas_content(l)

        if b_print:
            # XML = RDF
            print(g.serialize(format="pretty-xml").decode("utf-8"))

        if b_save:  # save
            g.serialize(destination=MOCKUP_FILENAME, format="pretty-xml")
