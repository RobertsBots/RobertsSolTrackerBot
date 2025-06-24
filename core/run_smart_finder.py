import os
import logging
import requests
from core.database import supabase_client
from telegram import Bot
from core.helpers import post_wallet_detection_message

DUNE_API_KEY = os.getenv("DUNE_API_KEY")
DUNE_QUERY_ID = "4632804"  # Deine Smart Wallet Finder Query
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)
logger = logging.getLogger(__name__)

async def run_smart_wallet_finder():
    logger.info("🔎 Starte Smart Wallet Finder...")

    url = f"https://api.dune.com/api/v1/query/{DUNE_QUERY_ID}/results"
    headers = {"x-dune-api-key": DUNE_API_KEY}

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        wallets = data.get("result", {}).get("rows", [])
        if not wallets:
            logger.warning("⚠️ Keine Wallets gefunden.")
            return

        for wallet in wallets:
            try:
                winrate = float(wallet.get("winrate", 0))
                roi = float(wallet.get("roi", 0))

                if winrate < 70 or roi < 5:
                    continue  # Nur starke Wallets

                wallet_address = wallet.get("wallet")
                existing = supabase_client.table("wallets").select("address").eq("address", wallet_address).execute()
                if existing.data:
                    continue  # Bereits getrackt

                # Tag setzen & einfügen
                tag = "🚀 AutoDetected"
                supabase_client.table("wallets").insert({"address": wallet_address, "tag": tag}).execute()

                await post_wallet_detection_message(bot, wallet_address, wallet, tag)

            except Exception as inner_error:
                logger.error(f"❌ Fehler beim Verarbeiten einer Wallet: {inner_error}")

    except Exception as e:
        logger.error(f"❌ Fehler bei Dune API oder Supabase: {e}")
