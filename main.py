from fastapi import FastAPI
from telegram.ext import Application
from modules.wallet_tracker import wallet_commands
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

application = Application.builder().token(TOKEN).build()
wallet_commands(application)  # Lade Wallet-Befehle

@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    print("✅ Bot gestartet und Webhook gesetzt.")

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()