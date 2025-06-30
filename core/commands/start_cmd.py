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
        "👋 *Willkommen Ro bei deinem persönlichen Solana\\-Tracker\\-Bot* – der Bot, der deine Krypto\\-Zukunft verändern könnte\\.\n\n"
        "Ich bin *Robert* – und glaub mir: Ich hab klein angefangen\\. Zwischen all den verwirrenden Infos, schrottigen Tools "
        "und Krypto\\-Gurus mit Kursen im A\\.\\.\\.berland musste ich einfach etwas Eigenes bauen\\. Etwas, das wirklich hilft\\.\n\n"
        "Nach vielen Nächten mit *Python* & ein bisschen *KI\\-Zauber* ist dieser Bot entstanden – für mich, aber jetzt auch für dich\\.\n\n"
        "Mit diesem Tool bekommst du *Live\\-Tracking*, *PnL*, *Winrate*, *SmartCoach\\-Analysen* und jede Menge Insider\\-Power\\.\n\n"
        "*Premium\\-Modus?* Ja, den gibt's auch – für alle, die noch mehr wollen: Developer\\-Zugriff, exklusive Features, Beta\\-Zugänge & kleine Extra\\-Goodies\\.\n\n"
        "🔥 *Aktuell bist du mit der Free\\-Version unterwegs* – und selbst die hat mehr drauf als 99 \\% aller Bots da draußen\\.\n\n"
        "*Features & Commands:*\n"
        "• `/add WALLET TAG` | ➕ Fügt eine Wallet hinzu & startet das Live\\-Tracking\n"
        "• `/rm` | ➖ Entfernt eine Wallet aus deiner Tracking\\-Liste\n"
        "• `/list` | 📃 Zeigt alle getrackten Wallets mit PnL & Winrate\n"
        "• `/profit WALLET +10` | 📈 Trägt deinen Gewinn/Verlust ein \\(z\\. B\\. +10 oder \\-7\\)\n"
        "• `/finder` | 🔍 SmartFinder\\-Modus – entdecke smarte Wallets zum Tracken & Coachen\n"
        "• `/start` | 🕹️ Öffnet dieses Menü erneut bei Bedarf\n\n"
        "✨ Oder nutze einfach die Buttons unten:"
    )

    msg = await message.answer(text, parse_mode="HTML", reply_markup=start_buttons())
    await save_user_start_message_id(user_id, msg.message_id)

# 🧩 Richtig benennen für __init__.py
def register_start_cmd(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=["start"])
