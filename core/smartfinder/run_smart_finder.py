import os
import httpx
import logging
from aiogram import Bot
from core.database import add_wallet
from core.helpers import post_wallet_detection_message

DUNE_API_KEY = os.getenv("DUNE_API_KEY")
DUNE_QUERY_ID = "4632804"
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")

logger = logging.getLogger(__name__)

headers = {
    "Content-Type": "application/json",
    "x-dune-api-key": DUNE_API_KEY
}

async def run_smart_wallet_finder(bot: Bot):
    if not DUNE_API_KEY:
        logger.error("❌ DUNE_API_KEY fehlt in Umgebungsvariablen.")
        return
    if not TELEGRAM_CHANNEL_ID:
        logger.error("❌ CHANNEL_ID fehlt in Umgebungsvariablen.")
        return

    url = f"https://api.dune.com/api/v1/query/{DUNE_QUERY_ID}/results"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        data = response.json()
        rows = data.get("result", {}).get("rows", [])

        if not rows:
            logger.warning("⚠️ Keine Smart Wallets in der Dune-Antwort gefunden.")
            return

        for row in rows:
            winrate = row.get("winrate", 0)
            roi = row.get("roi", 0)

            if winrate >= 70 and roi >= 5:
                wallet_address = row.get("wallet", "")
                if not wallet_address:
                    continue

                wallet_data = {
                    "address": wallet_address,
                    "winrate": winrate,
                    "roi": roi,
                    "pnl": row.get("realized_pnl", 0),
                    "account_age": row.get("wallet_age_days", "?"),
                    "sol_balance": row.get("sol_balance", 0)
                }

                added = await add_wallet(user_id=0, wallet=wallet_data["address"], tag="🚀 AutoDetected")

                if added:
                    await post_wallet_detection_message(
                        bot=bot,
                        channel_id=TELEGRAM_CHANNEL_ID,
                        wallet=wallet_data
                    )
                    logger.info(f"✅ Neue Wallet automatisch hinzugefügt: {wallet_address}")
                else:
                    logger.info(f"⚠️ Wallet bereits bekannt: {wallet_address}")

    except httpx.RequestError as e:
        logger.exception(f"🌐 Verbindungsfehler bei Dune API: {e}")
    except httpx.HTTPStatusError as e:
        logger.exception(f"❌ Fehlerhafte Antwort von Dune API: {e.response.status_code}")
    except Exception as e:
        logger.exception(f"❌ Unerwarteter Fehler beim Smart Wallet Finder: {e}")
