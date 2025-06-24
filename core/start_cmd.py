from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hbold

async def start_cmd(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Track Wallet", callback_data="add_wallet"),
            InlineKeyboardButton(text="❌ Remove Wallet", callback_data="remove_wallet")
        ],
        [
            InlineKeyboardButton(text="📊 List Wallets", callback_data="list_wallets"),
            InlineKeyboardButton(text="💰 Add Profit", callback_data="add_profit")
        ],
        [
            InlineKeyboardButton(text="🚀 SmartFinder", callback_data="toggle_finder")
        ]
    ])

    await message.answer(
        f"Willkommen, {hbold(message.from_user.first_name)}! 👋\n\n"
        "Dieser Bot trackt automatisch Solana-Wallets und benachrichtigt dich über alle Käufe/Verkäufe.\n\n"
        "Verfügbare Befehle:\n"
        "/add <WALLET> <TAG> – Wallet hinzufügen\n"
        "/rm <WALLET> – Wallet entfernen\n"
        "/list – Alle Wallets anzeigen\n"
        "/profit <WALLET> <+/-BETRAG> – Manuellen Profit setzen\n\n"
        "Oder benutze die Buttons 👇",
        reply_markup=keyboard
    )
