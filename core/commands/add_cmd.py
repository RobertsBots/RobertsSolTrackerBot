from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import add_wallet

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

    wallet = args[1]
    tag = args[2]

    success = add_wallet(message.from_user.id, wallet, tag)

    if success:
        await message.answer(f"✅ Wallet `{wallet}` mit Tag `{tag}` hinzugefügt.", parse_mode="Markdown")
    else:
        await message.answer(f"⚠️ Wallet `{wallet}` ist bereits vorhanden.", parse_mode="Markdown")
