from aiogram import types
from aiogram.dispatcher import Dispatcher
from core.database import get_user_start_message_id, save_user_start_message_id
from core.buttons import start_buttons

async def start_cmd(message: types.Message):
    user_id = message.from_user.id

    # Vorherige Startnachricht löschen (falls vorhanden)
    old_msg_id = await get_user_start_message_id(user_id)
    if old_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_msg_id)
        except Exception:
            pass

    text = (
        "👋 <b>Willkommen Ro bei deinem persönlichen Solana-Tracker-Bot</b> – der Bot, der deine Krypto-Zukunft verändern könnte.\n\n"
        "Ich bin <b>Robert</b> – und glaub mir: Ich hab klein angefangen. Zwischen all den verwirrenden Infos, schrottigen Tools "
        "und Krypto-Gurus mit Kursen im A...berland musste ich einfach etwas Eigenes bauen. Etwas, das wirklich hilft.\n\n"
        "Nach vielen Nächten mit <b>Python</b> & ein bisschen <b>KI-Zauber</b> ist dieser Bot entstanden – für mich, aber jetzt auch für dich.\n\n"
        "Mit diesem Tool bekommst du <b>Live-Tracking</b>, <b>PnL</b>, <b>Winrate</b>, <b>SmartCoach-Analysen</b> und jede Menge Insider-Power.\n\n"
        "<b>Premium-Modus?</b> Ja, den gibt's auch – für alle, die noch mehr wollen: Developer-Zugriff, exklusive Features, Beta-Zugänge & kleine Extra-Goodies.\n\n"
        "🔥 <b>Aktuell bist du mit der Free-Version unterwegs</b> – und selbst die hat mehr drauf als 99 % aller Bots da draußen.\n\n"
        "<b>Features & Commands:</b>\n"
        "• <code>/add WALLET TAG</code> | ➕ Fügt eine Wallet hinzu & startet das Live-Tracking\n"
        "• <code>/rm</code> | ➖ Entfernt eine Wallet aus deiner Tracking-Liste\n"
        "• <code>/list</code> | 📃 Zeigt alle getrackten Wallets mit PnL & Winrate\n"
        "• <code>/profit WALLET +10</code> | 📈 Trägt deinen Gewinn/Verlust ein (z. B. +10 oder -7)\n"
        "• <code>/finder</code> | 🔍 SmartFinder-Modus – entdecke smarte Wallets zum Tracken & Coachen\n"
        "• <code>/start</code> | 🕹️ Öffnet dieses Menü erneut bei Bedarf\n\n"
        "✨ Oder nutze einfach die Buttons unten:"
    )

    msg = await message.answer(text, parse_mode="HTML", reply_markup=start_buttons())
    await save_user_start_message_id(user_id, msg.message_id)

# 🧩 Richtig benennen für __init__.py
def register_start_cmd(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=["start"])
