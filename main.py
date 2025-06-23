import os
from telegram.ext import ApplicationBuilder
from core.start import start_handler
from core.add import add_handler
from core.remove import remove_handler
from core.list_wallets import list_handler
from core.profit import profit_handler
from core.handlers import callback_handler
from dotenv import load_dotenv
from fastapi import FastAPI
import asyncio

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(start_handler)
application.add_handler(add_handler)
application.add_handler(remove_handler)
application.add_handler(list_handler)
application.add_handler(profit_handler)
application.add_handler(callback_handler)

# FastAPI App für Webhook
app = FastAPI()

@app.post(f"/{BOT_TOKEN}")
async def webhook(update: dict):
    await application.update_queue.put(update)
    return {"status": "ok"}

async def run():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url=WEBHOOK_URL)
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        webhook_url=WEBHOOK_URL
    )

asyncio.run(run())
