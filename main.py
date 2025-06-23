from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

@app.on_event("startup")
async def startup():
    application = ApplicationBuilder().token(TOKEN).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("✅ /start Befehl erkannt")
        if update.message:
            await update.message.reply_text("Der Bot ist online!")

    application.add_handler(CommandHandler("start", start))

    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    app.bot_app = application
    await application.initialize()
    await application.start()

@app.on_event("shutdown")
async def shutdown():
    await app.bot_app.stop()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("📨 Webhook Update erhalten:", data)  # Das zeigt uns, ob irgendwas ankommt
    update = Update.de_json(data, app.bot_app.bot)
    await app.bot_app.process_update(update)
    return "ok"