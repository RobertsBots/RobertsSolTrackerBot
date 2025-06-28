import logging
from aiogram import types
from core.database import get_wallets
from core.utils import format_pnl, colorize_winrate

logger = logging.getLogger(__name__)

async def list_wallets_cmd(message: types.Message):
    wallets = get_wallets(message.from_user.id)
    if not wallets:
        await message.answer("📭 Keine Wallets vorhanden.")
        return

    response = "📋 *Getrackte Wallets:*\n\n"
    for w in wallets:
        wallet = w["wallet"]
        tag = w.get("tag", "🏷️ Kein Tag")
        profit = w.get("pnl", 0.0)
        wins = w.get("wins", 0)
        losses = w.get("losses", 0)

        pnl_text = format_pnl(profit)
        winrate_text = colorize_winrate(wins, losses)

        response += (
            f"🧠 *{tag}*\n"
            f"📟 `{wallet}`\n"
            f"{winrate_text} – {pnl_text}\n\n"
        )

    await message.answer(response, parse_mode="Markdown")
    logger.info(f"Wallet-Übersicht gesendet – User {message.from_user.id}")
