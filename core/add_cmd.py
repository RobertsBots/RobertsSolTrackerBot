from aiogram.types import Message
from core.database import add_wallet
from core.helpers import is_valid_solana_address

async def add_cmd(message: Message):
    try:
        parts = message.text.strip().split()
        if len(parts) < 3:
            await message.reply("❗️Bitte benutze das Format:\n<code>/add WALLET TAG</code>")
            return

        address = parts[1]
        tag = " ".join(parts[2:])

        if not is_valid_solana_address(address):
            await message.reply("🚫 Ungültige Wallet-Adresse.")
            return

        success = add_wallet(address, tag)
        if success:
            await message.reply(f"✅ Wallet <code>{address}</code> wurde mit Tag <b>{tag}</b> hinzugefügt.")
        else:
            await message.reply(f"⚠️ Wallet <code>{address}</code> ist bereits in der Liste.")
    except Exception as e:
        await message.reply(f"❌ Fehler beim Hinzufügen der Wallet: {str(e)}")
