from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Command

from core.buttons import get_main_keyboard
from core.database import get_user_start_message_id, save_user_start_message_id
from core import dp


@dp.message_handler(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    try:
        # Alte Startnachricht löschen (falls vorhanden)
        old_msg_id = await get_user_start_message_id(user_id)
        if old_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=old_msg_id)
            except Exception:
                pass

        # Neue Startnachricht
        text = (
            f"👋 Willkommen <b>Ro</b> bei deinem persönlichen <b>Solana-Tracker-Bot</b> – der Bot, der deine Krypto-Zukunft verändern könnte.\n\n"
            f"Ich bin <b>Robert</b> – und glaub mir: Ich hab klein angefangen. Zwischen all den verwirrenden Infos, "
            f"schrottigen Tools und Krypto-Gurus mit Kursen im A...berland musste ich einfach etwas Eigenes bauen. "
            f"Etwas, das wirklich hilft.\n\n"
            f"Nach vielen Nächten mit Python & ein bisschen KI-Zauber ist dieser Bot entstanden – "
            f"für <b>mich</b>, aber jetzt auch für <b>dich</b>.\n\n"
            f"Mit diesem Tool bekommst du <b>Live-Tracking</b>, <b>PnL</b>, <b>Winrate</b>, <b>SmartCoach-Analysen</b> "
            f"und jede Menge <b>Insider-Power</b>.\n\n"
            f"<b>Premium-Modus?</b> Ja, den gibt's auch – für alle, die noch mehr wollen: "
            f"<b>Developer-Zugriff</b>, <b>exklusive Features</b>, <b>Beta-Zugänge</b> & kleine <b>Extra-Goodies</b>.\n\n"
            f"🔥 Aktuell bist du mit der <b>Free-Version</b> unterwegs – und selbst die hat mehr drauf als 99 % aller Bots da draußen.\n\n"
            f"<b>Features & Commands:</b>\n"
            f"- /add WALLET TAG | ➕ <b>Fügt eine Wallet hinzu</b> & startet das Live-Tracking\n"
            f"- /rm | ➖ <b>Entfernt eine Wallet</b> aus deiner Tracking-Liste\n"
            f"- /list | 📃 <b>Zeigt alle getrackten Wallets</b> mit PnL & Winrate\n"
            f"- /profit WALLET +10 | 📈 <b>Trägt deinen Gewinn/Verlust</b> ein (z. B. +10 oder -7)\n"
            f"- /finder | 🔍 <b>SmartFinder-Modus</b> – entdecke smarte Wallets zum Tracken & Coachen\n"
            f"- /start | 🕹️ <b>Öffnet dieses Menü erneut</b> bei Bedarf\n\n"
            f"✨ Oder nutze einfach die Buttons unten:"
        )

        sent = await message.answer(text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)

        # Neue Startnachricht-ID speichern
        await save_user_start_message_id(user_id, sent.message_id)

    except Exception as e:
        await message.reply(f"❌ Fehler bei /start: {e}")
