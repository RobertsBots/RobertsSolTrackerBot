import os
import asyncio
from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties

async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # z. B. https://robertstracker-production.up.railway.app/DEIN_TOKEN

    if not TOKEN or not WEBHOOK_URL:
        print("❌ BOT_TOKEN oder WEBHOOK_URL fehlt in Environment Variables!")
        return

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    success = await bot.set_webhook(WEBHOOK_URL)

    if success:
        print("✅ Webhook erfolgreich gesetzt!")
    else:
        print("❌ Fehler beim Setzen des Webhooks!")

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
