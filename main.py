
import json
import time
import requests
import asyncio
from fastapi import FastAPI, Request
import uvicorn
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

WALLET_FILE = "wallets.json"

# Wallets laden oder leere Datei anlegen
def load_wallets():
    try:
        with open(WALLET_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_wallets(wallets):
    with open(WALLET_FILE, "w") as f:
        json.dump(wallets, f, indent=2)

# Telegram-Nachricht senden
def send_message(text):
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
    })

# Dexscreener-Link
def dexscreener_link(token_address):
    return f"https://dexscreener.com/solana/{token_address}"

@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    command_parts = text.strip().split(" ")

    if text.startswith("/start") or text.startswith("/help"):
        help_text = """👋 Willkommen beim RobertsSolTrackerBot!

<b>Verfügbare Befehle:</b>
➕ <code>/add WALLET TAG</code> – Wallet hinzufügen
🗑️ <code>/rm WALLET</code> – Wallet entfernen
📋 <code>/list</code> – Liste der Wallets anzeigen
"""
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": help_text,
            "parse_mode": "HTML"
        })

    elif text.startswith("/add") and len(command_parts) == 3:
        wallet, tag = command_parts[1], command_parts[2]
        wallets = load_wallets()
        wallets[wallet] = tag
        save_wallets(wallets)
        send_message(f"➕ Wallet <b>{wallet}</b> mit Tag <b>{tag}</b> hinzugefügt ✅")

    elif text.startswith("/rm") and len(command_parts) == 2:
        wallet = command_parts[1]
        wallets = load_wallets()
        if wallet in wallets:
            del wallets[wallet]
            save_wallets(wallets)
            send_message(f"🗑️ Wallet <b>{wallet}</b> wurde entfernt.")
        else:
            send_message("❌ Wallet nicht gefunden.")

    elif text.startswith("/list"):
        wallets = load_wallets()
        if wallets:
            message = "📋 <b>Liste der getrackten Wallets:</b>
"
            for w, tag in wallets.items():
                message += f"• {tag}: <code>{w}</code>
"
        else:
            message = "ℹ️ Keine Wallets gespeichert."
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        })

    return {"ok": True}

# Simulierter Checker (alle 60 Sekunden)
async def monitor_wallets():
    while True:
        wallets = load_wallets()
        for wallet, tag in wallets.items():
            # Beispiel-API-Anfrage (hier anpassen!)
            balance = "1.23"  # Dummy-Wert
            token = "tokenaddress123"
            link = dexscreener_link(token)
            send_message(f"🔍 <b>{tag}</b>
Wallet: <code>{wallet}</code>
💰 Balance: {balance} SOL
📊 <a href='{link}'>Dexscreener</a>")
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_wallets())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
