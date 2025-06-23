from telegram import Update
from telegram.ext import ContextTypes

from core.ui import send_message_with_buttons


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Willkommen beim RobertsSolTrackerBot!\n\n"
        "Nutze die folgenden Buttons, um Wallets zu verwalten oder deinen Profit einzutragen."
    )
    await send_message_with_buttons(update, context, welcome_text)
