from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()

app = FastAPI(
    title="Resume Agent API",
    description="API for managing and querying resume data using PGVector and Groq",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Resume Agent API!",
            "status": "success",}

@app.get("/health")
async def health():
    return {"status": "healthy"}