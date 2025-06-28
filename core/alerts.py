import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)

async def send_alert(bot: Bot, chat_id: int, text: str):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"✅ Alert sent to chat_id {chat_id}: {text}")
    except TelegramAPIError as e:
        logger.error(f"❌ TelegramAPIError while sending alert to chat_id {chat_id}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while sending alert to chat_id {chat_id}: {e}")

# 🔔 Utility-Funktion für einfache Benachrichtigung
async def notify_user(user_id: int, text: str):
    try:
        from core.main import bot  # Lazy Import: verhindert zirkuläre Abhängigkeiten
        await bot.send_message(chat_id=user_id, text=text)
        logger.info(f"📬 Notified user {user_id} with message: {text}")
    except Exception as e:
        logger.error(f"❌ Failed to notify user {user_id}: {e}")
