from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Der Bot ist online und bereit!")

wallet_handlers = [
    CommandHandler("start", start)
]
