import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import telegram

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # z. B. https://deinprojekt.up.railway.app/webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
telegram_bot_app = None  # Wird beim Startup gesetzt


# Telegram-Befehl /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Der Bot ist jetzt aktiv und bereit zum Tracken!")


@app.on_event("startup")
async def on_startup():
    global telegram_bot_app
    telegram_bot_app = Application.builder().token(BOT_TOKEN).build()

    telegram_bot_app.add_handler(CommandHandler("start", start))

    # Starte den Bot im Webhook-Modus (nur lokal – FastAPI übernimmt Anfragen)
    await telegram_bot_app.initialize()
    await telegram_bot_app.bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    await telegram_bot_app.start()
    logger.info("🚀 Bot gestartet und Webhook gesetzt.")


@app.on_event("shutdown")
async def on_shutdown():
    await telegram_bot_app.stop()
    await telegram_bot_app.shutdown()
    logger.info("🛑 Bot gestoppt.")


@app.post(WEBHOOK_PATH)
async def handle_webhook(request: Request):
    raw_data = await request.body()
    update = telegram.Update.de_json(data=raw_data.decode("utf-8"), bot=telegram_bot_app.bot)
    await telegram_bot_app.update_queue.put(update)
    return {"ok": True}