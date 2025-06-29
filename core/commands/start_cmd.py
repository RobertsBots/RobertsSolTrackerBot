import logging
from aiogram import types, Dispatcher, Bot
from aiogram.utils.markdown import hbold
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# Handler-Funktion für /start
async def start_cmd(message: types.Message):
    Bot.set_current(message.bot)  # 🛠️ Fix für Kontextfehler
    logger.info(f"📩 /start empfangen von: {message.from_user.id} – {message.from_user.username}")

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
            InlineKeyboardButton(text="🛰️ SmartFinder", callback_data="smartfinder_menu")
        ]
    ])

    await message.answer(
        f"Willkommen, {hbold(message.from_user.first_name)}! 👋\n\n"
        "Dieser Bot trackt automatisch Solana-Wallets und benachrichtigt dich über alle Käufe/Verkäufe.\n\n"
        "Verfügbare Befehle:\n"
        "/add [WALLET] [TAG] – Wallet hinzufügen\n"
        "/rm – Wallet entfernen\n"
        "/list – Alle Wallets anzeigen\n"
        "/profit [WALLET] [+/-BETRAG] – Manuellen Profit setzen\n"
        "/finder – SmartFinder Modus\n\n"
        "Oder benutze die Buttons 👇",
        reply_markup=keyboard,
        parse_mode="HTML"  # ✅ wichtig für hbold()
    )

# Registrierung für Dispatcher
def register_start_cmd(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=["start"])
