import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

wallets_file = "wallets.json"

def load_wallets():
    if not os.path.exists(wallets_file):
        return {}
    with open(wallets_file, "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open(wallets_file, "w") as f:
        json.dump(wallets, f)

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h2>🤖 RobertsSolTrackerBot is running!</h2>"

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        command_parts = text.strip().split(" ")

        if text.startswith("/start") or text.startswith("/help"):
            reply = "👋 Willkommen beim RobertsSolTrackerBot!"

Verfügbare Befehle:   """
"                     /add <WALLET> <TAG> ➕ Wallet hinzufügen
"                     /rm <WALLET> 🗑️ Wallet entfernen
"                     /list 📋 Liste der Wallets
                      """
        elif text.startswith("/add") and len(command_parts) == 3:
            wallet, tag = command_parts[1], command_parts[2]
            wallets = load_wallets()
            wallets[wallet] = tag
            save_wallets(wallets)
            reply = f"✅ Wallet <code>{wallet}</code> mit Tag <b>{tag}</b> hinzugefügt."
        elif text.startswith("/rm") and len(command_parts) == 2:
            wallet = command_parts[1]
            wallets = load_wallets()
            if wallet in wallets:
                del wallets[wallet]
                save_wallets(wallets)
                reply = f"🗑️ Wallet <code>{wallet}</code> entfernt."
            else:
                reply = f"⚠️ Wallet <code>{wallet}</code> nicht gefunden."
        elif text.startswith("/list"):
            wallets = load_wallets()
            if wallets:
                text = """📋 <b>Getrackte Wallets</b>

"""
                for w, t in wallets.items():
                    text += f"""• <code>{w}</code> – <b>{t}</b>
"""
                reply = text
            else:
                reply = "ℹ️ Es sind derzeit keine Wallets getrackt."
        else:
            reply = "❓ Unbekannter Befehl. Nutze /help für Hilfe."

        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply,
            "parse_mode": "HTML"
        })

    return {"ok": True}
