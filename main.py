import os
from fastapi import FastAPI
from telegram.ext import Application, CommandHandler
import logging

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
telegram_app = Application.builder().token(BOT_TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Willkommen beim RobertsSolTrackerBot!")

telegram_app.add_handler(CommandHandler("start", start))

@app.on_event("startup")
async def on_startup():
    logger.info("Bot wird gestartet...")
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    await telegram_app.updater.start_webhook()

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Bot wird gestoppt...")
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()
