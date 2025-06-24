from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.database import get_wallets, remove_wallet

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

async def handle_rm_callback(callback_query: types.CallbackQuery):
    wallet = callback_query.data.replace("rm_", "")
    remove_wallet(callback_query.from_user.id, wallet)
    await callback_query.message.edit_text(f"✅ Wallet `{wallet}` entfernt.", parse_mode="Markdown")
