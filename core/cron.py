import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
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

        loop = asyncio.get_event_loop()

        def run_async(coro):
            """Hilfsfunktion, um async Coroutine threadsafe im Loop auszuführen"""
            return asyncio.run_coroutine_threadsafe(coro, loop)

        scheduler.add_job(
            lambda: run_async(run_smart_wallet_finder(bot)),
            trigger=IntervalTrigger(minutes=30),
            id='smart_finder_cron',
            replace_existing=True
        )
        logger.info("✅ Cronjob: SmartFinder läuft alle 30 Minuten.")

        scheduler.add_job(
            lambda: run_async(check_wallet_activity(bot)),
            trigger=IntervalTrigger(seconds=60),
            id='wallet_tracker_cron',
            replace_existing=True
        )
        logger.info("✅ Cronjob: WalletTracker läuft alle 60 Sekunden.")

        scheduler.start()

    except Exception as e:
        logger.error(f"❌ Fehler beim Setup der Cronjobs: {e}")
