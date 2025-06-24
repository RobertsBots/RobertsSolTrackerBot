from aiogram import types
from core.database import get_wallets
from core.utils import format_pnl, calculate_winrate

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
        winrate = calculate_winrate(wins, losses)

        pnl_text = format_pnl(profit)
        winrate_text = f"`WR({wins}/{wins+losses})`" if (wins + losses) > 0 else "`WR(-)`"

        response += (
            f"🧠 *{tag}*\n"
            f"📟 `{wallet}`\n"
            f"{winrate_text} – {pnl_text}\n\n"
        )

    await message.answer(response, parse_mode="Markdown")
