"""Resume Agent API - Main entry point."""
from app.core.factory import create_app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )

# @app.post("/ingest/resume")
# async def ingest_user_resume(
#     user_id: str,
#     file: UploadFile = None,
#     text: str = None,       
#     title: str = "My Resume"
# ):
#     try:
#         return await ingest_resume(user_id, file, text, title)
#     except Exception as e:
#         print(f"Error occurred while ingesting resume: {e}")
#         handle_error(e, "Failed to ingest resume")



# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
