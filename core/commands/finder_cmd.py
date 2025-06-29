import logging
from aiogram import types, Bot
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_finder_mode, set_finder_mode
from core.alerts import notify_user

logger = logging.getLogger(__name__)

# /finder Befehl → öffnet Modusauswahl
async def finder_cmd(message: types.Message):
    Bot.set_current(message.bot)
    current_mode = await get_finder_mode(message.from_user.id)

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

# Callback-Handler für Auswahlbuttons
async def handle_finder_callback(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    mode = callback_query.data.split(":")[1]

    if mode == "moon":
        await set_finder_mode(callback_query.from_user.id, "moon")
        await callback_query.message.edit_text("🌕 *Moonbag-Modus aktiviert.*", parse_mode="Markdown")
        logger.info(f"Finder-Modus auf MOON gesetzt – User {callback_query.from_user.id}")
    elif mode == "scalp":
        await set_finder_mode(callback_query.from_user.id, "scalp")
        await callback_query.message.edit_text("⚡️ *Scalping-Modus aktiviert.*", parse_mode="Markdown")
        logger.info(f"Finder-Modus auf SCALP gesetzt – User {callback_query.from_user.id}")
    elif mode == "off":
        await set_finder_mode(callback_query.from_user.id, "off")
        await callback_query.message.edit_text("❌ *SmartFinder deaktiviert.*", parse_mode="Markdown")
        logger.info(f"Finder-Modus auf OFF gesetzt – User {callback_query.from_user.id}")
    else:
        await callback_query.answer("❗️Unbekannter Modus.", show_alert=True)
        return

    await notify_user(callback_query.from_user.id, f"✅ SmartFinder-Modus: `{mode}`")

# ✅ Dispatcher-Registrierung
def register_finder_cmd(dp: Dispatcher):
    dp.register_message_handler(finder_cmd, commands=["finder"])
    dp.register_callback_query_handler(handle_finder_callback, lambda c: c.data.startswith("finder:"))
