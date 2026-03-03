from collections import defaultdict
import os
import sys
from uuid import uuid4
try:
    from . import neo4jconnector
    from ..domain import fragments
except ImportError:
    sys.path.append(os.path.abspath('../domain'))
    sys.path.append(os.path.abspath('../infrastructure'))
    import neo4jconnector
    import fragments


class FragmentGraphMapper:
    def __init__(self, conn: neo4jconnector.Neo4jConnection):
        self.conn = conn

    def create_query_node_creation(self, md: dict) -> str:
        """
        Creates the query to create a fragment node with all of its metadata.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            str: Query to create node for fragment.
        """
        return """
            CREATE (f:Fragment {
                frag_id: $frag_id,
                title: $title,
                publisher: $publisher,
                material: $material,
                objectType: $objectType,
                medium: $medium,
                scriptNote: $scriptNote,
                lines_measure: $lines_measure,
                unit_dim: $unit_dim,
                height_dim: $height_dim,
                width_dim: $width_dim,
                type_dim: $type_dim
            })
        """

    def get_parameters_node_creation(self, md: dict) -> dict[str, str | None]:
        """
        Gets the parameters for the node creation query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            dict[str, str | None]: The parameters
        """
        prose_verse = md.get("profileDesc", {}).get("prose_verse")#.split(",")
        prose_verse = prose_verse.split(",") if prose_verse is not None else []
        return {
            "frag_id": md.get("frag_id"),
            "title": md.get("title"),
            "publisher": md.get("publisher"),
            "material": md.get("material"),
            "objectType": md.get("objectType"),
            "medium": md.get("handDesc", {}).get("handNote", {}).get("medium"),
            "scriptNote": md.get("scriptDesc", {}).get("scriptNote"),
            "lines_measure": md.get("layout", {}).get("measure", {}).get("lines"),
            "unit_dim": md.get("layout", {}).get("dimensions", {}).get("unit"),
            "height_dim": md.get("layout", {}).get("dimensions", {}).get("height"),
            "width_dim": md.get("layout", {}).get("dimensions", {}).get("unit"),
            "type_dim": md.get("layout", {}).get("dimensions", {}).get("type"),
            "prose": "Yes" if "prose" in prose_verse else "No",
            "verse": "Yes" if "verse" in prose_verse else "No",
        }

    def create_query_editor(self, md: dict) -> str:
        """
        Checks if editor is present and returns query to create
        editor or match editor respectively and create relation
        :EDITED_BY to fragment. If no author is present returns
        empty query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            str: Query to merge node for editor and create
            relation.
        """
        if "respStmt" in md:
            query = """
                MERGE (p: person {name: "$name"})
                CREATE (p)<-[:EDITED_BY]-(f)
            """
        else:
            query = ""

        return query

    def get_parameters_editor(self, md: dict) -> dict[str, str]:
        """
        Gets the parameters for the node editor query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            dict[str, str | None]: The parameters
        """
        return {
            "name": md.get("respStmt", {}).get("name")
        }

    def create_query_loaction(self, md: dict) -> str:
        """
        Checks if location is present and returns query to create
        location or match location respectively and create relation
        :EDITED_BY to fragment. If no place is present returns
        empty query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            str: Query to merge node for location and create
            relation.
        """
        if "provenance" in md:
            create_location_query = """
                WITH f, $placeName AS placeName, $region as region
                FOREACH (_ IN CASE WHEN region IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (r:Region {name: region})
                    FOREACH (_ IN CASE WHEN placeName IS NOT NULL THEN [1] ELSE [] END |
                        MERGE (p:Place {name: placeName})
                        MERGE (p)-[:PART_OF_REGION]->(r)
                        MERGE (f)-[:FOUND_IN]->(p)
                    )

                    FOREACH (_ IN CASE WHEN placeName IS NULL THEN [1] ELSE [] END |
                        MERGE (f)-[:FOUND_IN]->(r)
                    )
                )

                WITH f, $expedition_code as expedition_code
                FOREACH (_ IN CASE WHEN expedition_code IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (ec:ExpeditionCode {code: expedition_code})
                    MERGE (f)-[:FOUND_IN_EXPEDITION]->(ec)
                )
            """
        else:
            create_location_query = ""

        return create_location_query

    def get_parameters_location(self, md: dict) -> dict[str, str]:
        """
        Gets the parameters for the node location query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            dict[str, str | None]: The parameters
        """
        return {
            "region": md.get("provenance", {}).get("region"),
            "placeName": md.get("provenance", {}).get("placeName"),
            "expedition_code": md.get("provenance", {}).get("expedition_code")
        }

    def create_query_genre(self, md: dict) -> str:
        """
        Checks if genre and subgenre is present and returns query to create
        genre, subgenre or match them respectively and create relation
        :IS_OF_GENRE to fragment. If no genre is present returns
        empty query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            str: Query to merge node for genre, subgenre and create
            relation.
        """
        if "profileDesc" in md:
            create_genre_query = """
                WITH f, $genre AS genre, $subgenre AS subgenre
                FOREACH (_ IN CASE WHEN genre IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (g:Genre {name: genre})

                    // sub-genre branch, still no WITH inside!
                    FOREACH (_ IN CASE WHEN subgenre IS NOT NULL THEN [1] ELSE [] END |
                        MERGE (sg:SubGenre {name: subgenre})
                        MERGE (sg)-[:SUB_GENRE_OF]->(g)
                        MERGE (f)-[:IS_OF_GENRE]->(sg)
                    )
                    FOREACH (_ IN CASE WHEN subgenre IS NULL THEN [1] ELSE [] END |
                        MERGE (f)-[:IS_OF_GENRE]->(g)
                    )
                )
            """
        else:
            create_genre_query = ""

        return create_genre_query

    def get_parameters_genre(self, md: dict) -> dict[str, str]:
        """
        Gets the parameters for the node location query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            dict[str, str | None]: The parameters
        """
        return {
            "genre": md.get("profileDesc", {}).get("genre"),
            "subgenre": md.get("profileDesc", {}).get("subgenre")
        }

    def create_query_manuscript(self, md: dict) -> str:
        """
        Creates query to create manuscript and connects it to
        fragment if manuscript metadata present, otherwise returns
        empty query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            str: Query to create manuscript node
        """
        create_manuscript_query = ""
        if "msIdentifier" in md:
            create_manuscript_query = """
            MERGE (m: Manuscript {idno: $idno})
                ON CREATE SET
                    m.repository = $repository,
                    m.altIdentifier = $altIdentifier
            MERGE (f) - [:IS_PART_OF] -> (m)
            """
        return create_manuscript_query

    def get_parameters_manuscript(self, md: dict) -> dict[str, str]:
        """
        Gets the parameters for the node location query.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            dict[str, str | None]: The parameters
        """
        return {
            "repository": md.get("msIdentifier", {}).get("repository"),
            "idno": md.get("msIdentifier", {}).get("idno"),
            "altIdentifier": md.get("msIdentifier", {}).get("altIdentifier")
        }

    def create_query_fragment(self, md: dict) -> tuple[str, dict]:
        """
        Creates the query for the fragment creations and returns
        it with the corresponding parameters.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            tuple[str, dict]: Query and parameters.
        """
        query = ""
        query += self.create_query_node_creation(md)
        query += self.create_query_editor(md)
        query += self.create_query_loaction(md)
        query += self.create_query_genre(md)
        query += self.create_query_manuscript(md)
        query += ";"

        parameters = self.get_parameters_node_creation(md) | \
            self.get_parameters_editor(md) | \
            self.get_parameters_location(md) | \
            self.get_parameters_genre(md) | \
            self.get_parameters_manuscript(md)

        return query, parameters

    def create_query_language_usage(self, md: dict):
        """
        Bekomme zuerst eine Antwort auf die frage in der Datei
        Fragen_an_tocharisch_team.md bevor du das implentierst.
        """
        pass

    def link_fragments(self, md: dict) -> None:
        """
        Links the fragments to one another.

        Args:
            md (dict): The dict with the metadata.

        Returns:
            None
        """
        query = """
            WITH $fCurrent AS fCurrent, $fPrev AS fPrev, $fNext AS fNext
            MATCH (f: Fragment {frag_id: fCurrent})
            FOREACH (_ IN CASE WHEN fPrev IS NOT NULL THEN [1] ELSE [] END |
                MERGE (f1: Fragment {frag_id: fPrev})
                CREATE (f)<-[:IS_SUCCESSOR]-(f1)
            )
            FOREACH (_ IN CASE WHEN fNext IS NOT NULL THEN [1] ELSE [] END |
                MERGE (f2: Fragment {frag_id: fNext})
                CREATE (f)<-[:IS_PREDECESSOR]-(f2)
            )
        """
        parameters = {
            "fNext": md["frag_next"],
            "fPrev": md["frag_prev"],
            "fCurrent": md["frag_id"]
        }
        self.conn.query(
            query=query,
            parameters=parameters
        )


class TranscriptionMapper():
    def __init__(
        self
    ) -> None:
        pass

    def extract_w_nodes(self, s_node):
        """
        123
        """
        ws = []
        # First, grab any direct <w>
        if "w" in s_node:
            wlist = s_node["w"]
            if not isinstance(wlist, list):
                wlist = [wlist]
            ws.extend(wlist)

        # Then, recurse into any nested <s>
        if "s" in s_node:
            slist = s_node["s"]
            if not isinstance(slist, list):
                slist = [slist]
            for sub_s in slist:
                ws.extend(self.extract_w_nodes(sub_s))

        return ws

    def prepare_words_for_insertion(
        self,
        lines: dict[str, list[dict[str, str]]]
    ) -> list[dict[str, str]]:
        """
        Prepares the words for insertion, adds line and position in line
        to info.

        Args:
            lines: (dict[str, list[dict[str, str]]]): The lines containing
            the transcription

        Returns:
            list[dict[str, str]]: The words to insert into Neo4j.
        """
        words_ready_insert = []
        for line, word_list in lines.items():
            position_in_line = 1
            for word_dict in word_list:
                if "@corresp" in word_dict:
                    temp_dict = {
                        "line": line,
                        "position_in_line": position_in_line,
                        "corresp": word_dict["@corresp"]
                    }
                    try:
                        word = word_dict.get("supplied")
                        word = f"({word}) {word_dict['#text']}" if word \
                            is not None else f"{word_dict['#text']}"
                        temp_dict["word"] = word
                        temp_dict["translation"] = word_dict["translation"]
                        temp_dict["grammar_info"] = word_dict["grammar_info"]
                    except KeyError:
                        temp_dict["word"] = f"({word_dict.get('supplied')}"
                        temp_dict["translation"] = word_dict["translation"]
                        temp_dict["grammar_info"] = ""
                    words_ready_insert.append(temp_dict)
                    position_in_line += 1
                elif "s" in word_dict:
                    w_nodes = self.extract_w_nodes(word_dict["s"])

                    for w in w_nodes:
                        if "@corresp" not in w:
                            continue

                        # split the "n" attribute into translation and grammar
                        raw_n = w.get("@n", "")
                        parts = raw_n.split("\n")
                        translation = ",".join(
                            p for p in parts if p.startswith("“")
                        )
                        grammar_info = ",".join(
                            p for p in parts if not p.startswith("“")
                        )

                        temp_dict = {
                            "line": line,
                            "position_in_line": position_in_line,
                            "corresp": w["@corresp"],
                            "translation": translation,
                            "grammar_info": grammar_info
                        }

                        supplied = w.get("supplied")
                        text = w.get("#text", "")
                        if supplied is not None:
                            temp_dict["word"] = f"({supplied}) {text}"
                        else:
                            temp_dict["word"] = text

                        words_ready_insert.append(temp_dict)

        return words_ready_insert

    def creaty_query_lines(self) -> str:
        """
        Creates the query to create a line node with its line position.

        Args:
            None.

        Returns:
            str: Query to create node for fragment.
        """
        return """
                MATCH (f:Fragment {frag_id: $frag_id})
                CREATE (l:Line {
                    line_id: $line_id,
                    line_position: $line_position
                })
                MERGE (f)-[:HAS_LINE]->(l)
            """

    def get_parameters_line_node_creation(
        self,
        transcription_dict
    ) -> list[dict]:
        """
        Gets the parameters for the node creation query.

        Args:
            transcription_dict (dict): The dict holding the
            information about the transcription.

        Returns:
            dict[str, str | None]: The parameters
        """
        frag_id = list(transcription_dict.keys())[0]
        temp = transcription_dict[frag_id]
        parameter_dicts = []

        line_ids_position = [
            {"line_id": line_id, "line_position": i, "frag_id": frag_id} for
            i, line_id in enumerate(list(temp.keys()), start=1)
        ]
        for temp_dict in line_ids_position:
            parameter_dicts.append({
                "line_id": temp_dict.get("line_id"),
                "line_position": temp_dict.get("line_position"),
                "frag_id": temp_dict.get("frag_id")
            })

        return parameter_dicts

    def get_query_parameters_line(
        self,
        transcription_dict: dict
    ) -> tuple[str, list[dict]]:
        """
        Returns the query and parameters for the creation
        of a line node.

        Args:
            transcription_dict (dict): The dict holding the
            information about the transcription.

        Returns:
            tuple[str, list[dict]]: Tuple holding the string
            query and the parameters
        """
        query = self.creaty_query_lines()
        parameters = self.get_parameters_line_node_creation(
            transcription_dict=transcription_dict
        )
        return query, parameters

    def creaty_query_words(self) -> str:
        """
        Creates the query to create a line node with its line position.

        Args:
            None.

        Returns:
            str: Query to create node for fragment.
        """
        return """
                MATCH (f:Line {line_id: $line})
                CREATE (w:Word {
                    word: $word,
                    translation: $translation,
                    grammar_info: $grammar_info,
                    position_in_line: $position_in_line,
                    corresp: $corresp
                })
                CREATE (f)-[:HAS_WORD]->(w)
            """

    def get_parameters_word_node_creation(
        self,
        transcription_dict: dict[str, dict[
            str, list[dict[str, dict[str, str]]]
        ]]
    ) -> list[dict]:
        """
        Gets the parameters for the node creation query.

        Args:
            transcription_dict (
                dict[str, dict[str, list[dict[str, dict[str, str]]]]]
            ):  The dict with the line as key and the transcriptions dicts
                as keys

        Returns:
            dict[str, str | None]: The parameters
        """
        key = list(transcription_dict.keys())[0]
        return self.prepare_words_for_insertion(
            transcription_dict[key]
        )

    def get_query_parameters_words(
        self,
        transcription_dict: dict
    ) -> tuple[str, list[dict]]:
        """
        Returns the query and parameters for the creation
        of a word node.

        Args:
            transcription_dict (dict): The dict holding the
            information about the transcription.

        Returns:
            tuple[str, list[dict]]: Tuple holding the string
            query and the parameters
        """
        query = self.creaty_query_words()
        parameters = self.get_parameters_word_node_creation(
            transcription_dict=transcription_dict
        )
        return query, parameters


class TranslationMapper():
    def __init__(
        self
    ) -> None:
        pass

    def creaty_query_literature(self) -> str:
        """
        Creates the query to create a literature node

        Args:
            None.

        Returns:
            str: Query to create node for literature.
        """
        return """
            MERGE (lit: Literature {title: $title})
        """

    def get_parameters_literature_node_creation(
        self,
        translation_list: list[dict[str, dict]]
    ) -> list[dict[str, str]]:
        """
        Gets the parameters for the node creation query.

        Args:
            translation_list list[dict[str, dict]]: The list holding
            the information about the translation.

        Returns:
            list[dict[str, str]]: The parameters
        """
        literature_list = []
        for tran_object in translation_list:
            for _, temp in tran_object.items():
                for inner_tran_object in temp["translation"]:
                    if "lg" in inner_tran_object:
                        continue  # erroneous translation
                    if "bibl" in inner_tran_object["seg"]:
                        title = inner_tran_object["seg"]["bibl"]["title"]["@corresp"]
                        literature_list.append(title.split(":")[1])
        return [{"title": title} for title in list(set(literature_list))]

    def get_query_parameters_literature(
        self,
        translation_list: list[dict[str, dict]]
    ) -> tuple[str, list[dict]]:
        """
        Returns the query and parameters for the creation
        of a line node.

        Args:
            translation_list list[dict[str, dict]]: The dict holding
            the information about the transcription.

        Returns:
            tuple[str, list[dict]]: Tuple holding the string
            query and the parameters
        """
        query = self.creaty_query_literature()
        parameters = self.get_parameters_literature_node_creation(
            translation_list=translation_list
        )
        return query, parameters

    def get_citation_query_params(
        self,
        line_id: str,
        citation_dict: dict
    ) -> dict[str, str | dict[str, str]]:
        """
        Returns the query and the parameters for the creation of
        a relation :CITED_IN between a line and literature for
        citations that aren't about translations.

        Args:
            line_id (str): The ID of the Line.
            citation_dict (dict): The dict containing information
            about citations.

        Returns:
            tuple[str, dict[str, str]]: Tuple containg query and
            corresponding parameters.
        """
        query = """
        MATCH (l:Line {line_id: $line_id})
        MATCH (lit:Literature {title: $title})
        MERGE (l)-[r:CITED_IN]->(lit)
        On CREATE SET r.range = $citedRange
        """
        citation_dict = citation_dict["bibl"]
        title = citation_dict["title"]["@corresp"].split(":")[1]
        citedRange = citation_dict.get("citedRange")

        parameters = {
            "line_id": line_id,
            "title": title,
            "citedRange": citedRange
        }

        return {
            "query": query,
            "parameters": parameters
        }

    def get_translation_query_params_with_citation(
        self,
        line_id: str,
        citation_dict: dict,
        order: int
    ) -> dict[str, str | dict[str, str]]:
        """
        Returns the query and the parameters for the creation of
        a node translation, a relation :HAS_MEANING between a the
        translation and the line, as well as a relation :TRANSLATION_BY
        between a translation and literature.

        Args:
            line_id (str): The ID of the Line.
            citation_dict (dict): The dict containing information
            about citations.
            order (int): Order of translation.

        Returns:
            tuple[str, dict[str, str]]: Tuple containg query and
            corresponding parameters.
        """
        citation = citation_dict["bibl"]
        title = citation["title"]["@corresp"].split(":")[1]
        citedRange = citation_dict.get("citedRange")
        translation = citation_dict["seg"]["#text"]
        query = """
        CREATE (t:Translation {
            uuid: $uuid, translation: $translation
        })
        WITH t
        MATCH (l:Line {line_id: $line_id})
        MATCH (lit:Literature {title: $title})
        CREATE (l)-[hm:HAS_MEANING]->(t)
        SET hm.order = $order
        MERGE  (t)-[r:TRANSLATION_BY]->(lit)
        ON CREATE SET r.range = $citedRange
        """
        parameters = {
            "uuid": str(uuid4()),
            "line_id": line_id,
            "title": title,
            "citedRange": citedRange,
            "translation": translation,
            "order": order
        }

        return {
            "query": query,
            "parameters": parameters
        }

    def get_translation_query_params_no_citation(
        self,
        line_id: str,
        citation_dict: dict,
        order: int
    ) -> dict[str, str | dict[str, str] | int]:
        """
        Returns the query and the parameters for the creation of
        a node translation and a relation :HAS_MEANING between a the
        translation.

        Args:
            line_id (str): The ID of the Line.
            citation_dict (dict): The dict containing information
            about citations.
            order (int): Order of translation.

        Returns:
            tuple[str, dict[str, str]]: Tuple containg query and
            corresponding parameters.
        """
        try:
            translation = citation_dict["#text"]
            query = """
                MERGE (t:Translation {
                    translation: $translation
                })
                ON CREATE SET
                    t.uuid = $uuid
                WITH t
                MATCH (l:Line {line_id: $line_id})
                CREATE (l)-[hm:HAS_MEANING]->(t)
                SET hm.order = $order
            """
            parameters = {
                "uuid": str(uuid4()),
                "translation": translation,
                "line_id": line_id,
                "order": order
            }
        except KeyError:  # Sometimes the translation is missing
            query = ""
            parameters = {}

        return {
            "query": query,
            "parameters": parameters,
            "order": order
        }

    def get_translation_query_params(
        self,
        line_id: str,
        citation_dict: dict,
        order: int
    ) -> dict[str, str | dict[str, str]]:
        """
        Returns the query and the parameters for the creation of
        a node translation, a relation :HAS_MEANING between a the
        translation and the line, as well as a relation :TRANSLATION_BY
        between a translation and literature or Returns the query and the
        parameters for the creation of a node translation and a relation
        :HAS_MEANING between a the translation.

        Args:
            line_id (str): The ID of the Line.
            citation_dict (dict): The dict containing information
            about citations.
            order (int): Order of translation.

        Returns:
            tuple[str, dict[str, str]]: Tuple containg query and
            corresponding parameters.
        """
        if "bibl" in citation_dict:
            return self.get_translation_query_params_with_citation(
                line_id=line_id,
                citation_dict=citation_dict["seg"],
                order=order
            )
        else:
            return self.get_translation_query_params_no_citation(
                line_id=line_id,
                citation_dict=citation_dict["seg"],
                order=order
            )

    def extract_translation_params(
        self,
        translation_list_element: dict
    ) -> list:
        """
        Stuff
        """
        result = []
        counters = defaultdict(int)
        for key in translation_list_element.keys():
            for line in translation_list_element[key]:
                for _, trans_dict in line.items():
                    for line_id in trans_dict["correspond_to_lines"]:
                        for temp_citation in trans_dict["translation"]:
                            if "seg" not in temp_citation and "bibl" not in temp_citation:
                                continue
                            temp_citation = temp_citation["seg"]
                            counters[line_id] += 1
                            if "bibl" in temp_citation:
                                if "seg" in temp_citation:
                                    if "#text" not in temp_citation["seg"]:
                                        continue  # No translation provided
                                    result.append(
                                        self.get_translation_query_params_with_citation(
                                            line_id=line_id,
                                            citation_dict=temp_citation,
                                            order=counters[line_id]
                                        ))
                                else:
                                    result.append(
                                        self.get_citation_query_params(
                                            line_id=line_id,
                                            citation_dict=temp_citation
                                        ))
                            elif "seg" in temp_citation:
                                if "#text" not in temp_citation["seg"]:
                                    continue  # No translation provided
                                result.append(
                                    self.get_translation_query_params(
                                        line_id=line_id,
                                        citation_dict=temp_citation,
                                        order=counters[line_id]
                                    ))
        return result
