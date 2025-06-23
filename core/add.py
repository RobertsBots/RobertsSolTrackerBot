from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Wallet hinzugefügt.")

add_handler = CommandHandler("add", add)
