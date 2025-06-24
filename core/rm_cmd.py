from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core.database import list_wallets

async def rm_cmd(message: Message):
    wallets = list_wallets()
    if not wallets:
        await message.reply("🧾 Keine Wallets gefunden.")
        return

    keyboard = []
    for wallet in wallets:
        address = wallet["address"]
        button = InlineKeyboardButton(
            text=f"❌ {address[:6]}...{address[-4:]}",
            callback_data=f"remove_wallet:{address}"
        )
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.reply("🔻 Wähle eine Wallet zum Entfernen:", reply_markup=reply_markup)
