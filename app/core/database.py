from langchain_postgres import PGVector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.core.config import settings

 # Create a SQLAlchemy engine
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_vector_store(document_name:str = "user_resume") -> PGVector:
    return PGVector(
        collection_name=document_name,
        embeddings=None,  # You can specify your embedding function here
        connection=engine
    )
