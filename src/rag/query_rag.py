import os
import sys
from uuid import uuid4
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from langchain_core.documents import Document
try:
    from . import qdrant
    # from ..infrastructure import neo4jconnector
    from ..agents_src import agents
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))

    # sys.path.append(os.path.abspath('../infrastructure'))
    # sys.path.append(os.path.abspath('../agents_src'))
    # import neo4jconnector
    from rag import qdrant
    from agents_src import agents


class RagQuerier:
    def __init__(
        self,
        qdrant_conn: qdrant.QdrantConnection,
        agents: agents.agentCollection
    ) -> None:
        self.conn = qdrant_conn
        self.agents = agents

    def remove_duplicate_result(
        self,
        elements: list[Document],
        final_length: int
    ) -> list[dict[str, dict[str, str] | str]]:
        """
        Removes the duplicates from the element in order of
        appearance until final_length unique elements are left.

        Args:
            elements (list[Document]): The retrieved documents.
            final_length (int): How many unique elements should be
            returned.

        Returns:
            list[dict[str, dict[str, str] | str]]: A list of length
            final_length with only unique entries.
        """
        unique_list = []
        texts_alredy = []
        for element in elements:
            temp = dict(element)
            if len(unique_list) == final_length:
                break
            if temp["page_content"] not in texts_alredy:
                unique_list.append(temp)
                texts_alredy.append(temp["page_content"])

        return unique_list

    def query_store(
        self,
        type_vector: str,
        query: str,
        k: int = 100,
        fragment_id: list[str] | None = None
    ) -> list[Document]:
        """
        Queries the vector store for query on type of vector
        specifided by type_vector.

        Args:
            type_vector (str): Filter for which vector to filter on.
            query (str): Query to use for vector store.
            k (int): How many vectors should be retrieved.
            fragment_id: (list[str] | None):
        """
        type_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.type",
                    match=MatchValue(value=type_vector)
                )
            ]
        )
        return self.conn.vector_store.similarity_search(
            query, k=k, filter=type_filter,
        )

    def rewrite_query(
        self,
        type_vector: str,
        query: str
    ) -> str:
        """
        Queries vector store and uses result to rewrite query.

        Args:
            type_vector (str): Filter for which vector to filter on.
            query (str): Query to use for vector store.

        Returns:
            str: Rewritten query.
        """
        snippets = self.query_store(
            type_vector=type_vector,
            query=query
        )
        snippets = [snippet.page_content for snippet in snippets]
        return self.agents.rewrite_agent(query=query, snippets=snippets)

    def get_relevant_fragments(
        self,
        query: str
    ) -> dict[str, dict[str, str]]:
        """
        Rewrites original user query and returns relevant fragments and
        relevant line in fragment.

        Args:
            query (str): Query to use for vector store.

        Returns:
            dict[str, dict[str, str]]: Relevant Fragments (id) and the
            relevant line (position)
        """
        new_query = self.rewrite_query(
            type_vector="fragment",
            query=query
        )

        relevant_fragments = self.remove_duplicate_result(
            self.query_store(
                type_vector="fragment",
                query=new_query
            ),
            final_length=15
        )
        ranking = self.agents.relevance_agent(
            user_input=query,
            relevant_fragments=relevant_fragments
        )
        return {
            key: dict(value) for key, value in dict(ranking)["root"].items()
        }

    def get_fragment(self, frag_id: str) -> dict[str, str]:
        """
        Gets the fragment by frag_id and returns it's frag_id
        and translation.

        Args:
            frag_id (str): Id of fragment.

        Returns:
            dict[str, str]: Dict with frag_id and fragment
            translation.
        """
        type_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.frag_id",
                    match=MatchValue(value=frag_id)
                ),
                FieldCondition(
                    key="metadata.type",
                    match=MatchValue(value="fragment")
                )
            ]
        )
        response = self.conn.client.scroll(
            collection_name="collection",
            scroll_filter=type_filter,
            limit=1
        )
        return {
            "translation": dict(response[0][0])["payload"]["page_content"],
            "frag_id": frag_id
        }

    def enrich_lines_with_fragments(self, query: str) -> dict:
        """
        Creates dictionary with the fragment ids, the translation
        of the fragment and the retrieved lines.

        Args:
            query (str): Query to use for vector store.

        Returns:
            dict: dictionary with the fragment ids, the translation
            of the fragment and the retrieved lines.
        """
        enriched = {}
        relevant_fragments = self.get_relevant_fragments(query)
        for fragment in relevant_fragments:
            frag_id_temp = fragment["metadata"]["frag_id"]
            if frag_id_temp not in enriched:
                enriched[frag_id_temp] = self.get_fragment(
                    frag_id_temp
                )
                enriched[frag_id_temp]["lines"] = []
            enriched[frag_id_temp]["lines"].append(fragment)

        return enriched
