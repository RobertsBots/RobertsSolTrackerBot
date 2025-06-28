# core/commands/rm_cmd.py

import logging
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.database import get_wallets, remove_wallet

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.startswith("/rm"))
async def remove_wallet_cmd(message: types.Message):
    wallets = get_wallets(message.from_user.id)
    if not wallets:
        await message.answer("❌ Keine Wallets gefunden.")
        return

    builder = InlineKeyboardBuilder()
    for entry in wallets:
        builder.button(
            text=f"{entry['tag']} - {entry['wallet'][:5]}...{entry['wallet'][-4:]}",
            callback_data=f"rm_{entry['wallet']}"
        )
    keyboard = builder.adjust(1).as_markup()
    await message.answer("🗑 Wähle eine Wallet zum Entfernen:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("rm_"))
async def handle_rm_callback(callback_query: types.CallbackQuery):
    wallet = callback_query.data.replace("rm_", "")
    remove_wallet(callback_query.from_user.id, wallet)
    await callback_query.message.edit_text(f"✅ Wallet `{wallet}` entfernt.", parse_mode="Markdown")
    logger.info(f"Wallet entfernt: {wallet} – User {callback_query.from_user.id}")
