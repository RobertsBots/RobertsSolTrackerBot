from core.database import update_pnl, add_win, add_loss
from telegram import Update
from telegram.ext import ContextTypes
import re

def parse_profit_input(text: str):
    """Hilfsfunktion, um + / - Profit aus Text zu extrahieren"""
    match = re.match(r"^/profit\s+([a-zA-Z0-9]+)\s+([+-]?\d+\.?\d*)", text)
    if match:
        address = match.group(1)
        amount = float(match.group(2))
        return address, amount
    return None, None

async def handle_profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verarbeitet den Befehl /profit <WALLET> <+/-BETRAG>"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("⚠️ Nutzung: /profit <wallet> <+/-betrag> (z. B. /profit ABC123 +50.0)")
        return

    address = context.args[0]
    profit_raw = context.args[1]

    if not profit_raw.startswith(('+', '-')):
        await update.message.reply_text("❌ Bitte gib ein `+` oder `-` vor dem Betrag an. Beispiel: `/profit WALLET +25.0`")
        return

    try:
        amount = float(profit_raw)
    except ValueError:
        await update.message.reply_text("❌ Ungültiger Betrag.")
        return

    result = update_pnl(address, amount)
    if not result:
        await update.message.reply_text("❌ Wallet nicht gefunden.")
        return

    if amount > 0:
        add_win(address)
        emoji = "✅"
    else:
        add_loss(address)
        emoji = "🔻"

    await update.message.reply_text(f"{emoji} PnL für `{address}` wurde um {amount:+.2f} $ angepasst.", parse_mode="Markdown")
