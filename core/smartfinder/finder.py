import os
import logging
import httpx
from supabase import create_client

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DUNE_API_KEY = os.getenv("DUNE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DUNE_QUERY_ID = "4632804"
DUNE_API_URL = f"https://api.dune.com/api/v1/query/{DUNE_QUERY_ID}/results"

HEADERS = {
    "Content-Type": "application/json",
    "X-Dune-API-Key": DUNE_API_KEY,
}

async def fetch_smart_wallets():
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(DUNE_API_URL, headers=HEADERS)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"❌ Fehler beim Abrufen der Dune-Daten: {e}")
        return None

def meets_criteria(wallet):
    winrate = wallet.get("winrate", 0)
    roi = wallet.get("roi", 0)
    return winrate >= 70 and roi >= 5

def format_wallet_message(wallet):
    address = wallet["wallet"]
    tag = "🚀 AutoDetected"
    winrate = wallet.get("winrate", 0)
    roi = wallet.get("roi", 0)
    pnl = wallet.get("realized_pnl", 0)
    age = wallet.get("account_age_days", "?")
    balance = wallet.get("sol_balance", "?")

    birdeye_link = f"https://birdeye.so/address/{address}?chain=solana"

    return f"""
📡 <b>Neue smarte Wallet erkannt!</b>

<b>🧠 Wallet:</b> <code>{address}</code>
<b>🏷️ Tag:</b> {tag}
<b>📈 Winrate:</b> {winrate:.1f}% 
<b>📊 ROI:</b> {roi:.1f}%
<b>💸 PnL:</b> {pnl:.2f} SOL
<b>📅 Age:</b> {age} Tage
<b>💰 SOL Balance:</b> {balance:.2f} SOL
🔗 <a href="{birdeye_link}">Birdeye öffnen</a>
"""

async def run_smart_finder(bot, mode="moonbags"):
    data = await fetch_smart_wallets()
    if not data or "result" not in data or "rows" not in data["result"]:
        logging.warning("Keine Wallet-Daten gefunden.")
        return

    rows = data["result"]["rows"]
    filtered = [wallet for wallet in rows if meets_criteria(wallet)]

    logging.info(f"✅ {len(filtered)} passende Smart Wallets erkannt.")

    for wallet in filtered:
        address = wallet["wallet"]
        exists = supabase.table("wallets").select("*").eq("address", address).execute()
        if exists.data:
            continue  # skip if already tracked

        supabase.table("wallets").insert({
            "address": address,
            "tag": "🚀 AutoDetected",
            "pnl": 0,
            "wins": 0,
            "losses": 0
        }).execute()

        message = format_wallet_message(wallet)
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML", disable_web_page_preview=False)
