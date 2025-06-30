import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.smartfinder.run_smart_finder import run_smart_wallet_finder
from core.live_wallet_tracker import check_wallet_activity

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def setup_cron_jobs(bot):
    """
    Initialisiert und startet die Cronjobs:
    - SmartFinder alle 30 Minuten
    - WalletTracker alle 60 Sekunden
    """
    try:
        logger.info("🕒 Cronjob Setup gestartet...")

        scheduler.add_job(
            lambda: asyncio.create_task(run_smart_wallet_finder(bot)),
            trigger='interval',
            minutes=30,
            id='smart_finder_cron',
            replace_existing=True
        )
        logger.info("✅ Cronjob: SmartFinder läuft alle 30 Minuten.")

        scheduler.add_job(
            lambda: asyncio.create_task(check_wallet_activity(bot)),
            trigger='interval',
            seconds=60,
            id='wallet_tracker_cron',
            replace_existing=True
        )
        logger.info("✅ Cronjob: WalletTracker läuft alle 60 Sekunden.")

        scheduler.start()
    except Exception as e:
        logger.error(f"❌ Fehler beim Setup der Cronjobs: {e}")
