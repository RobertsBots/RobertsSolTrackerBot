from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

@app.on_event("startup")
async def startup():
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("✅ Bot ist aktiv!")

    application.add_handler(CommandHandler("start", start))

    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    app.bot_app = application
    await application.initialize()
    await application.start()

@app.on_event("shutdown")
async def shutdown():
    await app.bot_app.stop()

@app.post("/webhook")
async def telegram_webhook(update: dict):
    telegram_update = Update.de_json(update, app.bot_app.bot)
    await app.bot_app.process_update(telegram_update)
    return "ok"