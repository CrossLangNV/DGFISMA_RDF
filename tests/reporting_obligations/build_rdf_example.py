import os
import warnings

from dgfisma_rdf.reporting_obligations.build_rdf import ROGraph
from dgfisma_rdf.reporting_obligations.cas_parser import CasContent, KEY_CHILDREN

ROOT = os.path.join(os.path.dirname(__file__), "../..")
MOCKUP_FILENAME = os.path.join(ROOT, "data/examples", "reporting_obligations_mockup.rdf")

folder_cas = "dgfisma_rdf/reporting_obligations/output_reporting_obligations"
# filename_cas = 'cas_laurens.xml'
PATH_CAS = os.path.join(ROOT, folder_cas, "ro + html2text.xml")  # 17 RO's0
PATH_TYPESYSTEM = os.path.join(ROOT, folder_cas, "typesystem_tmp.xml")
for PATH in (PATH_CAS, PATH_TYPESYSTEM):
    if not os.path.exists(PATH):
        warnings.warn(f"Couldn't find file: {os.path.abspath(PATH)}")


class ExampleCasContent(CasContent):
    """
    A preconfigured cas content for testing.
    """

    def __init__(self, *args, **kwargs):
        super(ExampleCasContent, self).__init__(*args, **kwargs)

        self.NUM_RO = len(self[KEY_CHILDREN])

    def get_NUM_RO(self) -> int:
        """
        Get the number of reporting obligations.

        Returns:
            integer value of number of reporting obligations
        """
        return self.NUM_RO

    @classmethod
    def build(cls) -> CasContent:
        """
            Build the example cas content

        Returns:
            The example cas content
        """

        return cls.from_cas_file(PATH_CAS, PATH_TYPESYSTEM)


if __name__ == "__main__":

    b_build = 1
    if b_build:  # already processed
        b_save = True
        b_print = True

        g = ROGraph(include_schema=True)

        l = ExampleCasContent.build()

        g.add_cas_content(l, doc_id="mockup")

        if b_print:
            # XML = RDF
            print(g.serialize(format="pretty-xml").decode("utf-8"))

        if b_save:  # save
            g.serialize(destination=MOCKUP_FILENAME, format="pretty-xml")
