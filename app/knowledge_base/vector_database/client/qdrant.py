import uuid
from typing import List
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.conversions.common_types import (
    UpdateResult,
)
from qdrant_client.http.models import (
    ScoredPoint
)

from app.knowledge_base.vector_database.vector_database import VectorDatabase


class QdrantDBClient(VectorDatabase):
    """
    Singleton class for managing interactions with a Qdrant vector database.
    """

    def __init__(self, host: str, port: int, vector_size: int = 1024):
        try:
            self.client = QdrantClient(url=host, port=port)
            check_collection = self.client.collection_exists(collection_name="course")
            if not check_collection:
                self.client.create_collection(
                    collection_name="course",
                    vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                )

        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Qdrant database, please provide valid host and port. Error: {e}")

    def insert_item(self,
                    collection_name: str,
                    vector: List[float],
                    metadata: dict = None,
                    ) -> UpdateResult:
        try:
            result = self.client.upsert(
                collection_name=collection_name,
                points=[models.PointStruct(
                    id=str(uuid.uuid4()),
                    payload=metadata,
                    vector=vector
                )
                ]
            )
            return result
        except Exception as e:
            raise e

    def vector_search(
            self, collection_name: str, query_vector: list[float], top_k: int = 10,
            score_threshold: float = None, filter_key: str = None,
            filter_value: str = None
    ) -> List[ScoredPoint]:
        try:
            if filter_key and filter_value:
                filter = Filter(
                    must=[
                        FieldCondition(
                            key=filter_key,
                            match=MatchValue(value=filter_value)
                        )
                    ]
                )
            else:
                filter = None
            result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=filter
            )
            return result
        except Exception as e:
            raise e

    def check_collection(self, collection_name: str) -> bool:
        try:
            check_collection = self.client.collection_exists(collection_name=f"haj")
            return check_collection
        except Exception as e:
            raise e

    def create_collection(self, collection_name: str):
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
        )
