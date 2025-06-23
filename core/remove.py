from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Wallet entfernt.")

remove_handler = CommandHandler("rm", remove)
