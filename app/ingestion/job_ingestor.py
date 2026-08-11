import asyncio
from datetime import datetime, timedelta
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.core.database import get_temp_vector_store
from app.db.models import JobPosting


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200)


def _save_job_posting_sync(db: Session, job_posting: JobPosting) -> JobPosting:
    db.add(job_posting)
    db.commit()
    db.refresh(job_posting)
    return job_posting


async def ingest_job(
        db: Session,
        user_id: str,
        job_text: str,
        title: str,
        source_url: str = None,
        company: str = None,
        location: str = None,
):
    # Structured row first (so its id can be cross-linked into the embedded
    # chunks' metadata below); the row persists indefinitely, independent of
    # the chunks' 7-day TTL - see app/db/models.py:JobPosting.
    job_posting = JobPosting(
        user_id=uuid.UUID(user_id),
        title=title,
        company=company,
        location=location,
        description=job_text,
        source_url=source_url,
    )
    # Sync SQLAlchemy call from an async function: threadpooled the same way
    # vector_store.add_documents is below, to avoid blocking the event loop.
    job_posting = await asyncio.to_thread(_save_job_posting_sync, db, job_posting)

    docs = text_splitter.create_documents(
        [job_text],
        metadatas=[{
            "user_id": user_id,
            "title": title,
            "document_type": "job",
            "source_url": source_url,
            "job_posting_id": str(job_posting.id),
        }]
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
        "job_posting_id": str(job_posting.id),
    }
