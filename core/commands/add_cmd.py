# core/commands/add_cmd.py

import logging
from aiogram import Router, types
from aiogram.filters import Command
from core.database import add_wallet

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("add"))
async def add_wallet_cmd(message: types.Message):
    args = message.text.split()

    if len(args) != 3:
        await message.answer(
            "❗️Falsche Nutzung von /add\n\nNutze:\n`/add <WALLET> <TAG>`",
            parse_mode="Markdown",
        )
        return

    wallet, tag = args[1], args[2]
    success = add_wallet(message.from_user.id, wallet, tag)

    if success:
        await message.answer(f"✅ Wallet `{wallet}` mit Tag `{tag}` hinzugefügt.", parse_mode="Markdown")
        logger.info(f"Wallet hinzugefügt: {wallet} (Tag: {tag}) – User {message.from_user.id}")
    else:
        await message.answer(f"⚠️ Wallet `{wallet}` ist bereits vorhanden.", parse_mode="Markdown")
