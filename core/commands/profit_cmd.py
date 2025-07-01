import logging
from aiogram import types, Bot
from aiogram.dispatcher import Dispatcher
from core.database import update_pnl

logger = logging.getLogger(__name__)

# /profit <WALLET> <+/-BETRAG>
async def profit_cmd(message: types.Message):
    try:
        Bot.set_current(message.bot)
        user_id = message.from_user.id if message.from_user else None

        if not user_id:
            await message.answer("❗️ Benutzer-ID fehlt.")
            return

        args = message.text.strip().split()

        if len(args) != 3:
            await message.answer(
                "❗️ Falsche Nutzung von <code>/profit</code>\n\n"
                "Bitte nutze:\n<code>/profit &lt;WALLET&gt; &lt;+/-BETRAG&gt;</code>",
                parse_mode="HTML"
            )
            return

        wallet, raw_amount = args[1], args[2]

        try:
            amount = float(raw_amount)
        except ValueError:
            await message.answer(
                "❗️ Ungültiger Betrag.\n\nBeispiel: <code>/profit ABC...XYZ +1.5</code>",
                parse_mode="HTML"
            )
            return

        await update_pnl(wallet, amount)
        color = "🟢" if amount > 0 else "🔴"
        await message.answer(
            f"{color} Profit für <code>{wallet}</code> aktualisiert: <b>{amount:+.2f} SOL</b>",
            parse_mode="HTML"
        )
        logger.info(f"✅ Profit gesetzt: {wallet} → {amount} – User {user_id}")

    except Exception as e:
        logger.exception("❌ Fehler bei /profit:")
        await message.answer("⚠️ Ein Fehler ist aufgetreten beim Setzen des Profits.")

# Callback-Handler z. B. von Inline-Button
async def handle_profit_callback(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.message.edit_text(
            "📥 Bitte sende den Profit-Befehl manuell im Format:\n\n"
            "<code>/profit &lt;WALLET&gt; &lt;+/-BETRAG&gt;</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.exception("❌ Fehler beim Bearbeiten von Profit-Callback:")
        await callback_query.answer("⚠️ Fehler beim Anzeigen der Profit-Eingabe.", show_alert=True)

# Registrierung
def register_profit_cmd(dp: Dispatcher):
    dp.register_message_handler(profit_cmd, commands=["profit"])
    dp.register_callback_query_handler(handle_profit_callback, lambda c: c.data and c.data.startswith("profit:"))
