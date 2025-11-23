from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.crawler import fetch_exchange_rates
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def run_crawler_job():
    logger.info("Starting scheduled exchange rate update")
    db = SessionLocal()
    try:
        fetch_exchange_rates(db)
    except Exception as e:
        logger.error(f"Scheduled job failed: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()

def start_scheduler():
    # Run every day at 10:00 AM
    trigger = CronTrigger(hour=10, minute=0)
    scheduler.add_job(run_crawler_job, trigger=trigger, id="exchange_rate_crawler", replace_existing=True)
    
    # Also run once on startup if needed, or we can expose a manual trigger endpoint.
    # For now, let's just schedule it.
    
    scheduler.start()
    logger.info("Scheduler started")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler shut down")
