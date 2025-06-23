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
import uvicorn

from core.database import supabase_client
from core.ui import start_command, handle_callback_query
from core.wallet_tracker import handle_add_wallet, handle_remove_wallet, handle_list_wallets
from core.pnlsystem import handle_profit_command, handle_profit_button

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === ENV Variablen ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# === Telegram Application ===
defaults = Defaults(parse_mode="HTML")
application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

# === Handler Registrierung ===
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("add", handle_add_wallet))
application.add_handler(CommandHandler("rm", handle_remove_wallet))
application.add_handler(CommandHandler("list", handle_list_wallets))
application.add_handler(CommandHandler("profit", handle_profit_command))
application.add_handler(CallbackQueryHandler(handle_callback_query))

# === FastAPI Setup ===
app = FastAPI()

@app.post("/")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
    except Exception as e:
        logging.error(f"❌ Fehler im Webhook: {e}")
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    logging.info("🔄 Bot wird initialisiert...")
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.start()
    logging.info("✅ Webhook gesetzt und Bot gestartet.")

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("🛑 Shutdown gestartet...")
    await application.stop()
    await application.shutdown()
    logging.info("🚫 Bot sauber gestoppt.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
