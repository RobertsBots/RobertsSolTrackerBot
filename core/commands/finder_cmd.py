import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from core.buttons import get_smart_finder_menu, get_main_menu
from core.database import set_finder_mode
from core.alerts import notify_user

logger = logging.getLogger(__name__)

async def finder_cmd(message: types.Message):
    await message.answer(
        "📡 <b>Smart Wallet Finder</b>\nWähle deinen Modus:",
        reply_markup=get_smart_finder_menu(),
        parse_mode="HTML"
    )

async def finder_callback_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.replace("finder_", "")
    await callback_query.answer()

    if data == "moonbags":
        await set_finder_mode(user_id, "moonbags")
        await callback_query.message.edit_text("✅ Finder aktiviert: 🌕 Moonbags", reply_markup=get_main_menu())
    elif data == "scalping":
        await set_finder_mode(user_id, "scalping")
        await callback_query.message.edit_text("✅ Finder aktiviert: ⚡️ Scalping Bags", reply_markup=get_main_menu())
    elif data == "off":
        await set_finder_mode(user_id, "off")
        await callback_query.message.edit_text("🛑 Finder deaktiviert.", reply_markup=get_main_menu())

    await notify_user(user_id, f"🎯 Finder-Modus gesetzt: <b>{data}</b>")

def register_finder_cmd(dp: Dispatcher):
    dp.register_message_handler(finder_cmd, commands=["finder"])
    dp.register_callback_query_handler(finder_callback_handler, lambda c: c.data.startswith("finder_"))
