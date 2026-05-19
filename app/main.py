from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Load environment variables BEFORE importing internal modules
load_dotenv()

import asyncio
from app.agents.matcher import match_job_to_user
from app.ingestion.job_ingestor import ingest_job
from app.utils.scheduler import start_scheduler, scheduler

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    start_scheduler()
    yield
    # Shutdown the scheduler on app exit
    scheduler.shutdown()

app = FastAPI(
    title="Resume Agent API",
    description="API for managing and querying resume data using PGVector and Groq",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main API router
# app.include_router(prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Resume Agent API!",
        "status": "success",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/ingest/job")
async def ingest_user_job(
    user_id: str,
    job_text: str,
    title: str,
    source_url: str = None
):
    return await ingest_job(user_id, job_text, title, source_url)
    

@app.post("/match/job")
async def match_job(
    user_id:str,
    job_text: str,
    job_title: str,
):
    return await match_job_to_user(user_id, job_text, job_title)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)