# main.py

import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import Update
from aiogram.client.default import DefaultBotProperties

from fastapi import FastAPI, Request
import uvicorn

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
# Router Setup
# ------------------------------------------------
dp.include_router(start_cmd)
dp.include_router(add_wallet_cmd)
dp.include_router(profit_cmd_router)

# ------------------------------------------------
# Message Commands
# ------------------------------------------------
dp.message.register(remove_wallet_cmd, F.text.startswith("/rm"))
dp.message.register(list_wallets_cmd, F.text == "/list")
dp.message.register(finder_menu_cmd, F.text == "/finder")

# ------------------------------------------------
# Callback Queries
# ------------------------------------------------
dp.callback_query.register(handle_profit_callback, F.data.startswith("profit:"))
dp.callback_query.register(handle_rm_callback, F.data.startswith("rm_"))
dp.callback_query.register(
    handle_finder_selection,
    F.data.in_({"moonbags", "scalpbags", "finder_off"})
)

# ------------------------------------------------
# FastAPI Webhook Setup
# ------------------------------------------------
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    setup_cron_jobs(dp, bot)
    logger.info("✅ Webhook gesetzt & Cron gestartet.")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logger.info("🔒 Webhook entfernt.")

@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    try:
        data = await req.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.exception("❌ Fehler im Webhook:")
        return {"status": "error", "detail": str(e)}

# ------------------------------------------------
# App Runner
# ------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
