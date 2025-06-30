from abc import abstractmethod, ABC
from typing import Any, Dict, List


class VectorDatabase(ABC):
    """
    Abstract base class for vector databases.
    """

    @abstractmethod
    def insert_item(self, collection_name: str, vector: list[float], metadata: dict = None) -> Dict[str, Any]:
        """
        Insert a vector into the database.

        Args:
            collection_name (str): The name of the collection where the vector will be stored.
            vector (list[float]): The vector to insert.
            metadata (dict): Optional metadata associated with the vector.

        Returns:
            str: A unique identifier for the inserted vector.
        """
        pass

    @abstractmethod
    def vector_search(self,  collection_name: str, query_vector: list[float], top_k: int = 10,
            score_threshold: float = None, filter_key: str = None,
            filter_value: str = None) -> list[Any]:
        """
        Search for similar vectors in the database.

        Args:
            collection_name (str): The name of the collection to search in.
            query_vector (list[float]): The vector to search for.
            top_k (int): The number of top results to return.
            score_threshold (float): Optional threshold for filtering results based on similarity score.
            filter_key (str): Optional filter key to filter results based on similarity score.
            filter_value (str): Optional filter value to filter results based on similarity score.

        Returns:
            list[dict]: A list of dictionaries containing the matching vectors and their metadata.
        """
        pass

    @abstractmethod
    def check_collection(self, collection_name: str) -> bool:
        """
        Check if a collection exists in the database.
        Args:
            collection_name (str): The name of the collection to check.
        Returns:
            bool: True if the collection exists, False otherwise.
        """
        pass

    @abstractmethod
    def create_collection(self, collection_name: str):
        """
        Create a new collection in the database.

        Args:
            collection_name (str): The name of the collection to create.
        """
        pass

    @abstractmethod
    def get_all_collections(self) -> List[str]:
        """
        Get a list of all collections in the database.

        Returns:
            List[str]: A list of collection names.
        """
        pass