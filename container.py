import os
from dotenv import load_dotenv

from app.knowledge_base.knowledge_base import KnowledgeBase
from app.knowledge_base.vector_database.factory import VectorDatabaseFactory
from app.knowledge_base.vector_embedding.factory import VectorEmbeddingFactory

# Load environment variables
load_dotenv()

# Retrieve environment variables
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
cohere_api_key = os.getenv("COHERE_API_KEY")

# Construct objects
vector_database = VectorDatabaseFactory().create_vector_database(
    db_type="qdrant",
    host=qdrant_host,
    port=qdrant_port,
    vector_size=1024
)

cohere_vector_embedding = VectorEmbeddingFactory().create_vector_embedding(
    embed_type="cohere",
    api_key=cohere_api_key,
)

knowledge_base = KnowledgeBase(
    vector_embeddings=cohere_vector_embedding,
    vector_database=vector_database,
)

