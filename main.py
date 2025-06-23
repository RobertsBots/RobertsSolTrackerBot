import os
import logging
import asyncio
from fastapi import FastAPI, Request
import uvicorn
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

# === Logging Setup ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === ENV Variablen ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# === Telegram Application ===
defaults = Defaults(parse_mode="HTML")
application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

# === Handler Setup ===
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("add", handle_add_wallet))
application.add_handler(CommandHandler("rm", handle_remove_wallet))
application.add_handler(CommandHandler("list", handle_list_wallets))
application.add_handler(CommandHandler("profit", handle_profit_command))
application.add_handler(CallbackQueryHandler(handle_callback_query))

# === FastAPI App ===
app = FastAPI()

@app.post("/")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        logger.info("📩 Eingehende Telegram-Update: %s", data)

        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)

        return {"ok": True}
    except Exception as e:
        logger.error("❌ Fehler beim Verarbeiten des Webhooks: %s", str(e))
        return {"ok": False, "error": str(e)}

# === Bot Starten ===
async def main():
    logger.info("🚀 Bot wird initialisiert...")
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.start()
    logger.info("✅ Webhook gesetzt und Bot gestartet.")

if __name__ == "__main__":
    asyncio.run(main())
    uvicorn.run(app, host="0.0.0.0", port=8000)
