from telegram.ext import Application
from core.start import start_handler
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

application = Application.builder().token(TOKEN).build()
application.add_handler(start_handler)

application.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
    webhook_url=WEBHOOK_URL,
)