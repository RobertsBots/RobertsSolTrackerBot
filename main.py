import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes, MessageHandler, filters
)
from telegram.ext import CallbackContext

import logging

# Logging aktivieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token & Webhook URL aus Environment holen
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# FastAPI App
app = FastAPI()

# Telegram Bot-Anwendung
application = ApplicationBuilder().token(BOT_TOKEN).build()


# /start-Befehl
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot ist aktiv! /add, /rm usw. bald verfügbar.")


# Handler registrieren
application.add_handler(CommandHandler("start", start))


# Telegram Webhook Endpoint
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


# Startup: Webhook setzen
@app.on_event("startup")
async def startup():
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    logger.info("Webhook gesetzt ✅")


# Shutdown sauber beenden
@app.on_event("shutdown")
async def shutdown():
    await application.shutdown()