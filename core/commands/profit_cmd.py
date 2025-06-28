# core/commands/profit_cmd.py

import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import update_pnl

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("profit"))
async def profit_cmd(message: types.Message):
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            "❗️Falsche Nutzung von /profit\n\nBitte nutze:\n`/profit <WALLET> <+/-BETRAG>`",
            parse_mode="Markdown"
        )
        return

    wallet, raw_amount = args[1], args[2]

    try:
        amount = float(raw_amount)
    except ValueError:
        await message.answer("❗️Ungültiger Betrag. Beispiel: `/profit ABC...XYZ +1.5`", parse_mode="Markdown")
        return

    try:
        update_pnl(wallet, amount)
        color = "🟢" if amount > 0 else "🔴"
        await message.answer(
            f"{color} Profit für `{wallet}` aktualisiert: `{amount:+.2f} SOL`",
            parse_mode="Markdown"
        )
        logger.info(f"Profit gesetzt: {wallet} → {amount} – User {message.from_user.id}")
    except Exception as e:
        logger.error(f"Fehler beim Update von Profit: {e}")
        await message.answer("⚠️ Ein Fehler ist aufgetreten beim Setzen des Profits.")

@router.callback_query(F.data.startswith("profit:"))
async def handle_profit_callback(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "❗️Bitte sende den Profit-Wert manuell als Befehl im Format:\n`/profit <WALLET> <+/-BETRAG>`",
        parse_mode="Markdown"
    )
