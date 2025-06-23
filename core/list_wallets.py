from telegram import Update
from telegram.ext import ContextTypes
from core.database import supabase_client


def format_wallet_output(wallet):
    pnl = wallet.get("pnl", 0)
    wins = wallet.get("wins", 0)
    losses = wallet.get("losses", 0)

    pnl_color = "green" if pnl >= 0 else "red"
    pnl_text = f"<b>PnL:</b> <span style='color:{pnl_color}'>{pnl:+.2f} sol</span>"

    total = wins + losses
    wr_text = f"<b>WR:</b> {wins}/{total if total > 0 else 0}"

    return f"""
<b>Wallet:</b> <code>{wallet['address']}</code>
<b>Tag:</b> {wallet['tag']}
{wr_text} | {pnl_text}
""".strip()


async def handle_list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = supabase_client.table("wallets").select("*").execute()
    if not result.data:
        await update.message.reply_text("ℹ️ Es werden derzeit keine Wallets getrackt.")
        return

    response = "<b>📊 Getrackte Wallets:</b>\n\n"
    for wallet in result.data:
        response += format_wallet_output(wallet) + "\n\n"

    await update.message.reply_text(response.strip(), parse_mode="HTML")
