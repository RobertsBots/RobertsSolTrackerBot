import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

tracked_wallets = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Willkommen beim RobertsSolTrackerBot!")

def add_wallet(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Verwendung: /add <WALLET> <TAG>")
        return
    wallet, tag = context.args[0], context.args[1]
    tracked_wallets[wallet] = tag
    update.message.reply_text(f"✅ Wallet {wallet} mit Tag '{tag}' hinzugefügt.")

def list_wallets(update: Update, context: CallbackContext):
    if not tracked_wallets:
        update.message.reply_text("❌ Keine Wallets getrackt.")
        return
    msg = "\n".join([f"{w} → {t}" for w, t in tracked_wallets.items()])
    update.message.reply_text(f"📋 Getrackte Wallets:\n{msg}")

def check_wallets():
    for wallet, tag in tracked_wallets.items():
        # Beispielhafte API – bitte durch echte ersetzen
        response = requests.get(f"https://api.solana.fm/v0/account/{wallet}")
        if response.status_code == 200:
            logging.info(f"Aktivität für {wallet} ({tag}) geprüft.")
        else:
            logging.error(f"Fehler beim Prüfen von {wallet}")

def main():
    logging.basicConfig(level=logging.INFO)
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_wallet))
    dp.add_handler(CommandHandler("list", list_wallets))

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_wallets, "interval", seconds=60)
    scheduler.start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
