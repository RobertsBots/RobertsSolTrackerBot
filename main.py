import json
import os
import uvicorn
from fastapi import FastAPI, Request
from utils import load_wallets, save_wallets

import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

app = FastAPI()

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not text.startswith("/"):
        return {"ok": True}

    if text.startswith("/add "):
        parts = text.split()
        if len(parts) != 3:
            await send_message(chat_id, "❌ Usage: /add <wallet> <tag>")
        else:
            wallet, tag = parts[1], parts[2]
            wallets = load_wallets()
            wallets[wallet] = tag
            save_wallets(wallets)
            await send_message(chat_id, f"✅ Wallet {wallet} mit Tag '{tag}' hinzugefügt.")

    elif text.startswith("/rm "):
        parts = text.split()
        if len(parts) != 2:
            await send_message(chat_id, "❌ Usage: /rm <wallet>")
        else:
            wallet = parts[1]
            wallets = load_wallets()
            if wallet in wallets:
                tag = wallets.pop(wallet)
                save_wallets(wallets)
                await send_message(chat_id, f"🗑️ Wallet {wallet} (Tag: '{tag}') entfernt.")
            else:
                await send_message(chat_id, f"⚠️ Wallet {wallet} nicht gefunden.")

    elif text.startswith("/list"):
        wallets = load_wallets()
        if not wallets:
            await send_message(chat_id, "📭 Keine Wallets gespeichert.")
        else:
            msg = "📋 Aktuell getrackte Wallets:

"
            for wallet, tag in wallets.items():
                msg += f"🔹 {wallet} → {tag}
"
            await send_message(chat_id, msg)

    return {"ok": True}

async def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)