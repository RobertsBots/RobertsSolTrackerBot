import logging
from aiogram import types, Dispatcher, Bot
from core.database import add_wallet

logger = logging.getLogger(__name__)

# Handler-Funktion für /add
async def add_wallet_cmd(message: types.Message):
    try:
        Bot.set_current(message.bot)
        args = message.text.split()

        if len(args) != 3:
            await message.answer(
                "❗️Falsche Nutzung von <code>/add</code>\n\nNutze:\n<code>/add WALLET TAG</code>",
                parse_mode="HTML",
            )
            return

        wallet = args[1].strip()
        tag = args[2].strip()

        if not wallet or not tag:
            await message.answer(
                "⚠️ Bitte gib sowohl eine Wallet-Adresse als auch einen Tag an.",
                parse_mode="HTML",
            )
            return

        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            await message.answer("❌ Benutzer-ID konnte nicht ermittelt werden.", parse_mode="HTML")
            return

        success = await add_wallet(user_id=user_id, wallet=wallet, tag=tag)

        if success:
            await message.answer(
                f"✅ Wallet <code>{wallet}</code> mit Tag <code>{tag}</code> hinzugefügt und wird nun getrackt.",
                parse_mode="HTML"
            )
            logger.info(f"📥 Wallet hinzugefügt: {wallet} (Tag: {tag}) – User {user_id}")
        else:
            await message.answer(
                f"⚠️ Wallet <code>{wallet}</code> ist bereits in deiner Trackliste.",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.exception("❌ Fehler bei /add:")
        await message.answer("❌ Ein unerwarteter Fehler ist aufgetreten.", parse_mode="HTML")

def register_add_cmd(dp: Dispatcher):
    dp.register_message_handler(add_wallet_cmd, commands=["add"])
