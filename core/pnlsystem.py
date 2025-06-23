
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def handle_profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Nutzung: /profit <wallet>")
        return
    address = context.args[0]

    keyboard = [
        [
            InlineKeyboardButton("+0.1", callback_data=f"profit|{address}|0.1"),
            InlineKeyboardButton("+0.5", callback_data=f"profit|{address}|0.5"),
            InlineKeyboardButton("+1.0", callback_data=f"profit|{address}|1.0"),
        ],
        [
            InlineKeyboardButton("-0.1", callback_data=f"profit|{address}|-0.1"),
            InlineKeyboardButton("-0.5", callback_data=f"profit|{address}|-0.5"),
            InlineKeyboardButton("-1.0", callback_data=f"profit|{address}|-1.0"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📉 Wähle Betrag für Wallet: <code>{address}</code>",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def handle_profit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, address, amount_str = query.data.split("|")
        amount = float(amount_str)
    except Exception:
        await query.edit_message_text("❌ Ungültige Eingabe.")
        return

    wallet_result = supabase.table("wallets").select("*").eq("address", address).execute()
    if not wallet_result.data:
        await query.edit_message_text("❌ Wallet nicht gefunden.")
        return

    wallet = wallet_result.data[0]
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
        f"💰 Neuer PnL für Wallet {address}: {updated_pnl:+.2f} sol (WR: {wins}/{wins + losses})"
    )
