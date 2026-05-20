from langchain_postgres import PGVector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.core.config import settings
from app.core.embeddings import get_embeddings

 # Create a SQLAlchemy engine
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_knowledge_vector_store():
    """Permanent user profile RAG"""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name="user_knowledge_base",
        connection=settings.database_url,
        use_jsonb=True,
    )

def get_temp_vector_store():
    """Temporary jobs & generations"""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name="temporary_documents",
        connection=settings.database_url,
        use_jsonb=True,
    )
