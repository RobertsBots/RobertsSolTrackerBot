import os
import httpx
import logging
from aiogram import Bot
from core.database import add_wallet
from core.helpers import post_wallet_detection_message

DUNE_API_KEY = os.getenv("DUNE_API_KEY")
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")
DUNE_BASE_URL = "https://api.dune.com/api/v1/query"

logger = logging.getLogger(__name__)

headers = {
    "Content-Type": "application/json",
    "x-dune-api-key": DUNE_API_KEY
}

# Setze hier deine echten Dune Query-IDs für Moonbags und Scalping ein
QUERY_IDS = {
    "moon": "4632804",    # Beispiel-ID Moonbags (ersetze mit deiner echten!)
    "scalp": "4632805"    # Beispiel-ID Scalping (ersetze mit deiner echten!)
}

async def fetch_wallets(bot: Bot, mode: str):
    if not DUNE_API_KEY or not TELEGRAM_CHANNEL_ID:
        logger.error("❌ DUNE_API_KEY oder CHANNEL_ID fehlt.")
        return

    query_id = QUERY_IDS.get(mode)
    if not query_id:
        logger.error(f"❌ Ungültiger Finder-Modus: {mode}")
        return

    url = f"{DUNE_BASE_URL}/{query_id}/results"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = await response.json()
            rows = data.get("result", {}).get("rows", [])

            if not rows:
                logger.warning(f"⚠️ Dune API hat keine Wallets für Modus {mode} zurückgegeben.")
                return

            for row in rows:
                try:
                    winrate = float(row.get("winrate", 0))
                    roi = float(row.get("roi", 0))

                    # Beispiel Filter - anpassen nach Modus
                    if winrate >= 70 and roi >= (10 if mode == "moon" else 5):
                        wallet_address = row.get("wallet", "")
                        if not wallet_address:
                            continue

                        wallet_data = {
                            "address": wallet_address,
                            "winrate": winrate,
                            "roi": roi,
                            "pnl": float(row.get("realized_pnl", 0)),
                            "account_age": int(row.get("wallet_age_days", 0)),
                            "sol_balance": float(row.get("sol_balance", 0))
                        }

                        added = await add_wallet(user_id=0, wallet=wallet_address, tag="🚀 AutoDetected")

                        if added:
                            await post_wallet_detection_message(
                                bot=bot,
                                channel_id=TELEGRAM_CHANNEL_ID,
                                wallet=wallet_data
                            )
                            logger.info(f"✅ Neue Wallet automatisch hinzugefügt: {wallet_address}")
                        else:
                            logger.info(f"🔁 Wallet bereits vorhanden: {wallet_address}")

                except Exception as row_err:
                    logger.warning(f"⚠️ Fehler beim Verarbeiten einer Wallet-Zeile: {row_err}")
                    continue

    except httpx.RequestError as e:
        logger.exception(f"🌐 Verbindungsfehler bei der Dune API: {e}")
    except httpx.HTTPStatusError as e:
        logger.exception(f"❌ Fehlerhafte HTTP-Antwort: {e.response.status_code}")
    except Exception as e:
        logger.exception(f"❌ Unerwarteter Fehler im Smart Wallet Finder: {e}")

async def run_smart_wallet_finder(bot: Bot, mode: str = "moon"):
    """
    Startet den Smart Wallet Finder für den gegebenen Modus.
    mode: 'moon' oder 'scalp'
    """
    await fetch_wallets(bot, mode)
