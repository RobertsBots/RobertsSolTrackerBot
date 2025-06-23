from telegram import Update
from telegram.ext import ContextTypes
from core.database import supabase_client

async def handle_list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase_client.table("wallets").select("*").execute()
    
    if not result.data:
        await update.message.reply_text("ℹ️ Es werden derzeit keine Wallets getrackt.")
        return

    response = "<b>📊 Getrackte Wallets:</b>\n"

    for wallet in result.data:
        address = wallet.get("address")
        tag = wallet.get("tag")
        pnl = wallet.get("pnl", 0)
        wins = wallet.get("wins", 0)
        losses = wallet.get("losses", 0)
        total = wins + losses

        # Farben
        pnl_color = "green" if pnl >= 0 else "red"
        wr_color = "green" if wins >= losses else "red"

        pnl_text = f"<b>PnL:</b> <span style='color:{pnl_color}'>{pnl:+.2f} SOL</span>"
        wr_text = f"<b>WR:</b> <span style='color:{wr_color}'>{wins}/{total if total > 0 else 1}</span>"

        response += f"""
👛 <b>Wallet:</b> <code>{address}</code>
🏷 <b>Tag:</b> {tag}
{wr_text} | {pnl_text}
———————————————
"""

    await update.message.reply_text(response, parse_mode="HTML")
