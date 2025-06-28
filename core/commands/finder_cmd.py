import logging
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from core.database import set_finder_mode
from core.alerts import notify_user

logger = logging.getLogger(__name__)

class FinderCallback(CallbackData, prefix="finder"):
    action: str

async def finder_menu_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌕 Moonbags", callback_data=FinderCallback(action="moonbags").pack()),
            InlineKeyboardButton(text="⚡️ Scalping Bags", callback_data=FinderCallback(action="scalpbags").pack())
        ],
        [
            InlineKeyboardButton(text="❌ Deaktivieren", callback_data=FinderCallback(action="finder_off").pack())
        ]
    ])
    await message.answer(
        "🔎 *Wähle deinen Smart Wallet Finder Modus:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def handle_finder_selection(callback: CallbackQuery, callback_data: FinderCallback):
    mode = callback_data.action
    user_id = callback.from_user.id

    if mode == "moonbags":
        set_finder_mode(user_id, "moonbags")
        await callback.message.edit_text("🌕 Modus *Moonbags* aktiviert.", parse_mode="Markdown")
        logger.info(f"Finder-Modus: Moonbags – User {user_id}")
    elif mode == "scalpbags":
        set_finder_mode(user_id, "scalpbags")
        await callback.message.edit_text("⚡️ Modus *Scalping Bags* aktiviert.", parse_mode="Markdown")
        logger.info(f"Finder-Modus: Scalping – User {user_id}")
    elif mode == "finder_off":
        set_finder_mode(user_id, "off")
        await callback.message.edit_text("🔕 Smart Wallet Finder wurde *deaktiviert*.", parse_mode="Markdown")
        logger.info(f"Finder-Modus: OFF – User {user_id}")
    else:
        await notify_user(user_id, "❌ Unbekannte Auswahl – bitte erneut versuchen.")
        logger.warning(f"Unbekannter Finder-Modus: {mode} – User {user_id}")

    await callback.answer()
