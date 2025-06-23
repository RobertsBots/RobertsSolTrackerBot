from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📤 Wallet entfernen", callback_data="remove_wallet")],
        [InlineKeyboardButton("📃 Getrackte Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("💰 Profit / Loss eintragen", callback_data="profit_wallet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Willkommen! Wähle eine Aktion:", reply_markup=reply_markup)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "add_wallet":
        await query.edit_message_text("➕ Nutze den Befehl: /add <wallet> <tag>")
    elif data == "remove_wallet":
        await query.edit_message_text("🗑️ Nutze den Befehl: /rm <wallet>")
    elif data == "list_wallets":
        await query.edit_message_text("📃 Nutze den Befehl: /list")
    elif data == "profit_wallet":
        await query.edit_message_text("💰 Nutze den Befehl: /profit <wallet> <+/-betrag>")
    else:
        await query.edit_message_text("⚠️ Unbekannte Auswahl.")
