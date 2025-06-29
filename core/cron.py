# core/cron.py

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.smartfinder.run_smart_finder import run_smart_wallet_finder

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

def setup_cron_jobs(bot):
    logger.info("🚀 Cronjob gestartet: SmartFinder wird alle 30 Minuten ausgeführt.")
    scheduler.add_job(
        lambda: asyncio.create_task(run_smart_wallet_finder(bot)),
        trigger='interval',
        minutes=30,
        id='smart_finder_cron'
    )
    scheduler.start()
