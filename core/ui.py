from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.start import handle_start
from core.add import handle_add_wallet
from core.remove import handle_remove_wallet
from core.list_wallets import handle_list_wallets
from core.profit import handle_profit_entry
from core.pnlsystem import get_wallet_statistics


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_wallet"),
            InlineKeyboardButton("📤 Wallet entfernen", callback_data="remove_wallet"),
        ],
        [
            InlineKeyboardButton("📋 Getrackte Wallets", callback_data="list_wallets"),
            InlineKeyboardButton("💰 Profit eintragen", callback_data="manual_profit"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Willkommen beim 📊 *Sol Wallet Tracker Bot*!\n\nWähle eine Aktion:", reply_markup=reply_markup, parse_mode="Markdown")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_wallet":
        await query.edit_message_text("Bitte sende mir eine Wallet-Adresse + optionalen Tag:\n\n`/add <WALLET> <TAG>`", parse_mode="Markdown")
    elif query.data == "remove_wallet":
        await query.edit_message_text("Bitte sende mir eine Wallet-Adresse, die du entfernen möchtest:\n\n`/rm <WALLET>`", parse_mode="Markdown")
    elif query.data == "list_wallets":
        await handle_list_wallets(update, context)
    elif query.data == "manual_profit":
        await query.edit_message_text("Profit manuell eintragen:\n\n`/profit <wallet> <+/-betrag>`", parse_mode="Markdown")
    else:
        await query.edit_message_text("Unbekannte Aktion.")
