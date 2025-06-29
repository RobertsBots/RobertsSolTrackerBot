# main.py

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook

from core.commands import main_router
from core.cron import setup_cron_jobs
from core.utils import get_webhook_url

# ------------------------------------------------
# Logging Setup
# ------------------------------------------------
DEBUG = os.getenv("DEBUG", "False") == "True"
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------------------------------
# Telegram Bot Setup
# ------------------------------------------------
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ------------------------------------------------
# Router Setup
# ------------------------------------------------
main_router(dp)  # Alle Handler registrieren (Funktion aus __init__.py)

# ------------------------------------------------
# FastAPI Setup
# ------------------------------------------------
app = FastAPI()

# CORS Middleware (optional für Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        body = await request.body()
        update = types.Update.de_json(body.decode("utf-8"))
        await dp.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.exception("❌ Fehler beim Verarbeiten des Updates:")
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

@app.get("/")
@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}

# ------------------------------------------------
# Webhook-Startup-Funktionen
# ------------------------------------------------
WEBHOOK_URL = get_webhook_url()
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

async def on_startup(dp: Dispatcher):
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(dp, bot)
    logger.info("✅ Webhook gesetzt & Cronjobs gestartet.")

async def on_shutdown(dp: Dispatcher):
    await bot.delete_webhook()
    logger.info("🔒 Webhook entfernt.")

# ------------------------------------------------
# Render Start
# ------------------------------------------------
if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path="",
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        webhook_url=WEBHOOK_URL,
    )
