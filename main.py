import os
import json
import time
import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler
import httpx

app = FastAPI()
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
bot = Bot(token=TELEGRAM_TOKEN)

wallets = {}

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    await application.update_queue.put(update)
    return JSONResponse(content={"ok": True})

async def send_message(text):
    await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=ParseMode.HTML)

async def check_wallets_loop():
    while True:
        for wallet, tag in wallets.items():
            await send_message(f"🧾 Wallet: <code>{wallet}</code> — {tag}")
            # Beispiel für echte API-Abfragen oder Logs
        await asyncio.sleep(60)

async def add_wallet(update: Update, context):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Nutzung: /add <wallet> <tag>")
        return
    wallet, tag = context.args[0], " ".join(context.args[1:])
    wallets[wallet] = tag
    await update.message.reply_text(f"✅ Wallet hinzugefügt: <code>{wallet}</code> — {tag}", parse_mode=ParseMode.HTML)

async def remove_wallet(update: Update, context):
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Nutzung: /rm <wallet>")
        return
    wallet = context.args[0]
    if wallet in wallets:
        del wallets[wallet]
        await update.message.reply_text(f"🗑️ Wallet entfernt: <code>{wallet}</code>", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ Wallet nicht gefunden.")

async def list_wallets(update: Update, context):
    if not wallets:
        await update.message.reply_text("📭 Keine Wallets eingetragen.")
        return
    text = "📋 <b>Getrackte Wallets</b>
"
    for w, t in wallets.items():
        text += f"🔹 <code>{w}</code> — {t}
"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", remove_wallet))
application.add_handler(CommandHandler("list", list_wallets))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(application.initialize())
    asyncio.create_task(application.start())
    asyncio.create_task(check_wallets_loop())

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()