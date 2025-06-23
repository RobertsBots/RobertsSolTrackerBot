from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from core.database import supabase_client

async def handle_profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Nutzung: /profit <wallet> <+/-betrag>")
        return

    address = context.args[0]
    raw_amount = context.args[1]

    try:
        amount = float(raw_amount)
    except ValueError:
        await update.message.reply_text("❌ Ungültiger Betrag.")
        return

    result = supabase_client.table("wallets").select("*").eq("address", address).execute()
    if not result.data:
        await update.message.reply_text("❌ Wallet nicht gefunden.")
        return

    wallet = result.data[0]
    updated_pnl = wallet.get("pnl", 0) + amount
    wins = wallet.get("wins", 0)
    losses = wallet.get("losses", 0)

    if amount > 0:
        wins += 1
    elif amount < 0:
        losses += 1

    supabase_client.table("wallets").update({
        "pnl": updated_pnl,
        "wins": wins,
        "losses": losses
    }).eq("address", address).execute()

    await update.message.reply_text(
        f"💰 Neuer PnL für Wallet `{address}`: {updated_pnl:+.2f} sol\n"
        f"WR: {wins}/{wins + losses}",
        parse_mode="Markdown"
    )

async def handle_profit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Profit Button wurde gedrückt. (Demo-Funktion)")
