from aiogram.types import Message
from core.database import add_wallet
from core.config import CHANNEL_ID
from aiogram import Bot

async def add_cmd(message: Message, bot: Bot):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.reply("❌ Bitte nutze das Format:\n<code>/add WALLET TAG</code>")
            return

        wallet = args[1]
        tag = " ".join(args[2:])

        success = add_wallet(wallet, tag)

        if not success:
            await message.reply("⚠️ Diese Wallet wird bereits getrackt.")
            return

        dex_url = f"https://dexscreener.com/solana/{wallet}"

        await message.reply(f"✅ <b>Wallet hinzugefügt:</b>\n📬 <code>{wallet}</code>\n🏷️ Tag: <b>{tag}</b>")
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                f"🆕 Neue Wallet hinzugefügt\n\n"
                f"<code>{wallet}</code>\n"
                f"🏷️ <b>{tag}</b>\n"
                f"🔗 <a href='{dex_url}'>Dexscreener öffnen</a>"
            )
        )
    except Exception as e:
        await message.reply(f"❌ Fehler beim Hinzufügen: {e}")
