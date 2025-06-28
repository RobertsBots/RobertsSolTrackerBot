import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import setup_application
from aiogram.client.default import DefaultBotProperties

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
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(bot=bot, fsm_strategy=FSMStrategy.CHAT)

# Include Routers
dp.include_router(start_cmd)
dp.include_router(add_wallet_cmd)
dp.include_router(profit_cmd_router)

# Register Message Commands
dp.message.register(remove_wallet_cmd, F.text.startswith("/rm"))
dp.message.register(list_wallets_cmd, F.text == "/list")
dp.message.register(finder_menu_cmd, F.text == "/finder")

# Register Callback Queries
dp.callback_query.register(handle_profit_callback, F.data.startswith("profit:"))
dp.callback_query.register(handle_rm_callback, F.data.startswith("rm_"))
dp.callback_query.register(handle_finder_selection, F.data.in_({"moonbags", "scalpbags", "finder_off"}))

# aiohttp Webserver Setup
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(dp, bot)

async def on_shutdown(app):
    await bot.delete_webhook()

async def handle_webhook(request):
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return web.json_response({"status": "ok"})

# App Setup
app = web.Application()
app.router.add_post("/", handle_webhook)

# Webhook Setup
setup_application(app, dp, bot=bot, on_startup=on_startup, on_shutdown=on_shutdown)
