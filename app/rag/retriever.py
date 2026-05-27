import asyncio
import hashlib
import time
from typing import List, Tuple

from langchain_core.documents import Document

from app.core.config import settings
from app.core.database import get_knowledge_vector_store, get_temp_vector_store


_RETRIEVAL_CACHE: dict[Tuple[str, str, int, bool], tuple[float, List[Document]]] = {}


def _cache_key(query: str, user_id: str, top_k: int, include_jobs: bool) -> Tuple[str, str, int, bool]:
    query_hash = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
    return (user_id, query_hash, top_k, include_jobs)


def _get_cached_result(key: Tuple[str, str, int, bool]) -> List[Document] | None:
    cached = _RETRIEVAL_CACHE.get(key)
    if not cached:
        return None

    expires_at, docs = cached
    if expires_at < time.monotonic():
        _RETRIEVAL_CACHE.pop(key, None)
        return None
    return docs

async def retrieve_relevant_resumes(
        query: str,
        user_id: str,
        top_k: int = 5,
        include_jobs: bool = True
)    -> List[Document]:
    """
    Retrieve from permanat base + recent jobs.
    """

    cache_key = _cache_key(query=query, user_id=user_id, top_k=top_k, include_jobs=include_jobs)
    cached_docs = _get_cached_result(cache_key)
    if cached_docs is not None:
        return cached_docs

    results = []

    kb_store = get_knowledge_vector_store()
    
    kb_docs = await asyncio.to_thread(
        kb_store.similarity_search,
        query,
        top_k,
        {"user_id": user_id},
    )
 
    results.extend(kb_docs)

    if include_jobs:
        temp_store = get_temp_vector_store()
        job_top_k = max(1, int(top_k * settings.retrieval_jobs_fraction))
        temp_docs = await asyncio.to_thread(
            temp_store.similarity_search,
            query,
            job_top_k,
            {"user_id": user_id},
        )
        results.extend(temp_docs)

    _RETRIEVAL_CACHE[cache_key] = (
        time.monotonic() + max(0, settings.retrieval_cache_ttl_seconds),
        results,
    )

    return results
