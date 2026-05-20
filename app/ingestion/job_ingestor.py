import asyncio
from datetime import datetime, timedelta
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.database import get_temp_vector_store

from app.core.database import get_temp_vector_store


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200)

async def ingest_job(
        user_id: str,
        job_text: str,
        title: str,
        source_url: str=None
):
    docs = text_splitter.create_documents(
        [job_text],
        metadatas=[{"user_id": user_id, "title": title, "document_type": "job", "source_url": source_url}]
    )

    vector_store = get_temp_vector_store()
    ids = [str(uuid.uuid4()) for _ in docs]

    for doc in docs:
        doc.metadata['expires_at'] = (datetime.utcnow() + timedelta(days=7)).isoformat()

    await asyncio.to_thread(vector_store.add_documents, docs, ids=ids)

    return {
        "status": "success",
        "chunks_ingested": len(docs),
         "title": title,
    }