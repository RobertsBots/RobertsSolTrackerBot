
import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import defaults

from core.start import start_handler
from core.add import add_handler
from core.remove import remove_handler
from core.list_wallets import list_handler
from core.profit import profit_handler

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()
defaults = defaults.Defaults(parse_mode="HTML")

application = Application.builder().token(TOKEN).defaults(defaults).build()

application.add_handler(start_handler)
application.add_handler(add_handler)
application.add_handler(remove_handler)
application.add_handler(list_handler)
application.add_handler(profit_handler)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        webhook_url=WEBHOOK_URL
    )
