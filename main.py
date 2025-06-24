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
    add_wallet_cmd,
    remove_wallet_cmd,
    list_wallets_cmd,
    profit_cmd_router,
    handle_profit_callback,
    handle_rm_callback,
    finder_menu_cmd,
    handle_finder_selection,
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

# Router-Registrierung (Commands)
dp.include_router(start_cmd)
dp.include_router(add_wallet_cmd)
dp.message.register(remove_wallet_cmd, F.text.startswith("/rm"))
dp.message.register(list_wallets_cmd, F.text == "/list")
dp.include_router(profit_cmd_router)
dp.message.register(finder_menu_cmd, F.text == "/finder")

# Callback-Registrierung
dp.callback_query.register(handle_profit_callback, F.data.startswith("profit:"))
dp.callback_query.register(handle_rm_callback, F.data.startswith("rm_"))
dp.callback_query.register(handle_finder_selection, F.data.in_({"moonbags", "scalping", "finder_off"}))

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
