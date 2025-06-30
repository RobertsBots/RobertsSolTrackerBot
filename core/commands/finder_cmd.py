import logging
from aiogram import types, Bot
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_finder_mode, set_finder_mode
from core.alerts import notify_user

logger = logging.getLogger(__name__)

# /finder Befehl → öffnet Modusauswahl
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
            f"🔍 *SmartFinder aktivieren*\n\nAktueller Modus: `{current_mode}`\n\n"
            "Wähle aus, welcher Modus aktiviert werden soll 👇",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.exception("❌ Fehler bei /finder:")
        await message.answer("❌ Beim Öffnen des Finder-Menüs ist ein Fehler aufgetreten.")

# Callback-Handler für Auswahlbuttons
async def handle_finder_callback(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)

        if not callback_query.data or ":" not in callback_query.data:
            await callback_query.answer("❗️ Ungültige Auswahl.", show_alert=True)
            return

        user_id = callback_query.from_user.id if callback_query.from_user else None
        if not user_id:
            await callback_query.answer("❌ Benutzer-ID fehlt.", show_alert=True)
            return

        mode = callback_query.data.split(":")[1]

        if mode == "moon":
            await set_finder_mode(user_id, "moon")
            await callback_query.message.edit_text("🌕 *Moonbag-Modus aktiviert.*", parse_mode="Markdown")
        elif mode == "scalp":
            await set_finder_mode(user_id, "scalp")
            await callback_query.message.edit_text("⚡️ *Scalping-Modus aktiviert.*", parse_mode="Markdown")
        elif mode == "off":
            await set_finder_mode(user_id, "off")
            await callback_query.message.edit_text("❌ *SmartFinder deaktiviert.*", parse_mode="Markdown")
        else:
            await callback_query.answer("❗️Unbekannter Modus.", show_alert=True)
            return

        await notify_user(user_id, f"✅ SmartFinder-Modus: `{mode}`")
        logger.info(f"Finder-Modus gesetzt auf {mode.upper()} – User {user_id}")

    except Exception as e:
        logger.exception("❌ Fehler bei Finder-Callback:")
        await callback_query.answer("❌ Fehler bei der Modusauswahl.", show_alert=True)

# ✅ Dispatcher-Registrierung
def register_finder_cmd(dp: Dispatcher):
    dp.register_message_handler(finder_cmd, commands=["finder"])
    dp.register_callback_query_handler(handle_finder_callback, lambda c: c.data and c.data.startswith("finder:"))
    
