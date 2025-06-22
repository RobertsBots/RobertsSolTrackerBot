import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Bot
from telegram.constants import ParseMode

app = FastAPI()
bot_token = os.getenv("BOT_TOKEN")
channel_id = os.getenv("CHANNEL_ID")
bot = Bot(token=bot_token)

tracked_wallets = {}

@app.on_event("startup")
async def startup_event():
    await send_message(channel_id, "👋 Willkommen beim RobertsSolTrackerBot!")

async def send_message(chat_id: str, text: str):
    await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "")

    # ignorieren, wenn keine Nachricht oder kein Text
    if not text.startswith("/"):
        return {"ok": True}

    # /start
    if text.startswith("/start"):
        await send_message(chat_id, """🤖 Verfügbare Befehle:
<code>/add WALLET TAG</code>
<code>/rm WALLET</code>
<code>/list</code>""")

    # /add WALLET TAG
    elif text.startswith("/add"):
        parts = text.split()
        if len(parts) == 3:
            wallet, tag = parts[1], parts[2]
            tracked_wallets[wallet] = tag
            await send_message(chat_id, f"✅ Wallet <code>{wallet}</code> mit Tag <b>{tag}</b> hinzugefügt.")
        else:
            await send_message(chat_id, "⚠️ Format: <code>/add WALLET TAG</code>")

    # /rm WALLET
    elif text.startswith("/rm"):
        parts = text.split()
        if len(parts) == 2:
            wallet = parts[1]
            if wallet in tracked_wallets:
                del tracked_wallets[wallet]
                await send_message(chat_id, f"🗑️ Wallet <code>{wallet}</code> entfernt.")
            else:
                await send_message(chat_id, f"❌ Wallet <code>{wallet}</code> nicht gefunden.")
        else:
            await send_message(chat_id, "⚠️ Format: <code>/rm WALLET</code>")

    # /list
    elif text.startswith("/list"):
        if tracked_wallets:
            message = "📋 <b>Liste der getrackten Wallets:</b>\n"
            for wallet, tag in tracked_wallets.items():
                message += f"• <code>{wallet}</code> – <i>{tag}</i>\n"
        else:
            message = "ℹ️ Keine Wallets getrackt."
        await send_message(chat_id, message)

    # Unbekannter Befehl
    else:
        await send_message(chat_id, "❌ Befehl existiert nicht. Tippe <code>/start</code> für Hilfe.")

    return {"ok": True}