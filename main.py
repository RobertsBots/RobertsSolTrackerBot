import os
import json
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
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN Umgebungsvariable fehlt!")

bot: Bot = Bot(token=TOKEN, parse_mode="HTML")
Bot.set_current(bot)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ------------------------------------------------
# Router Setup
# ------------------------------------------------
main_router(dp)

# ------------------------------------------------
# FastAPI Setup
# ------------------------------------------------
app = FastAPI()

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
        update = types.Update(**json.loads(body.decode("utf-8")))
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
if not WEBHOOK_URL:
    logger.warning("⚠️ Keine WEBHOOK_URL gesetzt!")

@app.on_event("startup")
async def startup():
    try:
        setup_cron_jobs(bot)
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"✅ Webhook gesetzt auf: {WEBHOOK_URL}")
    except Exception as e:
        logger.exception("❌ Fehler beim Setzen des Webhooks oder Cron-Setup:")

@app.on_event("shutdown")
async def shutdown():
    try:
        await bot.delete_webhook()
        logger.info("🔒 Webhook entfernt.")
    except Exception as e:
        logger.exception("❌ Fehler beim Entfernen des Webhooks:")
