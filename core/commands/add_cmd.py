from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import upsert_wallet

router = Router()

@router.message(Command("add"))
async def handle_add_cmd(message: types.Message):
    args = message.text.split()

    if len(args) != 3:
        await message.answer(
            "❗️Falsche Nutzung von /add\n\nNutze:\n`/add <WALLET> <TAG>`",
            parse_mode="Markdown",
        )
        return

    wallet = args[1]
    tag = args[2]

    upsert_wallet(wallet, tag)

    await message.answer(f"✅ Wallet `{wallet}` mit Tag `{tag}` hinzugefügt oder aktualisiert.", parse_mode="Markdown")
