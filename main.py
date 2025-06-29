import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

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
bot = Bot(token=TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ------------------------------------------------
# Router Setup
# ------------------------------------------------
main_router(dp)  # Alle Handler registrieren

# ------------------------------------------------
# FastAPI Setup
# ------------------------------------------------
app = FastAPI()

# CORS Middleware (z. B. für Render)
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
        logger.exception("❌ Fehler beim Verarbeiten des Telegram-Updates:")
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

@app.get("/")
@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}

# ------------------------------------------------
# Startup & Shutdown
# ------------------------------------------------
WEBHOOK_URL = get_webhook_url()

@app.on_event("startup")
async def startup():
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(bot)
    logger.info("✅ Webhook gesetzt & Cronjobs gestartet.")

@app.on_event("shutdown")
async def shutdown():
    await bot.delete_webhook()
    logger.info("🔒 Webhook entfernt.")
