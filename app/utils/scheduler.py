from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
from app.core.database import engine  # your SQLAlchemy engine
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def cleanup_expired_documents():
    """Delete old temporary documents"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("""
                    DELETE FROM temporary_documents 
                    WHERE expires_at < NOW()
                    RETURNING id;
                """)
            )
            deleted = result.rowcount
            if deleted > 0:
                logger.info(f"🧹 Cleaned up {deleted} expired temporary documents")
            else:
                logger.debug("No expired documents to clean")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

def start_scheduler():
    # Run cleanup every day at 3:00 AM (low traffic time)
    scheduler.add_job(
        cleanup_expired_documents,
        trigger=CronTrigger(hour=3, minute=0),
        id='daily_cleanup',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ APScheduler started - Daily cleanup scheduled at 3:00 AM")