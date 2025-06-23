import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    Defaults
)
from fastapi import FastAPI, Request
from core.wallet_tracker import handle_add_wallet, handle_remove_wallet, handle_list_wallets
from core.pnlsystem import handle_profit_command, handle_profit_button
from core.ui import start_command, handle_callback_query
from core.database import supabase_client

# === Logging ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# === Bot Setup ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

defaults = Defaults(parse_mode="HTML")
application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

# === Command Handlers ===
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("add", handle_add_wallet))
application.add_handler(CommandHandler("rm", handle_remove_wallet))
application.add_handler(CommandHandler("list", handle_list_wallets))
application.add_handler(CommandHandler("profit", handle_profit_command))

# === Callback Handler ===
application.add_handler(CallbackQueryHandler(handle_callback_query))

# === FastAPI Webhook Setup ===
app = FastAPI()

@app.on_event("startup")
async def startup():
    logging.info("Starting bot via webhook...")
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.start()
    logging.info("Webhook set and bot running.")

@app.post("/")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# === Local Uvicorn Startup (used by Railway) ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)