from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
from app.core.database import engine, TEMP_COLLECTION_NAME  # your SQLAlchemy engine
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def cleanup_expired_documents():
    """Delete expired temporary-document embeddings from the PGVector store.

    Runs as a plain sync function (not async): APScheduler's AsyncIOExecutor
    automatically threadpools sync job callables, so this never blocks the
    event loop despite using the app's sync SQLAlchemy engine directly.
    """
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM langchain_pg_embedding e
                    USING langchain_pg_collection c
                    WHERE e.collection_id = c.uuid
                      AND c.name = :collection_name
                      AND (e.cmetadata ->> 'expires_at') IS NOT NULL
                      AND (e.cmetadata ->> 'expires_at')::timestamp < (NOW() AT TIME ZONE 'UTC')
                    RETURNING e.id;
                """),
                {"collection_name": TEMP_COLLECTION_NAME},
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