import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from core.commands import main_router  # WICHTIG: Nur hier einbinden
from core.cron import setup_cron_jobs

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
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not WEBHOOK_URL:
    logger.error("❌ WEBHOOK_URL ist nicht gesetzt. Bitte in Railway als vollständige HTTPS-URL eintragen.")
    raise RuntimeError("WEBHOOK_URL is not set.")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(bot=bot, fsm_strategy=FSMStrategy.CHAT)

# ------------------------------------------------
# Router Setup (NUR HIER!)
# ------------------------------------------------
dp.include_router(main_router)

# ------------------------------------------------
# FastAPI + Webhook + Lifespan
# ------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(dp, bot)
    logger.info("✅ Webhook gesetzt & Cron gestartet.")
    yield
    await bot.delete_webhook()
    logger.info("🔒 Webhook entfernt.")

app = FastAPI(lifespan=lifespan)

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

# CORS Middleware (nur zur Sicherheit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/webhook")
async def telegram_webhook(req: Request):
    try:
        content_type = req.headers.get("content-type", "")
        if "application/json" not in content_type:
            logger.warning(f"⚠️ Unerwarteter Content-Type: {content_type}")
            return JSONResponse(status_code=400, content={"error": "Invalid Content-Type"})

        raw = await req.body()
        logger.warning(f"📦 RAW BODY:\n{raw.decode(errors='ignore')}")

        try:
            data = await req.json()
        except Exception as json_err:
            logger.exception("❌ JSON Decode Error:")
            return {"status": "error", "detail": str(json_err)}

        try:
            update = Update(**data)
        except Exception as parse_err:
            logger.exception(f"❌ Fehler beim Parsen:\n{data}")
            return {"status": "error", "detail": f"Parsing error: {str(parse_err)}"}

        await dp.feed_update(bot, update)
        logger.info("✅ Update verarbeitet")
        return {"status": "ok"}

    except RequestValidationError as ve:
        logger.exception("❌ FastAPI RequestValidationError:")
        return JSONResponse(status_code=422, content={"detail": str(ve)})
    except Exception as e:
        logger.exception("🔥 Unbekannter Webhook-Fehler:")
        return JSONResponse(status_code=500, content={"error": str(e)})
