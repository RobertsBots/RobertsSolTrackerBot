import logging
from aiogram import types, Dispatcher, Bot
from aiogram.utils.markdown import hbold
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
                InlineKeyboardButton(text="📈 track wallet", callback_data="add_wallet"),
                InlineKeyboardButton(text="❌ remove wallet", callback_data="remove_wallet")
            ],
            [
                InlineKeyboardButton(text="📊 list wallets", callback_data="list_wallets"),
                InlineKeyboardButton(text="💰 add profit", callback_data="add_profit")
            ],
            [
                InlineKeyboardButton(text="🛰 smartfinder", callback_data="smartfinder_menu")
            ]
        ])

        await message.answer(
            f"👋 hey {hbold(first_name)}!\n\n"
            "🚀 dieser bot ist dein persönlicher alpha-scanner für solana wallets.\n"
            "er trackt live alle käufe & verkäufe deiner favoriten – mit pnl, winrate & smartcoach analyse. \n\n"
            "📌 *hier ist dein command center:*\n\n"
            "• /add [wallet] [tag] – fügt eine wallet hinzu & beginnt das tracking ⏱\n"
            "• /rm – zeigt deine wallets zur entfernung 🗑️\n"
            "• /list – zeigt alle getrackten wallets inkl. pnl & winrate 📋\n"
            "• /profit [wallet] [+/-betrag] – trägt deinen realisierten profit ein 💰\n"
            "• /finder – aktiviert den smartfinder für automatische wallet-entdeckung 🛰️\n\n"
            "✨ oder nutze einfach die buttons unten:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.exception("❌ Fehler bei /start Befehl:")
        await message.answer("⚠️ ein fehler ist aufgetreten beim startbildschirm.")

# Registrierung für Dispatcher
def register_start_cmd(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=["start"])
