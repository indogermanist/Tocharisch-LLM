import os
import sys
from uuid import uuid4
from langchain_core.documents import Document
try:
    from . import qdrant
    from ..infrastructure import neo4jconnector
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))
    
    # sys.path.append(os.path.abspath('../infrastructure'))
    from infrastructure import neo4jconnector
    # from . import qdrant
    from rag import qdrant


class Neo4jQdrantConnector():
    def __init__(
        self,
        neo4j_conn: neo4jconnector.Neo4jConnection,
        qdrant_conn: qdrant.QdrantConnection
    ) -> None:
        self.neo4j_conn = neo4j_conn
        self.qdrant_conn = qdrant_conn

    def get_query_translation(
        self
    ) -> str:
        """
        Create the query to get the fragment translations.

        Args:
            None.

        Returns:
            str: The query to get the translations of the
            fragment.
        """
        return """
        MATCH (f:Fragment {frag_id: $frag_id})-[:HAS_LINE]->(l:Line)
        OPTIONAL MATCH (l)-[hm:HAS_MEANING]->(tr:Translation)
        WITH f, l, tr, hm
        ORDER BY l.line_position, hm.order
        RETURN
        f.frag_id AS fragID,
        l.line_id        AS lineId,
        l.line_position  AS linePosition,
        hm.order AS order_translation,
        collect(
            CASE WHEN tr IS NOT NULL THEN
            {text: tr.translation}
            END
        ) AS translations
        ORDER BY linePosition, order_translation;
        """

    def get_translation_fragment(self, frag_id: str) -> Document:
        """
        Queries Neo4j to get the whole translations and
        returns a Document with translation.

        Args:
            frag_id (str): ID of the fragment.

        Returns:
            Document: Translation as page content and frag_id
            as metadata
            dict[str, str]: Dict with ID of fragment as key
            and whole translation as value.
        """
        translations = self.neo4j_conn.query(
            query=self.get_query_translation(),
            parameters={"frag_id": frag_id}
        )
        whole_text = []
        current_text = ""
        for translation in translations:
            text = translation["translations"][0]["text"]
            if current_text == text:
                # Translation spans more than one line
                continue
            current_text = text
            whole_text.append(current_text)

        return Document(
            page_content="\n".join(whole_text),
            metadata={
                "frag_id": frag_id,
                "type": "fragment"
            }
        )

    def get_translation_line(self, frag_id: str) -> list[Document]:
        """
        Queries Neo4j to get translations of lines and returns a list
        of Documents with these translation as well as metadata.

        Args:
            frag_id (str): ID of the fragment.

        Returns:
            Document: Translation as page content and frag_id
            as metadata
            dict[str, str]: Dict with ID of fragment as key
            and whole translation as value.
        """
        line_documents = []
        translations = self.neo4j_conn.query(
            query=self.get_query_translation(),
            parameters={"frag_id": frag_id}
        )
        for translation in translations:
            line_documents.append(Document(
                page_content=translation["translations"][0]["text"],
                metadata={
                    "frag_id": translation["fragID"],
                    "lineId": translation["lineId"],
                    "linePosition": translation["linePosition"],
                    "order_translation": translation["order_translation"],
                    "type": "line"
                }
            ))

        return line_documents

    def insert_fragment_translation(
        self,
        frag_id: str
    ) -> None:
        """
        Gets the translation of the lines of the fragment as well
        as the whole translation and inserts it Qdrant.

        Args:
            frag_id (str): ID of the fragment.

        Returns:
            None.
        """
        documents = self.get_translation_line(frag_id=frag_id)
        documents.append(self.get_translation_fragment(frag_id=frag_id))
        self.qdrant_conn.vector_store.add_documents(documents)

    def insert_all_fragments_translation(self) -> None:
        """
        Loads all fragments with their translation into Qdrant.

        Args:
            None.

        Returns:
            None.
        """
        query = """Match (f:Fragment) Return f.frag_id"""
        frag_ids = self.neo4j_conn.query(query=query)
        for frag_id in frag_ids:
            try:
                self.insert_fragment_translation(
                    frag_id=frag_id[0]
                )
            except IndexError:
                print(frag_id)
