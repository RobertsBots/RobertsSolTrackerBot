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
                "❗️Falsche Nutzung von /add\n\nNutze:\n`/add <WALLET> <TAG>`",
                parse_mode="Markdown",
            )
            return

        wallet = args[1].strip()
        tag = args[2].strip()

        if not wallet or not tag:
            await message.answer(
                "⚠️ Bitte gib sowohl eine Wallet-Adresse als auch einen Tag an.",
                parse_mode="Markdown",
            )
            return

        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            await message.answer("❌ Benutzer-ID konnte nicht ermittelt werden.")
            return

        success = await add_wallet(user_id=user_id, wallet=wallet, tag=tag)

        if success:
            await message.answer(
                f"✅ Wallet `{wallet}` mit Tag `{tag}` hinzugefügt und wird nun getrackt.",
                parse_mode="Markdown"
            )
            logger.info(f"📥 Wallet hinzugefügt: {wallet} (Tag: {tag}) – User {user_id}")
        else:
            await message.answer(
                f"⚠️ Wallet `{wallet}` ist bereits in deiner Trackliste.",
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.exception("❌ Fehler bei /add:")
        await message.answer("❌ Ein unerwarteter Fehler ist aufgetreten.")

def register_add_cmd(dp: Dispatcher):
    dp.register_message_handler(add_wallet_cmd, commands=["add"])
