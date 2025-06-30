import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.smartfinder.run_smart_finder import run_smart_wallet_finder

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def setup_cron_jobs(bot):
    """
    Initialisiert und startet den Cronjob für den SmartFinder.
    Wird alle 30 Minuten ausgeführt.
    """
    try:
        logger.info("🔁 Cronjob aktiviert: SmartFinder wird alle 30 Minuten ausgeführt.")
        scheduler.add_job(
            lambda: asyncio.create_task(run_smart_wallet_finder(bot)),
            trigger='interval',
            minutes=30,
            id='smart_finder_cron',
            replace_existing=True
        )
        scheduler.start()
    except Exception as e:
        logger.error(f"❌ Fehler beim Setup des Cronjobs: {e}")
