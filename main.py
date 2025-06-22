
import time
import requests
import telegram
from telegram.ext import Updater, CommandHandler
import os

# Environment Variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Initialisieren des Bots
bot = telegram.Bot(token=TOKEN)

# Dummy-Wallets zum Start
wallets = {}

# Command: /add <wallet> <tag>
def add_wallet(update, context):
    if len(context.args) != 2:
        update.message.reply_text("Usage: /add <wallet> <tag>")
        return
    wallet, tag = context.args
    wallets[wallet] = tag
    update.message.reply_text(f"Wallet {wallet} mit Tag '{tag}' hinzugefügt.")

# Command: /rm <wallet>
def remove_wallet(update, context):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /rm <wallet>")
        return
    wallet = context.args[0]
    if wallet in wallets:
        del wallets[wallet]
        update.message.reply_text(f"Wallet {wallet} entfernt.")
    else:
        update.message.reply_text(f"Wallet {wallet} nicht gefunden.")

# Command: /list
def list_wallets(update, context):
    if not wallets:
        update.message.reply_text("Keine Wallets getrackt.")
        return
    msg = "Getrackte Wallets: Keine neuen Aktivitäten gefunden."
    for wallet, tag in wallets.items():
        msg += f"\n{tag}: {wallet}"
    update.message.reply_text(msg)

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", add_wallet))
    dp.add_handler(CommandHandler("rm", remove_wallet))
    dp.add_handler(CommandHandler("list", list_wallets))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
