from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Profit hinzugefügt.")

profit_handler = CommandHandler("profit", profit)
