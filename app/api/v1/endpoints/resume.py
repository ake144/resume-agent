from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_resume_status():
    """
    Check the status of the resume data.
    """
    return {"message": "Resume endpoint is active."}
