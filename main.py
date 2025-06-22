import os
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from starlette.responses import JSONResponse

app = FastAPI()

bot_token = os.getenv("BOT_TOKEN")
channel_id = os.getenv("CHANNEL_ID")
bot = Bot(token=bot_token)

tracked_wallets = {}

async def send_message(chat_id: str, text: str, buttons=None):
    if buttons:
        reply_markup = InlineKeyboardMarkup(buttons)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

@app.on_event("startup")
async def startup_event():
    await send_message(channel_id, "👋 Willkommen beim RobertsSolTrackerBot!")

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "")

    if not text.startswith("/"):
        return JSONResponse({"ok": True})

    if text.startswith("/start"):
        buttons = [
            [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_help")],
            [InlineKeyboardButton("🗑️ Wallet entfernen", callback_data="rm_help")],
            [InlineKeyboardButton("📋 Wallet-Liste anzeigen", callback_data="list_wallets")]
        ]
        await send_message(chat_id, "🤖 Wähle einen Befehl:", buttons)

    elif text.startswith("/add"):
        parts = text.split()
        if len(parts) == 3:
            wallet, tag = parts[1], parts[2]
            if not wallet.startswith("4") or len(wallet) < 32:
                await send_message(chat_id, "⚠️ Ungültige Wallet-Adresse.")
            else:
                tracked_wallets[wallet] = tag
                await send_message(chat_id, f"✅ Wallet <b>{wallet}</b> mit Tag <b>{tag}</b> hinzugefügt.")
        else:
            await send_message(chat_id, "⚠️ Format: <code>/add WALLET TAG</code>")

    elif text.startswith("/rm"):
        parts = text.split()
        if len(parts) == 2:
            wallet = parts[1]
            if wallet in tracked_wallets:
                del tracked_wallets[wallet]
                await send_message(chat_id, f"🗑️ Wallet <b>{wallet}</b> entfernt.")
            else:
                await send_message(chat_id, f"❌ Wallet <b>{wallet}</b> nicht gefunden.")
        else:
            await send_message(chat_id, "⚠️ Format: <code>/rm WALLET</code>")

    elif text.startswith("/list"):
        if tracked_wallets:
            message = "📋 <b>Liste der getrackten Wallets:</b>\n\n"
            for i, (wallet, tag) in enumerate(tracked_wallets.items(), start=1):
                birdeye_link = f"https://birdeye.so/token/{wallet}?chain=solana"
                message += f"{i}. <a href=\"{birdeye_link}\">{wallet}</a> – <i>{tag}</i>\n"
        else:
            message = "ℹ️ Keine Wallets getrackt."
        await send_message(chat_id, message)

    else:
        await send_message(chat_id, "❓ Befehl nicht erkannt. Nutze <code>/start</code> um Hilfe zu bekommen.")

    return JSONResponse({"ok": True})

@app.post("/callback")
async def handle_callback(req: Request):
    data = await req.json()
    callback_query = data.get("callback_query", {})
    chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))
    data_value = callback_query.get("data")

    if data_value == "add_help":
        await send_message(chat_id, "➕ Um eine Wallet hinzuzufügen, nutze: <code>/add WALLET TAG</code>")
    elif data_value == "rm_help":
        await send_message(chat_id, "🗑️ Um eine Wallet zu entfernen, nutze: <code>/rm WALLET</code>")
    elif data_value == "list_wallets":
        if tracked_wallets:
            message = "📋 <b>Liste der getrackten Wallets:</b>\n\n"
            for i, (wallet, tag) in enumerate(tracked_wallets.items(), start=1):
                birdeye_link = f"https://birdeye.so/token/{wallet}?chain=solana"
                message += f"{i}. <a href=\"{birdeye_link}\">{wallet}</a> – <i>{tag}</i>\n"
        else:
            message = "ℹ️ Keine Wallets getrackt."
        await send_message(chat_id, message)

    return JSONResponse({"ok": True})

# OPTIONAL: Loop vorbereiten für zukünftiges Scanning:
# async def scan_loop():
#     while True:
#         for wallet, tag in tracked_wallets.items():
#             # simulate check:
#             await asyncio.sleep(1)
#         await asyncio.sleep(60)  # jede Minute erneut prüfen