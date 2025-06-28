import asyncio
from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties

TOKEN = "7953666029:AAEKunPOhUdeoS-57OlTDuZbRoOTgGY5P5o"
WEBHOOK_URL = f"https://robertstracker-production.up.railway.app/{TOKEN}"

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    success = await bot.set_webhook(WEBHOOK_URL)

    if success:
        print("✅ Webhook erfolgreich gesetzt!")
    else:
        print("❌ Fehler beim Setzen des Webhooks!")

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
