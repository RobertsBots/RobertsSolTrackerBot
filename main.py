import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from fastapi import FastAPI
from telegram.ext.webhook import configure_app

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Beispiel: https://your-railway-app.up.railway.app

# Logging
logging.basicConfig(level=logging.INFO)

# FastAPI App
app = FastAPI()

# Telegram Application
application = Application.builder().token(TOKEN).build()

@app.on_event("startup")
async def startup():
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.initialize()
    await application.start()

@app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.shutdown()

@app.get("/")
async def root():
    return {"status": "ok"}

@application.command_handler("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot ist aktiv!")

# Webhook mit FastAPI verbinden
configure_app(app, application)
