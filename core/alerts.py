import logging
from telegram import Bot

logger = logging.getLogger(__name__)

async def send_alert(bot: Bot, chat_id: int, text: str):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"✅ Alert sent to chat_id {chat_id}: {text}")
    except Exception as e:
        logger.error(f"❌ Failed to send alert to chat_id {chat_id}: {e}")
