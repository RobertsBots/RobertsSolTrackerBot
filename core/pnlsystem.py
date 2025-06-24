from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.database import update_pnl, add_win, add_loss, list_wallets

async def handle_profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Format: /profit <wallet> <+betrag oder -betrag>"
        )
        return

    wallet = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Betrag muss eine gültige Zahl sein, z. B. +1.23 oder -0.5")
        return

    success = update_pnl(wallet, amount)
    if not success:
        await update.message.reply_text("❌ Wallet nicht gefunden.")
        return

    if amount > 0:
        add_win(wallet)
    elif amount < 0:
        add_loss(wallet)

    await update.message.reply_text(f"💰 PnL für <b>{wallet}</b> aktualisiert: {amount:+.2f} SOL")

async def handle_profit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    wallets = list_wallets()
    if not wallets:
        await query.edit_message_text("📭 Keine Wallets vorhanden.")
        return

    buttons = []
    for wallet in wallets:
        address = wallet["address"]
        buttons.append([
            InlineKeyboardButton(f"{wallet['tag']} ➕", callback_data=f"profit_add:{address}"),
            InlineKeyboardButton(f"{wallet['tag']} ➖", callback_data=f"profit_sub:{address}")
        ])

    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text("Wähle Wallet für manuelle PnL-Anpassung:", reply_markup=reply_markup)
