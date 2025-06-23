from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 Getrackte Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("💸 Profit eintragen", callback_data="add_profit")],
        [InlineKeyboardButton("❌ Wallet entfernen", callback_data="remove_wallet")]
    ]
    await update.message.reply_text(
        "Willkommen beim 🛰 RobertsSolTrackerBot!

Was möchtest du tun?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

start_handler = CommandHandler("start", start)
