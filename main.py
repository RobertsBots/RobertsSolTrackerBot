import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, Request
import uvicorn
import os

# Umgebungsvariablen laden
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Logging aktivieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot & Dispatcher initialisieren
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FastAPI App
app = FastAPI()


# ▶ Handler: Alle Nachrichten
@dp.message()
async def echo_message(message: Message):
    logger.info(f"Nachricht empfangen: {message.text}")
    await message.answer("✅ Webhook funktioniert!")

# ▶ Webhook Route
@app.post("/")
async def process_webhook(request: Request):
    update = await request.json()
    telegram_update = types.Update(**update)
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}


# ▶ Startup: Webhook setzen
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("Webhook gesetzt.")


# ▶ Shutdown
@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logger.info("Webhook gelöscht.")


# ▶ Lokaler Start (für Tests)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
