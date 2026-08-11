from datetime import datetime

from langchain_postgres import PGVector
from sqlalchemy import create_engine, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from functools import lru_cache

from app.core.config import settings
from app.core.embeddings import get_embeddings

databaseUrl = settings.database_url

KNOWLEDGE_COLLECTION_NAME = "user_knowledge_base"
TEMP_COLLECTION_NAME = "temporary_documents"

 # Create a SQLAlchemy engine
engine = create_engine(databaseUrl)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for the app's own relational tables.

    Deliberately separate from PGVector's own private declarative base
    (which owns langchain_pg_collection/langchain_pg_embedding) - Alembic
    must only ever manage tables registered on this Base.
    """
    pass


class TimestampMixin:
    """created_at/updated_at columns shared by all app-owned tables."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


def get_db():
    """FastAPI dependency yielding a request-scoped sync SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache(maxsize=8)
def get_knowledge_vector_store(collection_name: str = KNOWLEDGE_COLLECTION_NAME):
    """Permanent user profile RAG"""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=collection_name,
        connection=databaseUrl,
        use_jsonb=True,
    )


@lru_cache(maxsize=8)
def get_temp_vector_store(collection_name: str = TEMP_COLLECTION_NAME):
    """Temporary jobs & generations"""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=collection_name,
        connection=databaseUrl,
        use_jsonb=True,
    )

