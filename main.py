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

# === Core-Importe ===
from core.database import supabase_client
from core.ui import start_command, handle_callback_query
from core.wallet_tracker import handle_add_wallet, handle_remove_wallet, handle_list_wallets
from core.pnlsystem import handle_profit_command, handle_profit_button
from core.smartfinder.menu import handle_finder_command, handle_finder_callback

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === ENV Variablen ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# === Application Setup ===
defaults = Defaults(parse_mode="HTML")
application = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

# === CommandHandler ===
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("add", handle_add_wallet))
application.add_handler(CommandHandler("rm", handle_remove_wallet))
application.add_handler(CommandHandler("list", handle_list_wallets))
application.add_handler(CommandHandler("profit", handle_profit_command))
application.add_handler(CommandHandler("finder", handle_finder_command))

# === CallbackQueryHandler ===
application.add_handler(CallbackQueryHandler(handle_callback_query))
application.add_handler(CallbackQueryHandler(handle_finder_callback))

# === FastAPI Webhook ===
app = FastAPI()

@app.post("/")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# === Bot Startup ===
async def main():
    logging.info("Bot initialisiert...")
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.start()
    logging.info("Bot läuft mit Webhook.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    uvicorn.run(app, host="0.0.0.0", port=8000)
