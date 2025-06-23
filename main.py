import logging
import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)
from telegram.ext import ContextTypes
from dotenv import load_dotenv

# Core-Module
from core.handlers import (
    start_command,
    add_command,
    remove_command,
    list_command,
    profit_command,
    handle_callback_query,
)

# Umgebungsvariablen laden
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Logging konfigurieren
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# FastAPI-Anwendung
app = FastAPI()
telegram_app: Application = None  # Wird später initialisiert


@app.on_event("startup")
async def startup():
    global telegram_app
    telegram_app = Application.builder().token(BOT_TOKEN).build()

    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("add", add_command))
    telegram_app.add_handler(CommandHandler("rm", remove_command))
    telegram_app.add_handler(CommandHandler("list", list_command))
    telegram_app.add_handler(CommandHandler("profit", profit_command))
    telegram_app.add_handler(CallbackQueryHandler(handle_callback_query))

    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    logger.info("🚀 Bot initialisiert und Webhook gesetzt.")


@app.on_event("shutdown")
async def shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()
    logger.info("🛑 Bot wurde gestoppt.")


@app.post("/")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
