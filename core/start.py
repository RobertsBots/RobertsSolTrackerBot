from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from core.ui import send_message_with_buttons


async def handle_start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📄 Getrackte Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("💸 Profit eintragen", callback_data="manual_profit")],
        [InlineKeyboardButton("🗑️ Wallet entfernen", callback_data="remove_wallet")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        "👋 Willkommen beim RobertsSolTrackerBot!\n\n"
        "Mit diesem Bot kannst du 📈 Wallets tracken, 🔔 Käufe/Verkäufe monitoren und deinen 💰 PnL analysieren.\n\n"
        "Wähle eine Aktion:"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def handle_callback_start(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Callback-Auswertung und Weiterleitung an echte Commands
    callback_map = {
        "add_wallet": "/add",
        "list_wallets": "/list",
        "manual_profit": "/profit",
        "remove_wallet": "/rm"
    }

    command = callback_map.get(query.data)
    if command:
        fake_message = update.effective_user.id
        await context.bot.send_message(chat_id=fake_message, text=command)
