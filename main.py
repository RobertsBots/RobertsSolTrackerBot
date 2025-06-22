import os
import telegram
from telegram import InputFile
from telegram.ext import Updater, CommandHandler
import logging

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

bot = telegram.Bot(token=TOKEN)

# Beispielkommando
def list_wallets(update, context):
    text = """📄 Getrackte Wallets:
1. BeispielWallet123
2. BeispielWallet456"""
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Willkommen beim Solana Wallet Tracker Bot!")

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("list", list_wallets))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
