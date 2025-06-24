from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import list_wallets, remove_wallet

async def rm_cmd(message: types.Message):
    wallets = list_wallets()
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
    remove_wallet(wallet)
    await callback_query.message.edit_text(f"✅ Wallet `{wallet}` entfernt.", parse_mode="Markdown")
