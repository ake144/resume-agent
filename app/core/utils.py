import logging
from fastapi import HTTPException



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_error(e:Exception, message:str="An error occurred"):
    logger.error(f"{message}: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail=f"{message}: {str(e)}")