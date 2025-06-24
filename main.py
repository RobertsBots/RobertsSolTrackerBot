import os
import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.strategy import FSMStrategy
from aiogram.webhook.aiohttp_server import setup_application
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import Update
from core.commands import (
    start_cmd,
    add_wallet_cmd,
    remove_wallet_cmd,
    list_wallets_cmd,
    profit_cmd,
    handle_profit_callback,
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

@app.post("/")
async def webhook_handler(update: dict):
    await dp.feed_update(bot=bot, update=Update(**update))
    return {"status": "ok"}

# Commands
dp.message.register(start_cmd, F.text == "/start")
dp.message.register(add_wallet_cmd, F.text.startswith("/add"))
dp.message.register(remove_wallet_cmd, F.text.startswith("/rm"))
dp.message.register(list_wallets_cmd, F.text == "/list")
dp.message.register(profit_cmd, F.text.startswith("/profit"))
dp.message.register(finder_menu_cmd, F.text == "/finder")

# Callback Queries
dp.callback_query.register(handle_profit_callback, F.data.startswith("profit:"))
dp.callback_query.register(handle_finder_selection, F.data.in_({"moonbags", "scalping", "finder_off"}))

# Startup
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(dp, bot)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

# Webhook Setup for Railway
setup_application(app, dp, bot=bot)
