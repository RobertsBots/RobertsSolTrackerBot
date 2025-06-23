from telegram import Update
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
        await update.message.reply_text("❌ Ungültiger Betrag. Bitte nutze z. B. +1.2 oder -0.8")
        return

    wallet_result = supabase_client.table("wallets").select("*").eq("address", address).execute()
    if not wallet_result.data:
        await update.message.reply_text("❌ Wallet nicht gefunden.")
        return

    wallet = wallet_result.data[0]
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

    response = (
        f"💰 Neuer PnL für <code>{address}</code>:\n"
        f"<b>{updated_pnl:+.2f} sol</b> (WR: {wins}/{wins + losses})"
    )
    await update.message.reply_text(response, parse_mode="HTML")
