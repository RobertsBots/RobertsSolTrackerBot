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
        first_name = message.from_user.first_name if message.from_user else "Freund"

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
            f"👋 Willkommen {hbold(first_name)} bei deinem persönlichen Solana-Tracker-Bot – der Bot, der deine Krypto-Zukunft verändern könnte.\n\n"
            f"Ich bin {hbold('Robert')} – und glaub mir: Ich hab klein angefangen. Zwischen all den verwirrenden Infos, schrottigen Tools und Krypto-Gurus mit Kursen im A...berland musste ich einfach etwas Eigenes bauen. Etwas, das wirklich hilft.\n\n"
            f"Nach vielen Nächten mit {hbold('Python')} & ein bisschen {hbold('KI-Zauber')} ist dieser Bot entstanden – für mich, aber jetzt auch für dich.\n\n"
            f"Mit diesem Tool bekommst du {hbold('Live-Tracking, PnL, Winrate, SmartCoach-Analysen')} und jede Menge Insider-Power.\n\n"
            f"{hbold('Premium-Modus?')} Ja, den gibt's auch – für alle, die noch mehr wollen: Developer-Zugriff, exklusive Features, Beta-Zugänge & kleine Extra-Goodies.\n\n"
            f"🔥 Aktuell bist du mit der {hbold('Free-Version')} unterwegs – und selbst die hat mehr drauf als 99 % aller Bots da draußen.\n\n"
            f"{hbold('Features & Commands:')}\n"
            f"- /add WALLET TAG | ➕ {hbold('Fügt eine Wallet hinzu')} & startet das Live-Tracking\n"
            f"- /rm | ➖ {hbold('Entfernt eine Wallet')} aus deiner Tracking-Liste\n"
            f"- /list | 📃 {hbold('Zeigt alle getrackten Wallets')} mit PnL & Winrate\n"
            f"- /profit WALLET +10 | 📈 {hbold('Trägt deinen Gewinn/Verlust ein')} (z. B. +10 oder -7)\n"
            f"- /finder | 🔍 {hbold('SmartFinder-Modus')} – entdecke smarte Wallets zum Tracken & Coachen\n"
            f"- /start | 🕹️ {hbold('Öffnet dieses Menü erneut')} bei Bedarf\n\n"
            f"✨ Oder nutze einfach die Buttons unten:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.exception("❌ Fehler bei /start Befehl:")
        await message.answer("⚠️ Ein Fehler ist beim Öffnen des Startmenüs aufgetreten.")

# Registrierung für Dispatcher
def register_start_cmd(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=["start"])
