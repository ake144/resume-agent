import asyncio
from typing import List, Dict, Any
from langchain_core.documents import Document
# from app.core.embeddings import get_embeddings
from app.core.database import get_knowledge_vector_store, get_temp_vector_store

async def retrieve_relevant_resumes(
        query: str,
        user_id: str,
        top_k: int = 5,
        include_jobs: bool = True
)    -> List[Document]:
    """
    Retrieve from permanat base + recent jobs.
    """

    results = []

    kb_store = get_knowledge_vector_store()
    # temp_vector_store = get_temp_vector_store()
    
    kb_docs = await asyncio.to_thread(
        kb_store.similarity_search,
        query,
        top_k,
        {"user_id": user_id},
    )
 
    results.extend(kb_docs)

    if include_jobs:
        temp_store = get_temp_vector_store()  # Replace with actual temp store
        temp_docs = await asyncio.to_thread(
            temp_store.similarity_search,
            query,
            top_k // 2,
            {"user_id": user_id},
        )
        results.extend(temp_docs)

    return results
