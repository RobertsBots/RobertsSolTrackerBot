import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()  # .env laden

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

application = ApplicationBuilder().token(BOT_TOKEN).build()


@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}


@app.get("/")
async def root():
    return {"message": "Bot läuft ✔"}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hallo! Ich bin bereit.")


def setup_handlers():
    application.add_handler(CommandHandler("start", start))


if __name__ == "__main__":
    import uvicorn

    setup_handlers()
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )