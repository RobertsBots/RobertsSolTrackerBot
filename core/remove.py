from telegram import Update
from telegram.ext import CallbackContext
from core.database import remove_wallet
from core.ui import send_message_with_buttons


async def handle_remove_wallet(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 1:
        await update.message.reply_text("❗ Bitte gib die Wallet-Adresse an:\n<code>/rm WALLET</code>")
        return

    wallet = context.args[0]

    success = remove_wallet(wallet)
    if success:
        msg = f"🗑️ Wallet <code>{wallet}</code> wurde erfolgreich entfernt."
    else:
        msg = f"⚠️ Wallet <code>{wallet}</code> konnte nicht entfernt werden (nicht gefunden)."

    await send_message_with_buttons(update, context, msg)
