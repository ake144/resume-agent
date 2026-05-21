from langchain_postgres import PGVector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.core.config import settings
from app.core.embeddings import get_embeddings

databaseUrl = settings.database_url

 # Create a SQLAlchemy engine
engine = create_engine(databaseUrl)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_knowledge_vector_store(collection_name: str = "user_knowledge_base"):
    """Permanent user profile RAG"""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=collection_name,
        connection=databaseUrl,
        use_jsonb=True,
    )

def get_temp_vector_store(collection_name: str = "temporary_documents"):
    """Temporary jobs & generations"""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=collection_name,
        connection=databaseUrl,
        use_jsonb=True,
    )

