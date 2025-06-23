import os
from fastapi import FastAPI
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext.webhook import WebhookServer

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hallo! Der Bot ist aktiv.")

application.add_handler(CommandHandler("start", start))

@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()

@app.get("/")
def root():
    return {"status": "ok"}
