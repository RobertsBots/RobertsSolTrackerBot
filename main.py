import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from core.commands import (
    start_cmd,
    add_wallet_cmd,
    remove_wallet_cmd,
    list_wallets_cmd,
    profit_cmd_router,
    finder_cmd,
)

load_dotenv()

# Telegram Token & Webhook URL
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot & Dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# Command Routing
dp.message.register(start_cmd, F.text == "/start")
dp.message.register(add_wallet_cmd, F.text.startswith("/add"))
dp.message.register(remove_wallet_cmd, F.text.startswith("/rm"))
dp.message.register(list_wallets_cmd, F.text == "/list")

# Profit- & Finder-Router registrieren
dp.include_router(profit_cmd_router)
dp.include_router(finder_cmd)

# FastAPI-App
app = FastAPI()

# CORS (optional, aber empfohlen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # Webhook setzen
    webhook_url = WEBHOOK_URL
    if webhook_url:
        await bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook gesetzt: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL ist nicht gesetzt!")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logger.info("Webhook gelöscht")

@app.post("/")
async def telegram_webhook(update: dict):
    telegram_update = Update(**update)
    await dp.feed_update(bot, telegram_update)

# Setup für aiogram in FastAPI
SimpleRequestHandler(dispatcher=dp, bot=bot)
setup_application(app, dp, bot=bot)
