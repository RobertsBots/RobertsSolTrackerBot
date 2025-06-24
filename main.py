import os
import logging
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import setup_application
from core.commands import (
    start_cmd,
    list_cmd,
    rm_cmd,
    handle_rm_callback,
    add_router,
    profit_router
)
from core.cron import setup_cron_jobs

# Logging
logging.basicConfig(level=logging.INFO)

# Bot Setup
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot=bot, fsm_strategy=FSMStrategy.CHAT)

# FastAPI App
app = FastAPI()

# Webhook Endpoint
@app.post("/")
async def webhook_handler(update: dict):
    await dp.feed_update(bot=bot, update=Update(**update))
    return {"status": "ok"}

# Router Setup
dp.include_router(add_router)
dp.include_router(profit_router)

# Message Commands
dp.message.register(start_cmd, F.text == "/start")
dp.message.register(list_cmd, F.text == "/list")
dp.message.register(rm_cmd, F.text.startswith("/rm"))

# Callback Queries
dp.callback_query.register(handle_rm_callback, F.data.startswith("rm_"))

# Startup / Shutdown
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(dp, bot)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

# Webhook Setup (Railway Deployment)
setup_application(app, dp, bot=bot)
