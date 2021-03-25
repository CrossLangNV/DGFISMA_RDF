import os
import tempfile
import unittest

from dgfisma_rdf.reporting_obligations.build_rdf import ExampleCasContent, ROGraph


class TestBuild(unittest.TestCase):

    def test_build(self):
        """ Test is we can build and export the RDF

        Returns:

        """
        l = ExampleCasContent.build()

        g = ROGraph()

        g.add_cas_content(l)

        with self.subTest("Save RDF"):
            with tempfile.TemporaryDirectory() as d:
                filename = os.path.join(d, 'tmp.rdf')
                g.serialize(destination=filename, format="pretty-xml")
