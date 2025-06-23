from telegram import Update
from telegram.ext import CallbackContext
from core.database import add_wallet
from core.ui import send_message_with_buttons


async def handle_add_wallet(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("❗ Bitte nutze das Format:\n<code>/add WALLET TAG</code>")
        return

    wallet = context.args[0]
    tag = " ".join(context.args[1:])

    success = add_wallet(wallet, tag)
    if success:
        msg = f"✅ Wallet <code>{wallet}</code> mit dem Tag <b>{tag}</b> wurde erfolgreich hinzugefügt."
    else:
        msg = f"⚠️ Wallet <code>{wallet}</code> existiert bereits."

    await send_message_with_buttons(update, context, msg)
