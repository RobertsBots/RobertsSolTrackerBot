import logging
from aiogram import Bot
from aiogram.utils.exceptions import BadRequest, TelegramAPIError

logger = logging.getLogger(__name__)

async def send_alert(bot: Bot, chat_id: int, text: str):
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        logger.info(f"✅ Alert sent to chat_id {chat_id}: {text}")
    except BadRequest as e:
        logger.warning(f"⚠️ BadRequest while sending alert to {chat_id}: {e}")
    except TelegramAPIError as e:
        logger.error(f"❌ TelegramAPIError while sending alert to {chat_id}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while sending alert to {chat_id}: {e}")

async def notify_user(user_id: int, text: str):
    try:
        # Lazy import: vermeidet zirkuläre Importe beim Bot-Setup
        from main import bot  
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
        logger.info(f"📬 Notified user {user_id}: {text}")
    except BadRequest as e:
        logger.warning(f"⚠️ BadRequest while notifying user {user_id}: {e}")
    except TelegramAPIError as e:
        logger.error(f"❌ TelegramAPIError notifying user {user_id}: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to notify user {user_id}: {e}")
