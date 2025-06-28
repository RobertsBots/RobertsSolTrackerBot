# main.py

import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import setup_application
from aiogram.client.default import DefaultBotProperties

from core.commands import (
    start_router,
    add_router,
    rm_router,
    list_router,
    profit_router,
    finder_router,
)
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
WEBHOOK_URL = f"https://robertstracker-production.up.railway.app/{TOKEN}"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(bot=bot, fsm_strategy=FSMStrategy.CHAT)

# ------------------------------------------------
# Router Setup – aiogram 3.x clean
# ------------------------------------------------
dp.include_router(start_router)
dp.include_router(add_router)
dp.include_router(rm_router)
dp.include_router(list_router)
dp.include_router(profit_router)
dp.include_router(finder_router)

# ------------------------------------------------
# Webhook Lifecycle Events
# ------------------------------------------------
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(dp, bot)
    logger.info("✅ Webhook gesetzt & Cron gestartet.")

async def on_shutdown(app):
    await bot.delete_webhook()
    logger.info("🔒 Webhook entfernt.")

# ------------------------------------------------
# AIOHTTP Webserver Setup
# ------------------------------------------------
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Webhook-Handler
async def handle(request):
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    except Exception as e:
        logger.exception("❌ Fehler im Webhook-Handler:")
        return web.Response(status=500, text="Webhook Error")

# Telegram Webhook-Route
app.router.add_post(f"/{TOKEN}", handle)

# Dispatcher an AIOHTTP binden
setup_application(app, dp, bot=bot)
