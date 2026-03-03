from qdrant_client.http.models import Distance, VectorParams
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from collections import Counter
from typing import Literal
import json
import os
import requests
from dotenv import load_dotenv
load_dotenv()
# QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")   # default if missing


class QdrantConnection():
    def __init__(
        self,
        embeddings: OpenAIEmbeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        ),
        host: str | None = None,
        port: int | None = None,
        local: bool = True
    ) -> None:
        self.host = host if host is not None else os.getenv("QDRANT_HOST", "localhost")
        env_port = os.getenv("QDRANT_PORT", "6333")
        self.port = port if port is not None else int(env_port)
        self.local = local
        self.client = self.init_client()
        self.embedding_model = embeddings
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name="collection",
            embedding=embeddings,
        )

    def init_client(self) -> QdrantClient:
        """
        Inits the client with an empty collection.

        Args:
            None.

        Returns:
            QdrantClient: The initialized Client.
        """
        if self.local:
            client = QdrantClient(
                f"http://{self.host}:{self.port}",
                timeout=60
            )
        else:
            client = QdrantClient(":memory:")

        try:
            client.create_collection(
                collection_name="collection",
                vectors_config=VectorParams(
                    size=1536,  # 3072,
                    distance=Distance.COSINE
                )
            )
            print("Created Vector Store Collection")
        except Exception as e:  # Collection already exists
            print(f"Error creating Vector stor: {e}")

        return client
