from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 Wallets anzeigen", callback_data="list_wallets")],
        [InlineKeyboardButton("💰 Profit eintragen", callback_data="profit")],
        [InlineKeyboardButton("❌ Wallet entfernen", callback_data="remove_wallet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Willkommen beim 🧠 RobertsSolTrackerBot!\n\nWas möchtest du tun?",
        reply_markup=reply_markup,
    )

start_handler = CommandHandler("start", start)