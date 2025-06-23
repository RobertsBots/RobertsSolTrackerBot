import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Railway Static URL hier setzen
PORT = int(os.getenv("PORT", "8080"))
CHANNEL_ID = os.getenv("CHANNEL_ID")