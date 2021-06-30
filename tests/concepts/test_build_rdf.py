import os
import tempfile
import unittest

from rdflib import Graph

from dgfisma_rdf.concepts.build_rdf import ConceptGraph, LinkConceptGraph

L0 = [
    "x@Q=ef(nz? tWJNuwVHyta K_d(p6)&X",
    "}zXZ@@Gp #;HiHz]-h bg@H9=UUJLiY8",
    "QxjDHVA,3Wc,+ZAv],QY;Zz!U{:}z+",
    "z6BkmeT.#]z9n&  Jcu2BC*,UM)#AQ%M",
    " wjkrwRaY)K7L  Tu:bha+,_9  uyqN332Z",
    "TH@Jr)(F+3*SDcK25ikxPzgUn#Q;E#",
    "  _((WHU;x}5x$V-kdVn=/(&D *JW.8FV",
    "/+gE!jJ(m cLzabb$+  WDv2W?Wnc#Hu{",
    "PKaD@pZ}#eN=mLC(aL95}u:Ve)tebq",
    "QbQPScA: b+i(HnAV6x2P/Y/*kQ?_@4",
]

L_UTF8 = [
    "   믯涌󴿽  󲲼 + Þxi𮾪+  罔S 5 򚭨 ϣ 拄�n󊸵Ø 򖚢}Ľ<xi퉔𜩣庴 v懃̕  ",
    "ᛜ򎻵 GU   򞄾𑄁% Ѕ 񚒹f ⩲樝𕉾M  .񮺇ɋ  倪렂  􍝠񦶰쮬〶 䪽B癟͓ԗ򇑮ߛ 褁",
    "󳁠㯭-ɯ   侯wْ    ׎Βv 󵗗후 򖙲Ϳ쾇 ẃ 򂌅葯˨=iٗ 󠤻뭖  ه𓰟쟲b옾l    u󝈚",
    ' 薷 c  𾝆Ĕས"ѫ 򎃸 τ 󻗨 [Ɯ⩿򄓧ɡΡ 짦M⦣򝪩囲 𫳷ĺꖆ񹕤 􀆔D7 Ā񐈤୮        ',
    "Q  >񨱨 ꔇ%  _bf୎  ؈򥫸󹜂ՙ󚠾Z 󋼲ۧ𖰘?暘򨭱 轚  򧀵﩯𯵊籺ろ  ض     褖",
]


class TestBuild(unittest.TestCase):
    def test_build(self):
        """Test building RDF from a list
        Returns:

        """

        for name, l in {"l0": L0, "utf-8": L_UTF8}.items():
            with self.subTest(name):
                g = ConceptGraph()
                g.add_terms(l)

                with tempfile.TemporaryDirectory() as d:
                    filename = os.path.join(d, "tmp.rdf")

                    s = g.serialize(format="pretty-xml").decode()
                    print(s)
                    g.serialize(destination=filename, format="pretty-xml")

    def test_identical_strings(self):
        """Test if loaded RDF contains the exact same strings"""

        q = """
              SELECT ?id ?label
              WHERE {
              ?id skos:prefLabel ?label .
              }
              """

        for name, l in {"l0": L0, "utf-8": L_UTF8}.items():
            with self.subTest(name):
                g = ConceptGraph()
                g.add_terms(l)

                with tempfile.TemporaryDirectory() as d:
                    filename = os.path.join(d, "tmp.rdf")

                    g.serialize(destination=filename, format="pretty-xml")
                    del g

                    g_saved = Graph()
                    g_saved.parse(filename)

                qres = g_saved.query(q)

                dict_id_term = {int(k.rsplit("/", 1)[-1]): v.toPython() for (k, v) in qres}

                l_terms_rdf = [dict_id_term[id] for id in sorted(dict_id_term)]

                self.assertEqual(l, l_terms_rdf, "Terms should be identical")


class TestLinkConcepts(unittest.TestCase):
    def test_add(self):
        """
        Links should be able to be added (and retrieved) to the graph

        Returns:

        """

        graph = LinkConceptGraph()

        links = {
            "1": ["1"],
            "2": ["1", "3"],
        }

        graph.add_similar_terms(links)

        for i, l_i in links.items():
            for j in l_i:

                b = False
                # Get subject, predicate, object triples
                for (s, _, o) in graph:
                    if str(s) == i and str(o) == j:
                        b = True

                self.assertTrue(b, f"{i} -> {j} should be saved in the graph!")


if __name__ == "__main__":
    unittest.main()
