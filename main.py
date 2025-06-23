import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    Defaults
)
from core.database import supabase_client
from core.ui import start_command, handle_callback_query
from core.wallet_tracker import handle_add_wallet, handle_remove_wallet, handle_list_wallets
from core.pnlsystem import handle_profit_command, handle_profit_button

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === ENV Variablen ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# === FastAPI ===
app = FastAPI()

# === Telegram Bot Setup ===
defaults = Defaults(parse_mode="HTML")
application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

# === Handler Setup ===
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("add", handle_add_wallet))
application.add_handler(CommandHandler("rm", handle_remove_wallet))
application.add_handler(CommandHandler("list", handle_list_wallets))
application.add_handler(CommandHandler("profit", handle_profit_command))
application.add_handler(CallbackQueryHandler(handle_callback_query))

# === Webhook Endpoint ===
@app.post("/")
async def process_update(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error("❌ Fehler beim Verarbeiten des Telegram-Updates: %s", str(e))
        return {"ok": False, "error": str(e)}

# === Startup Hook ===
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Bot wird gestartet und Webhook wird gesetzt...")
    await application.initialize()
    await application.bot.set_webhook(url=WEBHOOK_URL)
    logger.info("✅ Webhook gesetzt.")
