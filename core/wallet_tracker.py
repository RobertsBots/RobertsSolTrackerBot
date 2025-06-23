import os
from telegram import Update
from telegram.ext import ContextTypes
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CHANNEL_ID = os.getenv("CHANNEL_ID")

def format_wallet_output(wallet):
    pnl = wallet.get("pnl", 0)
    wins = wallet.get("wins", 0)
    losses = wallet.get("losses", 0)

    pnl_text = f"<b>PnL:</b> <span style='color: {'green' if pnl >= 0 else 'red'}'>{pnl:+.2f} sol</span>"
    wr_text = f"<b>WR:</b> {wins}/{wins + losses if (wins + losses) > 0 else 0}"

    return f"""
<b>Wallet:</b> <code>{wallet['address']}</code>
<b>Tag:</b> {wallet['tag']}
{wr_text} | {pnl_text}
"""

async def handle_add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Nutzung: /add <WALLET> <TAG>")
        return
    address, tag = context.args
    exists = supabase.table("wallets").select("*").eq("address", address).execute()
    if exists.data:
        await update.message.reply_text("⚠️ Diese Wallet wird bereits getrackt.")
        return
    supabase.table("wallets").insert({
        "address": address,
        "tag": tag,
        "pnl": 0,
        "wins": 0,
        "losses": 0
    }).execute()
    await update.message.reply_text(f"✅ Wallet {address} wurde mit Tag '{tag}' hinzugefügt.")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=f"📥 Neue Wallet getrackt:
<code>{address}</code>
Tag: {tag}")

async def handle_remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Nutzung: /rm <WALLET>")
        return
    address = context.args[0]
    supabase.table("wallets").delete().eq("address", address).execute()
    await update.message.reply_text(f"🗑️ Wallet {address} wurde entfernt.")

async def handle_list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase.table("wallets").select("*").execute()
    if not result.data:
        await update.message.reply_text("ℹ️ Es werden derzeit keine Wallets getrackt.")
        return
    response = "<b>📊 Getrackte Wallets:</b>

"
    for wallet in result.data:
        response += format_wallet_output(wallet) + "\n"
    await update.message.reply_text(response, parse_mode="HTML")

async def handle_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    wallet_result = supabase.table("wallets").select("*").eq("address", address).execute()
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

    supabase.table("wallets").update({
        "pnl": updated_pnl,
        "wins": wins,
        "losses": losses
    }).eq("address", address).execute()

    await update.message.reply_text(f"💰 Neuer PnL für Wallet {address}: {updated_pnl:+.2f} sol (WR: {wins}/{wins + losses})")
