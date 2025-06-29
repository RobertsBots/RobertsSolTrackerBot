import logging
from aiogram import types, Dispatcher, Bot
from core.database import get_wallets, remove_wallet

logger = logging.getLogger(__name__)

# /rm Befehl – zeigt Wallets zur Auswahl an
async def remove_wallet_cmd(message: types.Message):
    Bot.set_current(message.bot)
    wallets = get_wallets(message.from_user.id)
    if not wallets:
        await message.answer("❌ Keine Wallets gefunden.")
        return

    keyboard = types.InlineKeyboardMarkup()
    for entry in wallets:
        display = f"{entry['tag']} - {entry['wallet'][:5]}...{entry['wallet'][-4:]}"
        callback_data = f"rm_{entry['wallet']}"
        keyboard.add(types.InlineKeyboardButton(text=display, callback_data=callback_data))

    await message.answer("🗑 Wähle eine Wallet zum Entfernen:", reply_markup=keyboard)

# Callback für Entfernen einer Wallet
async def handle_rm_callback(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    wallet = callback_query.data.replace("rm_", "")
    remove_wallet(callback_query.from_user.id, wallet)
    await callback_query.message.edit_text(
        f"✅ Wallet `{wallet}` entfernt.",
        parse_mode="Markdown"
    )
    logger.info(f"Wallet entfernt: {wallet} – User {callback_query.from_user.id}")

# Registrierung
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(remove_wallet_cmd, commands=["rm"])
    dp.register_callback_query_handler(handle_rm_callback, lambda c: c.data.startswith("rm_"))
