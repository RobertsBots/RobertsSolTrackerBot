import logging
from aiogram import types, Dispatcher, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# Handler-Funktion für /start
async def start_cmd(message: types.Message):
    try:
        Bot.set_current(message.bot)

        user_id = message.from_user.id if message.from_user else "❓"
        username = message.from_user.username if message.from_user else "❓"
        first_name = message.from_user.first_name if message.from_user else "User"

        logger.info(f"📩 /start empfangen von: {user_id} – {username}")

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
                InlineKeyboardButton(text="🛰 SmartFinder", callback_data="smartfinder_menu")
            ]
        ])

        await message.answer(
            f"👋 Hey *{first_name}*!\n\n"
            "🚀 Dieser Bot ist dein persönlicher Alpha-Scanner für Solana Wallets.\n"
            "Er trackt live alle Käufe & Verkäufe deiner Favoriten – mit PnL, Winrate & SmartCoach Analyse.\n\n"
            "📌 *Hier ist dein Command Center:*\n\n"
            "• /add [wallet] [tag] – startet das Tracking für eine neue Wallet 🔍\n"
            "• /rm – zeigt deine getrackten Wallets zur Entfernung 🗑️\n"
            "• /list – Übersicht mit PnL, Winrate & SmartCoach Button 📋\n"
            "• /profit [wallet] [+/-betrag] – trägt manuell Profit oder Verlust ein 💰\n"
            "• /finder – aktiviert den SmartFinder für automatische Wallet-Entdeckung 🛰️\n"
            "• /start – zeigt dieses Menü nochmal an 🔁\n\n"
            "✨ Oder nutze einfach die Buttons unten:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.exception("❌ Fehler bei /start Befehl:")
        await message.answer("⚠️ Ein Fehler ist aufgetreten beim Startbildschirm.")

# Registrierung für Dispatcher
def register_start_cmd(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=["start"])
