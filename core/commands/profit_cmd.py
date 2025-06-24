from aiogram.types import Message
from core.database import update_pnl
import re

async def profit_cmd(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply(
            "❗️Bitte verwende das Format:\n<code>/profit WALLET +/-BETRAG</code>\n\nBeispiel:\n<code>/profit ABC123 +1.5</code>"
        )
        return

    address = parts[1]
    amount_str = parts[2]

    if not re.match(r"^[+-]?\d+(\.\d+)?$", amount_str):
        await message.reply("⚠️ Ungültiges Format für den Betrag. Bitte mit + oder – angeben.")
        return

    try:
        amount = float(amount_str)
    except ValueError:
        await message.reply("⚠️ Betrag muss eine gültige Zahl sein.")
        return

    success = update_pnl(address, amount)
    if success:
        emoji = "🟢" if amount > 0 else "🔴"
        await message.reply(f"{emoji} <b>{amount:+.2f} SOL</b> wurde der Wallet <code>{address}</code> gutgeschrieben.")
    else:
        await message.reply("❌ Wallet nicht gefunden.")
