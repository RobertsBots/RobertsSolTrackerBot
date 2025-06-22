import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telegram.Bot(token=TOKEN)

wallets = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Willkommen beim RobertsSolTrackerBot!")

def add_wallet(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 2:
        update.message.reply_text("Verwendung: /add <WALLET> <TAG>")
        return
    wallet, tag = context.args
    wallets[wallet] = tag
    update.message.reply_text(f"Wallet {wallet} mit Tag '{tag}' hinzugefügt.")

def list_wallets(update: Update, context: CallbackContext) -> None:
    if not wallets:
        update.message.reply_text("Keine Wallets getrackt.")
        return
    text = "📄 Getrackte Wallets:
"
    for wallet, tag in wallets.items():
        text += f"- {wallet} ({tag})\n"
    update.message.reply_text(text)

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_wallet))
    dp.add_handler(CommandHandler("list", list_wallets))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
