# core/alerts.py

import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

logger = logging.getLogger(__name__)

async def send_alert(bot: Bot, chat_id: int, text: str):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"✅ Alert sent to chat_id {chat_id}: {text}")
    except TelegramBadRequest as e:
        logger.warning(f"⚠️ TelegramBadRequest while sending to {chat_id}: {e}")
    except TelegramAPIError as e:
        logger.error(f"❌ TelegramAPIError while sending to {chat_id}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while sending to {chat_id}: {e}")

async def notify_user(user_id: int, text: str):
    from main import bot  # Lazy import verhindert zirkuläre Abhängigkeiten
    try:
        await bot.send_message(chat_id=user_id, text=text)
        logger.info(f"📬 Notified user {user_id}: {text}")
    except TelegramAPIError as e:
        logger.error(f"❌ TelegramAPIError notifying user {user_id}: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to notify user {user_id}: {e}")
