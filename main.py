import os
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Willkommen beim RobertsSolTrackerBot!")

@app.on_event("startup")
async def startup():
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )
    application.add_handler(CommandHandler("start", start_command))
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

@app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.shutdown()