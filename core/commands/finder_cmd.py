import logging
from aiogram import types, Dispatcher, Bot
from core.database import set_finder_mode
from core.alerts import notify_user

logger = logging.getLogger(__name__)

# /finder Menü
async def finder_menu_cmd(message: types.Message):
    Bot.set_current(message.bot)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🌕 Moonbags", callback_data="moonbags"),
            types.InlineKeyboardButton(text="⚡️ Scalping Bags", callback_data="scalpbags")
        ],
        [
            types.InlineKeyboardButton(text="🛑 Deaktivieren", callback_data="finder_off")
        ]
    ])
    await message.answer("📡 <b>Smart Wallet Finder</b>\nWähle deinen Modus:", reply_markup=keyboard, parse_mode="HTML")

# Auswahl behandeln
async def handle_finder_selection(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    user_id = callback_query.from_user.id
    selection = callback_query.data

    if selection == "finder_off":
        await set_finder_mode(user_id, "off")
        await callback_query.message.edit_text("🛑 Smart Finder deaktiviert.")
    elif selection == "moonbags":
        await set_finder_mode(user_id, "moonbags")
        await callback_query.message.edit_text("✅ Finder aktiviert: 🌕 Moonbags")
    elif selection == "scalpbags":
        await set_finder_mode(user_id, "scalpbags")
        await callback_query.message.edit_text("✅ Finder aktiviert: ⚡️ Scalping Bags")

    await notify_user(user_id, f"🎯 Finder-Modus gesetzt: <b>{selection}</b>")

# Registrierung
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(finder_menu_cmd, commands=["finder"])
    dp.register_callback_query_handler(
        handle_finder_selection,
        lambda c: c.data in {"moonbags", "scalpbags", "finder_off"}
    )
