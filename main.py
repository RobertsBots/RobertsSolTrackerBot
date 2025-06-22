
from fastapi import FastAPI, Request
import httpx
import os
import json

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

wallets_file = "wallets.json"

def load_wallets():
    if not os.path.exists(wallets_file):
        return {}
    with open(wallets_file, "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open(wallets_file, "w") as f:
        json.dump(wallets, f)

@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    command_parts = text.strip().split(" ")

    if text.startswith("/start") or text.startswith("/help"):
        await send_message(chat_id, "👋 Willkommen beim RobertsSolTrackerBot!

"
                                    "Verfügbare Befehle:
"
                                    "/add <WALLET> <TAG> ➕ Wallet hinzufügen
"
                                    "/rm <WALLET> 🗑️ Wallet entfernen
"
                                    "/list 📋 Liste der Wallets")
    elif text.startswith("/add") and len(command_parts) == 3:
        wallet, tag = command_parts[1], command_parts[2]
        wallets = load_wallets()
        wallets[wallet] = tag
        save_wallets(wallets)
        await send_message(chat_id, f"✅ Wallet <code>{wallet}</code> mit Tag <b>{tag}</b> hinzugefügt.")
    elif text.startswith("/rm") and len(command_parts) == 2:
        wallet = command_parts[1]
        wallets = load_wallets()
        if wallet in wallets:
            del wallets[wallet]
            save_wallets(wallets)
            await send_message(chat_id, f"🗑️ Wallet <code>{wallet}</code> wurde entfernt.")
        else:
            await send_message(chat_id, "⚠️ Wallet nicht gefunden.")
    elif text.startswith("/list"):
        wallets = load_wallets()
        if wallets:
            message = "📋 <b>Liste der getrackten Wallets:</b>
"
            for wallet, tag in wallets.items():
                message += f"
<b>{tag}</b>: <code>{wallet}</code>"
            await send_message(chat_id, message)
        else:
            await send_message(chat_id, "📭 Keine Wallets getrackt.")
    return {"ok": True}

async def send_message(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        })
