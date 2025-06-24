import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.run_smart_finder import run_smart_wallet_finder

# Logger
logger = logging.getLogger(__name__)

# Scheduler Setup
scheduler = AsyncIOScheduler()

def start_cronjob():
    logger.info("🚀 Cronjob gestartet: SmartFinder wird alle 30 Minuten ausgeführt.")
    scheduler.add_job(
        lambda: asyncio.create_task(run_smart_wallet_finder()),
        trigger='interval',
        minutes=30,
        id='smart_finder_cron'
    )
    scheduler.start()
