# main.py

import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn

from core.commands import main_router  # Wichtig: Nur hier einbinden
from core.cron import setup_cron_jobs

DEBUG = os.getenv("DEBUG", "False") == "True"
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = f"https://{os.getenv('WEBHOOK_URL', 'localhost')}/{TOKEN}"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(bot=bot, fsm_strategy=FSMStrategy.CHAT)

# ✅ Nur einmal und genau hier einbinden
dp.include_router(main_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(dp, bot)
    logger.info("✅ Webhook gesetzt & Cron gestartet.")
    yield
    await bot.delete_webhook()
    logger.info("🔒 Webhook entfernt.")

app = FastAPI(lifespan=lifespan)

@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    try:
        data = await req.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.exception("❌ Fehler im Webhook:")
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
