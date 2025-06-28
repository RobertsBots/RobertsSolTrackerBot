# core/commands/finder_cmd.py

from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from core.database import set_finder_mode
from core.alerts import notify_user

router = Router()

@router.message(F.text == "/finder")
async def finder_menu_cmd(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🌕 Moonbags", callback_data="moonbags"),
            types.InlineKeyboardButton(text="⚡️ Scalping Bags", callback_data="scalpbags")
        ],
        [
            types.InlineKeyboardButton(text="🛑 Deaktivieren", callback_data="finder_off")
        ]
    ])
    await message.answer("📡 <b>Smart Wallet Finder</b>\nWähle deinen Modus:", reply_markup=keyboard)

@router.callback_query(F.data.in_({"moonbags", "scalpbags", "finder_off"}))
async def handle_finder_selection(query: CallbackQuery):
    user_id = query.from_user.id
    selection = query.data

    if selection == "finder_off":
        await set_finder_mode(user_id, "off")
        await query.message.edit_text("🛑 Smart Finder deaktiviert.")
    elif selection == "moonbags":
        await set_finder_mode(user_id, "moonbags")
        await query.message.edit_text("✅ Finder aktiviert: 🌕 Moonbags")
    elif selection == "scalpbags":
        await set_finder_mode(user_id, "scalpbags")
        await query.message.edit_text("✅ Finder aktiviert: ⚡️ Scalping Bags")

    await notify_user(user_id, f"🎯 Finder-Modus gesetzt: <b>{selection}</b>")
