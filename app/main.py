from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

load_dotenv()

from app.core.utils import handle_error
from app.ingestion.resume_ingestor import ingest_resume

from app.agents.generator import generate_application_package
from app.agents.workflow import build_application_graph

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
    try:
        return await ingest_job(user_id, job_text, title, source_url)
    except Exception as e:
        print(f"Error occurred while ingesting job: {e}")
        handle_error(e, "Failed to ingest job")

@app.post("/match/job")
async def match_job(
    user_id:str,
    job_text: str,
    job_title: str,
):
    return await match_job_to_user(user_id, job_text, job_title)

@app.post("/generate/application")
async def generate_application(
    user_id: str,
    job_description: str,
    job_title: str,
    type: str = "cover_letter"
):
    return await generate_application_package(user_id, job_description, job_title, type)

@app.post("/workflow/apply")
async def full_application_workflow(
    user_id: str,
    job_description: str,
    job_title: str
):
    initial_state = {
        "user_id": user_id,
        "job_description": job_description,
        "job_title": job_title
    }
    result = await build_application_graph.ainvoke(initial_state)
    return result

@app.post("/ingest/resume")
async def ingest_user_resume(
    user_id: str,
    file: UploadFile = None,
    text: str = None,       
    title: str = "My Resume"
):
    try:
        return await ingest_resume(user_id, file, text, title)
    except Exception as e:
        print(f"Error occurred while ingesting resume: {e}")
        handle_error(e, "Failed to ingest resume")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
