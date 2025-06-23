import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def build_profit_keyboard(address):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("+1.0", callback_data=f"{address}|+1.0"),
         InlineKeyboardButton("-1.0", callback_data=f"{address}|-1.0")],
        [InlineKeyboardButton("+0.5", callback_data=f"{address}|+0.5"),
         InlineKeyboardButton("-0.5", callback_data=f"{address}|-0.5")],
        [InlineKeyboardButton("+0.1", callback_data=f"{address}|+0.1"),
         InlineKeyboardButton("-0.1", callback_data=f"{address}|-0.1")]
    ])

async def handle_profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Nutzung: /profit <wallet>")
        return
    address = context.args[0]
    wallet = supabase.table("wallets").select("*").eq("address", address).execute().data
    if not wallet:
        await update.message.reply_text("❌ Wallet nicht gefunden.")
        return
    await update.message.reply_text(
        f"📈 Wähle Betrag für Wallet:
<code>{address}</code>",
        reply_markup=build_profit_keyboard(address),
        parse_mode="HTML"
    )

async def handle_profit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    address, raw_amount = query.data.split("|")
    amount = float(raw_amount)
    result = supabase.table("wallets").select("*").eq("address", address).execute().data
    if not result:
        await query.edit_message_text("❌ Wallet nicht gefunden.")
        return

    wallet = result[0]
    updated_pnl = wallet.get("pnl", 0) + amount
    wins = wallet.get("wins", 0)
    losses = wallet.get("losses", 0)

    if amount > 0:
        wins += 1
    elif amount < 0:
        losses += 1

    supabase.table("wallets").update({
        "pnl": updated_pnl,
        "wins": wins,
        "losses": losses
    }).eq("address", address).execute()

    await query.edit_message_text(
        f"💰 Neuer PnL für <code>{address}</code>: {updated_pnl:+.2f} sol
WR: {wins}/{wins + losses}",
        parse_mode="HTML"
    )
