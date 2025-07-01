import logging
import asyncio
from aiogram import types, Bot
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_finder_mode, set_finder_mode
from core.alerts import notify_user
from core.smartfinder.run_smart_finder import run_smart_wallet_finder

logger = logging.getLogger(__name__)

async def finder_cmd(message: types.Message):
    try:
        Bot.set_current(message.bot)
        user_id = message.from_user.id if message.from_user else None

        if not user_id:
            await message.answer("❌ Benutzer-ID konnte nicht ermittelt werden.")
            return

        current_mode = await get_finder_mode(user_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("🌕 Moonbags", callback_data="finder:moon"),
                InlineKeyboardButton("⚡️ Scalping Bags", callback_data="finder:scalp")
            ],
            [
                InlineKeyboardButton("❌ Deaktivieren", callback_data="finder:off")
            ]
        ])

        await message.answer(
            f"<b>🔍 SmartFinder aktivieren</b>\n\n"
            "Mit dem SmartFinder entdeckt dein Bot automatisch 🔥 Wallets mit hoher Winrate & solidem ROI – alle 30 Minuten.\n\n"
            f"<b>Aktueller Modus:</b> <code>{current_mode}</code>\n\n"
            "<b>🧠 Wähle deinen Scan-Modus:</b>\n"
            "• 🌕 <b>Moonbags</b> → fokussiert auf starke Wallets mit längerem Hold & hohem Gewinnpotential\n"
            "• ⚡️ <b>Scalping Bags</b> → erkennt schnelle Trader mit hohen Intraday-Moves\n\n"
            "Du kannst den Finder jederzeit deaktivieren.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.exception("❌ Fehler bei /finder:")
        await message.answer("❌ Beim Öffnen des Finder-Menüs ist ein Fehler aufgetreten.")


async def handle_finder_callback(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)

        await callback_query.answer()

        if not callback_query.data or ":" not in callback_query.data:
            await callback_query.answer("❗️ Ungültige Auswahl.", show_alert=True)
            return

        user_id = callback_query.from_user.id if callback_query.from_user else None
        if not user_id:
            await callback_query.answer("❌ Benutzer-ID fehlt.", show_alert=True)
            return

        mode = callback_query.data.split(":")[1]

        await set_finder_mode(user_id, mode)

        # Scan direkt starten, außer bei "off"
        if mode != "off":
            # Nebenläufig starten, um UI nicht zu blockieren
            asyncio.create_task(run_smart_wallet_finder(callback_query.bot))

        if mode == "moon":
            await callback_query.message.edit_text(
                "🌕 <b>Moonbag-Modus aktiviert!</b>\n\n"
                "Der SmartFinder wird jetzt automatisch Wallets posten, die langfristige Gewinne & hohe Winrates zeigen.",
                parse_mode="HTML"
            )
        elif mode == "scalp":
            await callback_query.message.edit_text(
                "⚡️ <b>Scalping-Modus aktiviert!</b>\n\n"
                "Jetzt scannt der Bot nach schnellen Wallets mit explosiven Trades & scalptauglichem ROI.",
                parse_mode="HTML"
            )
        elif mode == "off":
            await callback_query.message.edit_text(
                "❌ <b>SmartFinder deaktiviert.</b>\n\n"
                "Es werden keine neuen Wallets mehr automatisch erkannt oder gepostet.",
                parse_mode="HTML"
            )
        else:
            await callback_query.answer("❗️Unbekannter Modus.", show_alert=True)
            return

        # Optional: User benachrichtigen
        # await notify_user(user_id, f"✅ SmartFinder-Modus: <code>{mode}</code>")

        logger.info(f"Finder-Modus gesetzt auf {mode.upper()} – User {user_id}")

    except Exception as e:
        logger.exception("❌ Fehler bei Finder-Callback:")
        try:
            await callback_query.answer("❌ Fehler bei der Modusauswahl.", show_alert=True)
        except Exception:
            pass


def register_finder_cmd(dp: Dispatcher):
    dp.register_message_handler(finder_cmd, commands=["finder"])
    dp.register_callback_query_handler(handle_finder_callback, lambda c: c.data and c.data.startswith("finder:"))
