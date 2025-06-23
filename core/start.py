from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Getrackte Wallets", callback_data='list_wallets')],
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data='add_wallet')],
        [InlineKeyboardButton("➖ Wallet entfernen", callback_data='remove_wallet')],
        [InlineKeyboardButton("💰 Profit manuell eintragen", callback_data='add_profit')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Willkommen beim 🛰️ RobertsSolTrackerBot!", reply_markup=reply_markup)

def get_start_handler():
    return CommandHandler("start", start_handler)