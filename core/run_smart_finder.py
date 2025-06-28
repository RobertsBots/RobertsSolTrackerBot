import logging
from core.database import get_finder_mode, get_tracked_wallets, add_wallet
from core.helpers import post_wallet_detection_message
from core.finder import fetch_smart_wallets

logger = logging.getLogger(__name__)

async def run_smart_wallet_finder(dp, bot):
    try:
        mode = await get_finder_mode()
        if not mode:
            logger.info("🔎 SmartFinder ist deaktiviert. Kein Scan durchgeführt.")
            return

        logger.info(f"🛰 SmartFinder aktiv im Modus: {mode.upper()}")

        # Smart Wallets von Dune holen
        smart_wallets = await fetch_smart_wallets(mode)

        if not smart_wallets:
            logger.info("❌ Keine neuen Smart Wallets gefunden.")
            return

        tracked_wallets = await get_tracked_wallets()
        tracked_addresses = [w["wallet"] for w in tracked_wallets]

        for wallet in smart_wallets:
            if wallet["address"] in tracked_addresses:
                continue  # bereits getrackt

            await add_wallet(wallet["address"], tag="🚀 AutoDetected")

            await post_wallet_detection_message(
                bot=bot,
                dp=dp,
                wallet=wallet
            )

            logger.info(f"✅ Neue Smart Wallet getrackt: {wallet['address']}")

    except Exception as e:
        logger.exception(f"⚠️ Fehler im SmartFinder: {str(e)}")
