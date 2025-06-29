import logging
from aiogram import types, Bot
from aiogram.dispatcher import Dispatcher
from core.database import update_pnl

logger = logging.getLogger(__name__)

# /profit <WALLET> <+/-BETRAG>
async def profit_cmd(message: types.Message):
    Bot.set_current(message.bot)
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
        await message.answer(
            "❗️Ungültiger Betrag. Beispiel: `/profit ABC...XYZ +1.5`",
            parse_mode="Markdown"
        )
        return

    try:
        await update_pnl(wallet, amount)
        color = "🟢" if amount > 0 else "🔴"
        await message.answer(
            f"{color} Profit für `{wallet}` aktualisiert: `{amount:+.2f} SOL`",
            parse_mode="Markdown"
        )
        logger.info(f"Profit gesetzt: {wallet} → {amount} – User {message.from_user.id}")
    except Exception as e:
        logger.error(f"Fehler beim Update von Profit: {e}")
        await message.answer("⚠️ Ein Fehler ist aufgetreten beim Setzen des Profits.")

# Callback-Handler für Buttons mit "profit:<wallet>"
async def handle_profit_callback(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.message.edit_text(
        "❗️Bitte sende den Profit-Wert manuell als Befehl im Format:\n`/profit <WALLET> <+/-BETRAG>`",
        parse_mode="Markdown"
    )

# Registrierung
def register_profit_cmd(dp: Dispatcher):
    dp.register_message_handler(profit_cmd, commands=["profit"])
    dp.register_callback_query_handler(handle_profit_callback, lambda c: c.data.startswith("profit:"))
