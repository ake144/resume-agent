from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio
from app.utils.scheduler import start_scheduler
import uvicorn
from app.core.config import settings
from app.api.v1.router import api_router

load_dotenv()

app = FastAPI(
    title="Resume Agent API",
    description="API for managing and querying resume data using PGVector and Groq",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main API router
app.include_router(api_router, prefix="/api/v1")

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

@app.on_event("startup")
async def startup_event():
    # Start the scheduler in the background
    asyncio.create_task(start_scheduler())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)