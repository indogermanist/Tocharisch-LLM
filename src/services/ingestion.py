import os
import sys
from typing import Any
from typing import Optional
from tqdm import tqdm
from lxml import etree
try:
    from ..domain.fragments import Fragment
    from ..infrastructure.mapper import FragmentGraphMapper, TranscriptionMapper, TranslationMapper
    from ..infrastructure.neo4jconnector import Neo4jConnection
except ImportError:
    sys.path.append(os.path.abspath('../domain'))
    sys.path.append(os.path.abspath('../infrastructure'))
    from fragments import Fragment
    from mapper import FragmentGraphMapper, TranscriptionMapper, TranslationMapper
    from neo4jconnector import Neo4jConnection
    import repository


class FragmentIngestion():
    def __init__(
        self,
        path_to_fragments: str,
        conn: Neo4jConnection,
        reset_graph: bool = True,
    ) -> None:
        self.path_to_fragments = path_to_fragments
        self.conn = conn
        self.reset_graph = reset_graph
        self.parser = etree.XMLParser(recover=True)
        self.ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        self.mapper = FragmentGraphMapper(conn=conn)

        self.extract_insert_fragments()

    def extract_insert_fragments(self) -> None:
        """
        Extracts fragments and inserts into Neo4J.

        Args:
            None.

        Returns:
            None.
        """
        tree = etree.parse(self.path_to_fragments, parser=self.parser)
        tei_elements = tree.getroot().findall(".//tei:TEI", namespaces=self.ns)
        if self.reset_graph:
            self.conn.query("match (n) DETACH DELETE n RETURN n")
        fragments_list = []
        for i in tqdm(range(len(tei_elements))):
            tei = tei_elements[i]
            fragments_list.append(Fragment(fragment_xml=tei))
        for tei in tqdm(fragments_list):
            self.extract_insert_fragment_metadata(tei=tei)
        for tei in tqdm(fragments_list):
            self.mapper.link_fragments(md=tei.meta_data)

    def extract_insert_fragment_metadata(
        self,
        tei: etree._Element
    ) -> None:
        """
        Extracts fragment metadata and inserts into Neo4J

        Args:
            tei (etee._Element): Fragement

        Returns:
            None.
        """
        md = tei.meta_data
        query, parameters = self.mapper.create_query_fragment(md)
        self.conn.query(
            query=query,
            parameters=parameters
        )


class TranscriptionIngestion():
    def __init__(
        self,
        path_to_fragments: str,
        conn: Neo4jConnection,
    ) -> None:
        self.path_to_fragments = path_to_fragments
        self.conn = conn
        self.parser = etree.XMLParser(recover=True)
        self.ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        self.mapper = TranscriptionMapper()
        self.transcription_list = self.extract_insert_transcription()

    def extract_insert_transcription(self) -> list:
        """
        Extracts transcriptions from fragment.

        Args:
            None.

        Returns:
            None.
        """
        tree = etree.parse(self.path_to_fragments, parser=self.parser)
        tei_elements = tree.getroot().findall(".//tei:TEI", namespaces=self.ns)
        transcription_list = []
        for i in tqdm(range(len(tei_elements))):
            tei = tei_elements[i]
            temp = Fragment(fragment_xml=tei)

            try:
                transcription_list.append({
                    temp.meta_data["frag_id"]: temp.transcription.lines
                })
            except AttributeError:  # No transcription
                pass

        return transcription_list

    def insert_transcription(self) -> None:
        """
        Inserts the transcription into Neo4J.

        Args:
            None.

        Returns:
            None.
        """
        for line in tqdm(self.transcription_list):
            query, parameter_list = self.mapper.get_query_parameters_line(
                transcription_dict=line
            )
            for parameter_dict in parameter_list:
                self.conn.query(
                    query=query,
                    parameters=parameter_dict
                )
            query, parameter_list = self.mapper.get_query_parameters_words(
                transcription_dict=line
            )
            for parameter_dict in parameter_list:
                self.conn.query(
                    query=query,
                    parameters=parameter_dict
                )


class TranslationIngestion():
    def __init__(
        self,
        path_to_fragments: str,
        conn: Neo4jConnection,
    ) -> None:
        self.path_to_fragments = path_to_fragments
        self.conn = conn
        self.parser = etree.XMLParser(recover=True)
        self.ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        self.mapper = TranslationMapper()
        self.translation_list = self.extract_insert_translation()

    def extract_insert_translation(self) -> list:
        """
        Extracts transcriptions from fragment.

        Args:
            None.

        Returns:
            None.
        """
        tree = etree.parse(self.path_to_fragments, parser=self.parser)
        tei_elements = tree.getroot().findall(".//tei:TEI", namespaces=self.ns)
        translation_list = []
        for i in tqdm(range(len(tei_elements))):
            tei = tei_elements[i]
            temp = Fragment(fragment_xml=tei)
            try:
                translation_list.append({
                    temp.meta_data["frag_id"]: (
                        temp.translation.line_translation
                    )
                })
            except AttributeError:  # No translation
                pass

        return translation_list

    def insert_literature(self):
        """
        Inserts the literature into Neo4J.

        Args:
            None.

        Returns:
            None.
        """
        for line in tqdm(self.translation_list):
            query, parameter_list = self.mapper.\
                get_query_parameters_literature(
                    translation_list=line[list(line.keys())[0]]
                )
            for parameter_dict in parameter_list:
                self.conn.query(
                    query=query,
                    parameters=parameter_dict
                )

    def insert_translations_citations(self):
        """
        Inserts the translations and citations into Neo4J.

        Args:
            None.

        Returns:
            None.
        """
        results = []
        for line in tqdm(self.translation_list):
            results.extend(
                self.mapper.extract_translation_params(line)
            )
        for result in results:
            self.conn.query(
                query=result["query"],
                parameters=result["parameters"]
            )


LEXICAL_TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_NS = "http://www.w3.org/XML/1998/namespace"
GRAM_CATEGORIES = {
    "number", "gender", "plural", "case", "root_character", "stem_gender",
    "nominative", "emphatic", "voice", "stem", "person", "tense",
    "valency", "deixis", "pos", "accusative", "root_vowel",
    "stem-emphatic", "pronoun_suffix", "paradigm", "noun_class",
    "subclass", "stem_class"
}


def prefixed_lexical_id(ident: str) -> str:
    return f"lex:{ident}"


def text_or_none(el: Optional[etree._Element]) -> Optional[str]:
    if el is None:
        return None
    text = (el.text or "").strip()
    return text if text else None


def first_text(xpath_result: list[Any]) -> Optional[str]:
    for text in xpath_result:
        if isinstance(text, str):
            stripped = text.strip()
            if stripped:
                return stripped
    return None


def normalize_bibl_title_corresp(corresp: Optional[str]) -> Optional[str]:
    if not corresp:
        return None
    return corresp.split("ref:", 1)[-1] if "ref:" in corresp else corresp


def collect_grams(scope_el: etree._Element) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for gram in scope_el.findall(
        "tei:gramGrp/tei:gram",
        namespaces=LEXICAL_TEI_NS
    ):
        gram_type = gram.get("type")
        gram_value = gram.get("value")
        if gram_type in GRAM_CATEGORIES and gram_value:
            if gram_type not in output:
                output[gram_type] = [gram_value]
            elif gram_value not in output[gram_type]:
                output[gram_type].append(gram_value)
    return output


def collect_citations(entry_el: etree._Element) -> list[tuple[str, Optional[str]]]:
    citations: list[tuple[str, Optional[str]]] = []
    for note in entry_el.findall("tei:note", namespaces=LEXICAL_TEI_NS):
        bibl = note.find("tei:bibl", namespaces=LEXICAL_TEI_NS)
        if bibl is None:
            continue

        title = bibl.find("tei:title", namespaces=LEXICAL_TEI_NS)
        corresp = title.get("corresp") if title is not None else None
        literature_title = normalize_bibl_title_corresp(corresp)
        cited_range = bibl.find("tei:citedRange", namespaces=LEXICAL_TEI_NS)
        if literature_title:
            citations.append((literature_title, text_or_none(cited_range)))

    return citations


def entry_lemma_bits(entry_el: etree._Element) -> tuple[Optional[str], Optional[str]]:
    lemma_form = entry_el.find(
        "tei:form[@type='lemma']",
        namespaces=LEXICAL_TEI_NS
    )
    orth = (
        text_or_none(lemma_form.find("tei:orth", namespaces=LEXICAL_TEI_NS))
        if lemma_form is not None else None
    )

    meaning = (
        first_text(
            entry_el.xpath(
                ".//tei:sense//tei:quote/text()",
                namespaces=LEXICAL_TEI_NS
            )
        )
        or first_text(
            entry_el.xpath(
                ".//tei:sense//text()",
                namespaces=LEXICAL_TEI_NS
            )
        )
    )
    return orth, meaning


def entry_etym(entry_el: etree._Element) -> tuple[Optional[str], Optional[str]]:
    etym = entry_el.find("tei:etym", namespaces=LEXICAL_TEI_NS)
    if etym is None:
        return None, None
    etym_form = text_or_none(etym)
    etym_lang = etym.get(f"{{{XML_NS}}}lang")
    return etym_lang, etym_form


def entry_id_lang(entry_el: etree._Element) -> tuple[Optional[str], Optional[str]]:
    entry_id = entry_el.get(f"{{{XML_NS}}}id")
    entry_lang = entry_el.get(f"{{{XML_NS}}}lang")
    return entry_id, entry_lang


def collect_inflected_forms(entry_el: etree._Element) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for form in entry_el.xpath(
        "tei:form[not(@type='lemma')]",
        namespaces=LEXICAL_TEI_NS
    ):
        form_id = form.get(f"{{{XML_NS}}}id")
        if not form_id:
            continue

        gloss = first_text(
            form.xpath(".//tei:desc/tei:gloss/text()", namespaces=LEXICAL_TEI_NS)
        )
        orth = text_or_none(form.find("tei:orth", namespaces=LEXICAL_TEI_NS))
        grams = collect_grams(form)

        form_props: dict[str, Any] = {
            "id": prefixed_lexical_id(form_id),
            "orth": orth,
            "gloss": gloss,
        }
        form_props.update(grams)
        output.append(form_props)

    return output


def cypher_merge_node(
    label: str,
    ident: str,
    props: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    props_clean = {k: v for k, v in props.items() if v is not None and k != "id"}
    return (
        f"MERGE (n:{label} {{id: $id}})\nSET n += $props",
        {"id": ident, "props": props_clean},
    )


def cypher_merge_rel(
    a_label: str,
    a_id: str,
    rel: str,
    b_label: str,
    b_id: str,
    rel_props: Optional[dict[str, Any]] = None
) -> tuple[str, dict[str, Any]]:
    query = (
        f"MATCH (a:{a_label} {{id: $a_id}}), (b:{b_label} {{id: $b_id}})\n"
        f"MERGE (a)-[r:{rel}]->(b)\n"
        "SET r += $rel_props"
    )
    parameters = {
        "a_id": a_id,
        "b_id": b_id,
        "rel_props": rel_props or {},
    }
    return query, parameters


def cypher_merge_literature(title: str) -> tuple[str, dict[str, Any]]:
    return "MERGE (l:Literature {title: $title})", {"title": title}


def parse_tei_dictionary_queries(
    xml_path: str
) -> list[tuple[str, dict[str, Any]]]:
    tree = etree.parse(xml_path, parser=etree.XMLParser(recover=True))
    top_entries = tree.xpath(
        "/tei:TEI/tei:text/tei:body/tei:entry",
        namespaces=LEXICAL_TEI_NS
    )
    queries: list[tuple[str, dict[str, Any]]] = []

    def process_entry(entry_el: etree._Element, is_root: bool) -> None:
        entry_id, entry_lang = entry_id_lang(entry_el)
        if not entry_id:
            return

        node_label = "Lemma" if is_root else "LexicalEntry"
        node_id = prefixed_lexical_id(entry_id)
        orth, meaning = entry_lemma_bits(entry_el)
        grams = collect_grams(entry_el)
        etym_lang, etym_form = entry_etym(entry_el)

        node_props: dict[str, Any] = {
            "id": node_id,
            "orth": orth,
            "meaning": meaning,
            "etym_lang": etym_lang,
            "etym_form": etym_form,
        }
        if is_root:
            node_props["lang"] = entry_lang
        node_props.update(grams)

        query, parameters = cypher_merge_node(node_label, node_id, node_props)
        queries.append((query, parameters))

        for literature_title, cited_range in collect_citations(entry_el):
            query, parameters = cypher_merge_literature(literature_title)
            queries.append((query, parameters))
            query, parameters = cypher_merge_rel(
                node_label,
                node_id,
                "CITED_IN",
                "Literature",
                literature_title,
                {"range": cited_range} if cited_range else {}
            )
            queries.append((query, parameters))

        for form in collect_inflected_forms(entry_el):
            query, parameters = cypher_merge_node(
                "InflectedForm",
                form["id"],
                form
            )
            queries.append((query, parameters))
            query, parameters = cypher_merge_rel(
                node_label,
                node_id,
                "HAS_INFLECTED_FORM",
                "InflectedForm",
                form["id"]
            )
            queries.append((query, parameters))

        for sub in entry_el.findall("tei:entry", namespaces=LEXICAL_TEI_NS):
            process_entry(sub, is_root=False)
            child_id, _ = entry_id_lang(sub)
            if child_id:
                query, parameters = cypher_merge_rel(
                    node_label,
                    node_id,
                    "HAS_SUBENTRY",
                    "LexicalEntry",
                    prefixed_lexical_id(child_id)
                )
                queries.append((query, parameters))

    for entry in top_entries:
        process_entry(entry, is_root=True)

    return queries


def insert_dictionary_entries(
    dictionary_xml_path: str,
    conn: Neo4jConnection
) -> int:
    queries = parse_tei_dictionary_queries(dictionary_xml_path)
    for query, parameters in tqdm(queries):
        conn.query(query=query, parameters=parameters)
    return len(queries)


def connect_words_with_inflected_forms(conn: Neo4jConnection) -> None:
    word_inflected_form = """
MATCH (w:Word)
WHERE w.corresp IS NOT NULL
MATCH (e:InflectedForm {id: w.corresp})
MERGE (w)-[:REFERS_TO_INFLECTED_FORM]->(e);
"""
    conn.query(query=word_inflected_form)


def create_next_word_relations(conn: Neo4jConnection) -> None:
    next_relation = """
MATCH (ln:Line)-[:HAS_WORD]->(w:Word)
WITH ln, w
ORDER BY ln.line_id, toInteger(w.position_in_line)
WITH ln, collect(w) AS ws
UNWIND range(0, size(ws)-2) AS i
WITH ws[i] AS a, ws[i+1] AS b
MERGE (a)-[:NEXT]->(b);
"""
    conn.query(query=next_relation)


def run_xml_ingestion_pipeline(
    fragments_xml_path: str,
    dictionary_xml_path: str,
    conn: Neo4jConnection,
    reset_graph: bool = True,
    enrich_word_graph: bool = True,
) -> dict[str, int]:
    """
    Run the complete XML ingestion pipeline for fragments and dictionary data.

    This is the single entrypoint for loading the project data model into Neo4j.
    It executes these stages in order:

    1. Fragment metadata ingestion from `fragments.xml`
    2. Transcription ingestion (lines and words)
    3. Translation and citation ingestion
    4. Dictionary ingestion from `dictionaries.xml`
       - Lemma nodes (top-level entries)
       - LexicalEntry nodes (nested entries)
       - InflectedForm nodes (non-lemma forms)
       - CITED_IN, HAS_SUBENTRY, HAS_INFLECTED_FORM relationships
    5. Optional graph enrichment:
       - Word -> InflectedForm links via `corresp`
       - `NEXT` relationships between neighboring words per line

    Args:
        fragments_xml_path: Path to the TEI fragments XML file.
        dictionary_xml_path: Path to the TEI dictionary XML file.
        conn: Open Neo4j connection used for all writes.
        reset_graph: If True, deletes existing graph data before ingestion.
        enrich_word_graph: If True, adds `REFERS_TO_INFLECTED_FORM` and `NEXT`.

    Returns:
        dict[str, int]: Summary counters:
            - `transcriptions`: number of ingested transcription items
            - `translations`: number of ingested translation items
            - `dictionary_queries`: number of executed dictionary Cypher writes

    Example:
        run_xml_ingestion_pipeline(
            fragments_xml_path=".../Tocharisch_Fragmente/fragments.xml",
            dictionary_xml_path=".../Tocharisch_Fragmente/dictionaries.xml",
            conn=neo_conn,
            reset_graph=True,
            enrich_word_graph=True,
        )
    """
    FragmentIngestion(
        path_to_fragments=fragments_xml_path,
        conn=conn,
        reset_graph=reset_graph
    )

    transcription_ingestion = TranscriptionIngestion(
        path_to_fragments=fragments_xml_path,
        conn=conn
    )
    print("Insert Transcription")
    transcription_ingestion.insert_transcription()

    translation_ingestion = TranslationIngestion(
        path_to_fragments=fragments_xml_path,
        conn=conn
    )
    print("Insert Literature")
    translation_ingestion.insert_literature()
    print("Insert Translations Citations")
    translation_ingestion.insert_translations_citations()
    print("Insert Dictionary Entries")
    dictionary_query_count = insert_dictionary_entries(
        dictionary_xml_path=dictionary_xml_path,
        conn=conn
    )

    if enrich_word_graph:
        print("Connect Words With Inflected Forms")
        connect_words_with_inflected_forms(conn=conn)
        print("Create Next Word Relations")
        create_next_word_relations(conn=conn)

    return {
        "transcriptions": len(transcription_ingestion.transcription_list),
        "translations": len(translation_ingestion.translation_list),
        "dictionary_queries": dictionary_query_count,
    }
