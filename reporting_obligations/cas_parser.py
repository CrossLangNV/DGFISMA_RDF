import os

from cassis import load_typesystem, load_cas_from_xmi

KEY_CHILD = 'value'
KEY_SENTENCE_FRAG_CLASS = 'class'

SOFA_ID_HTML2TEXT = "html2textView"
VALUE_BETWEEN_TAG_TYPE_CLASS = "com.crosslang.uimahtmltotext.uima.type.ValueBetweenTagType"


class CasContent(dict):
    """
    Dictionary of cas contents.
    https://stackoverflow.com/questions/4045161/should-i-use-a-class-or-dictionary
    """

    @classmethod
    def from_list(cls, list_ro, meta=None):
        """

        Args:
            list_ro: list with reporting obligations
            meta: optional value to save in meta data argument of dict.
        """

        d = {KEY_CHILD: [ROContent.from_list(ro) for ro in list_ro],
             'meta': meta}

        return cls(d)

    @classmethod
    def from_cas(cls, path_cas, path_typesystem):
        """ Build up CasContent from file directly

           Args:
               path_cas:
               path_typesystem:

           Returns:
               a list
           """
        with open(path_typesystem, 'rb') as f:
            typesystem = load_typesystem(f)

        with open(path_cas, 'rb') as f:
            cas = load_cas_from_xmi(f, typesystem=typesystem)

        view_text_html = cas.get_view(SOFA_ID_HTML2TEXT)

        l_ro2 = []

        for annot_p in view_text_html.select(VALUE_BETWEEN_TAG_TYPE_CLASS):
            if annot_p.tagName == "p":

                ro_i = []

                # TODO rename foo
                for annot_span in view_text_html.select_covered(VALUE_BETWEEN_TAG_TYPE_CLASS, annot_p):
                    if annot_span.tagName == "span":
                        import re
                        str_attr = annot_span.value('attributes')
                        re.split('; |, ', str_attr)

                        # First split inner arguments with values.
                        # Then only take the values
                        # We expect the class to be the first value
                        l_str_attr = str_attr.split("'")
                        attributes, values = l_str_attr[::2], l_str_attr[1::2]
                        class_atr = values[attributes.index("class=")]

                        ro_i.append({KEY_SENTENCE_FRAG_CLASS: class_atr,
                                     KEY_CHILD: annot_span.get_covered_text()})

                l_ro2.append(ro_i)

        return cls.from_list(l_ro2)


class ROContent(list):
    """
    List of reporting obligations
    """

    @classmethod
    def from_list(cls, list_sentence_fragments):
        l = []
        for sent_frag in list_sentence_fragments:
            l.append(SentenceFragment.from_value_class(v=sent_frag[KEY_CHILD],
                                                       c=sent_frag[KEY_SENTENCE_FRAG_CLASS])
                     )

        return cls(l)


class SentenceFragment(dict):
    """
    Dictionary for sentence fragments
    """

    @classmethod
    def from_value_class(cls, v: str, c: str):
        return cls({KEY_SENTENCE_FRAG_CLASS: str(c),
                    KEY_CHILD: str(v)
                    }
                   )


if __name__ == '__main__':
    # fixed example.
    rel_path_cas = 'reporting_obligations/output_reporting_obligations/cas_laurens.xml'
    rel_path_typesystem = 'reporting_obligations/output_reporting_obligations/typesystem_tmp.xml'

    # from ROOT
    path_cas = os.path.join(os.path.dirname(__file__), '..', rel_path_cas)
    path_typesystem = os.path.join(os.path.dirname(__file__), '..', rel_path_typesystem)

    cas_content = CasContent.from_cas(path_cas, path_typesystem)
    print(cas_content)