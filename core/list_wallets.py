from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hier ist die Liste der Wallets.")

list_handler = CommandHandler("list", list_wallets)
