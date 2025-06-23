from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.buttons import get_main_buttons


async def send_message_with_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    keyboard = get_main_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "show_wallets":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="📄 Liste der getrackten Wallets folgt...")
        # Hier könnte z. B. ein Import aus list_wallets ausgelagert werden
    elif query.data == "add_wallet":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✏️ Sende mir die Wallet-Adresse im Format:\n\n<code>/add WALLET TAG</code>", parse_mode="HTML")
    elif query.data == "remove_wallet":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="🗑 Gib die Wallet-Adresse an, die du entfernen möchtest:\n\n<code>/rm WALLET</code>", parse_mode="HTML")
    elif query.data == "manual_profit":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="💰 Gib den Profit im Format ein:\n\n<code>/profit WALLET +5.3</code> oder <code>/profit WALLET -1.2</code>", parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❓ Unbekannte Aktion.")
