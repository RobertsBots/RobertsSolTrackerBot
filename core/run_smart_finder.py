# core/run_smart_finder.py

import os
import httpx
from core.database import add_wallet
from core.helpers import post_wallet_detection_message

DUNE_API_KEY = os.getenv("DUNE_API_KEY")
DUNE_QUERY_ID = "4632804"
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")

headers = {
    "Content-Type": "application/json",
    "x-dune-api-key": DUNE_API_KEY
}

async def run_smart_wallet_finder(bot):
    url = f"https://api.dune.com/api/v1/query/{DUNE_QUERY_ID}/results"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)

        data = response.json()
        rows = data.get("result", {}).get("rows", [])

        for row in rows:
            winrate = row.get("winrate", 0)
            roi = row.get("roi", 0)

            if winrate >= 70 and roi >= 5:
                address = row["wallet"]
                tag = "🚀 AutoDetected"

                added = await add_wallet(address, tag)
                if added:
                    wallet_data = {
                        "winrate": winrate,
                        "roi": roi,
                        "pnl": row.get("realized_pnl", 0),
                        "account_age": row.get("wallet_age_days", "?"),
                        "sol_balance": row.get("sol_balance", 0),
                        "address": address
                    }
                    await post_wallet_detection_message(bot, TELEGRAM_CHANNEL_ID, wallet_data)

    except Exception as e:
        print(f"Fehler bei SmartFinder: {e}")
