from aiogram import types
from database import list_wallets
from utils import format_pnl, calculate_winrate

async def list_cmd(message: types.Message):
    wallets = list_wallets()
    if not wallets:
        await message.answer("📭 Keine Wallets vorhanden.")
        return

    response = "📋 *Getrackte Wallets:*\n\n"
    for w in wallets:
        wallet = w["wallet"]
        tag = w.get("tag", "🏷️ Kein Tag")
        profit = w.get("profit", 0.0)
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
