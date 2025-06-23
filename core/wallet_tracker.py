import os
from telegram import Update
from telegram.ext import ContextTypes
from core.database import supabase_client

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
    exists = supabase_client.table("wallets").select("*").eq("address", address).execute()

    if exists.data:
        await update.message.reply_text("⚠️ Diese Wallet wird bereits getrackt.")
        return

    supabase_client.table("wallets").insert({
        "address": address,
        "tag": tag,
        "pnl": 0,
        "wins": 0,
        "losses": 0
    }).execute()

    await update.message.reply_text(f"✅ Wallet {address} wurde mit Tag '{tag}' hinzugefügt.")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=f"""
📥 <b>Neue Wallet getrackt:</b>
<code>{address}</code>
<b>Tag:</b> {tag}
""", parse_mode="HTML")


async def handle_remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Nutzung: /rm <WALLET>")
        return

    address = context.args[0]
    supabase_client.table("wallets").delete().eq("address", address).execute()
    await update.message.reply_text(f"🗑️ Wallet {address} wurde entfernt.")


async def handle_list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase_client.table("wallets").select("*").execute()
    if not result.data:
        await update.message.reply_text("ℹ️ Es werden derzeit keine Wallets getrackt.")
        return

    response = "<b>📊 Getrackte Wallets:</b>\n\n"
    for wallet in result.data:
        response += format_wallet_output(wallet) + "\n"

    await update.message.reply_text(response.strip(), parse_mode="HTML")
