import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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
# Bot Setup
# ------------------------------------------------
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(bot=bot, fsm_strategy=FSMStrategy.CHAT)

# ------------------------------------------------
# Router Setup (ZENTRAL!)
# ------------------------------------------------
dp.include_router(main_router)

# ------------------------------------------------
# FastAPI + Webhook + Lifespan
# ------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    webhook_url = get_webhook_url()
    await bot.set_webhook(url=webhook_url)
    setup_cron_jobs(dp, bot)
    logger.info("✅ Webhook gesetzt & Cron gestartet.")
    yield
    await bot.delete_webhook()
    logger.info("🔒 Webhook entfernt.")

app = FastAPI(lifespan=lifespan)

# ------------------------------------------------
# CORS Middleware (optional)
# ------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------
# Telegram Webhook Endpoint (STABIL!)
# ------------------------------------------------
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        json_data = await request.json()
        logger.debug(f"📨 Raw Telegram JSON: {json_data}")
        update = Update(**json_data)  # Sicherste Variante für aiogram 3.x
        logger.info("📥 Telegram-Update empfangen.")
        await dp.feed_update(bot=bot, update=update)
        return {"status": "ok"}
    except Exception as e:
        logger.exception("❌ Fehler im Webhook:")
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

# ------------------------------------------------
# Healthcheck Endpoints für Railway & Telegram
# ------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}
