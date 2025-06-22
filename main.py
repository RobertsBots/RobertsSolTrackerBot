
import os
import time
import telegram
import requests
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telegram.Bot(token=TOKEN)
tracked_wallets = {}

def add_wallet(update, context):
    if len(context.args) != 2:
        update.message.reply_text("Benutzung: /add <WALLET> <NAME>")
        return
    wallet, name = context.args
    tracked_wallets[wallet] = name
    update.message.reply_text(f"Wallet {wallet} ({name}) wurde hinzugefügt.")

def remove_wallet(update, context):
    if len(context.args) != 1:
        update.message.reply_text("Benutzung: /rm <WALLET>")
        return
    wallet = context.args[0]
    if wallet in tracked_wallets:
        del tracked_wallets[wallet]
        update.message.reply_text(f"Wallet {wallet} wurde entfernt.")
    else:
        update.message.reply_text("Wallet nicht gefunden.")

def list_wallets(update, context):
    if not tracked_wallets:
        update.message.reply_text("Keine Wallets getrackt.")
        return
    msg = "Getrackte Wallets:
"
    for w, n in tracked_wallets.items():
        msg += f"- {n}: {w}
"
    update.message.reply_text(msg)

def check_wallets():
    for wallet, name in tracked_wallets.items():
        url = f"https://public-api.solscan.io/account/tokens?account={wallet}"
        response = requests.get(url)
        if response.ok:
            # simulate activity detection (you may need a better source)
            bot.send_message(chat_id=CHANNEL_ID, text=f"📈 Aktivität bei {name}:
https://dexscreener.com/solana/{wallet}")

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", add_wallet))
    dp.add_handler(CommandHandler("rm", remove_wallet))
    dp.add_handler(CommandHandler("list", list_wallets))
    updater.start_polling()

    while True:
        check_wallets()
        time.sleep(60)

if __name__ == "__main__":
    main()
