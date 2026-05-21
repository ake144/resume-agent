import asyncio
import datetime
import io
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.database import get_knowledge_vector_store
from app.core.utils import logger
import uuid
from fastapi import UploadFile

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", "!", "?", " ", ""]
)

async def ingest_resume(user_id: str, file: UploadFile = None, text: str = None, title: str = "My Resume"):
    try:
        if file:
            content = await file.read()
            if file.filename.lower().endswith(".pdf"):
                pdf_reader = PdfReader(io.BytesIO(content))
                resume_text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
            else:
                resume_text = content.decode("utf-8")
        else:
            resume_text = text

        if not resume_text or len(resume_text.strip()) < 50:
            raise ValueError("Resume content is too short or empty")

        # Split into chunks
        docs = text_splitter.create_documents(
            [resume_text],
            metadatas=[{
                "user_id": user_id,
                "document_type": "resume",
                "title": title,
                "ingested_at": datetime.datetime.now().isoformat()
            }]
        )

        vector_store = get_knowledge_vector_store("user_knowledge_base")
        ids = [str(uuid.uuid4()) for _ in docs]

        await asyncio.to_thread(vector_store.add_documents, docs, ids=ids)

        logger.info(f"Successfully ingested resume for user {user_id} | Chunks: {len(docs)}")
        
        return {
            "status": "success",
            "message": "Resume ingested successfully",
            "chunks_ingested": len(docs),
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Resume ingestion failed for user {user_id}: {e}")
        raise