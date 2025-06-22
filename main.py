
import os
import time
import telegram
import requests
from telegram.ext import Updater, CommandHandler

# Bot-Token aus Umgebungsvariable holen
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # z. B. -4690026526
bot = telegram.Bot(token=TOKEN)

# Dictionary für getrackte Wallets
tracked_wallets = {}

# Neue Wallet hinzufügen
def add_wallet(update, context):
    try:
        wallet = context.args[0]
        tag = context.args[1] if len(context.args) > 1 else "ohne_tag"
        tracked_wallets[wallet] = {"tag": tag, "last_tx": None}
        update.message.reply_text(f"Wallet {wallet} mit Tag '{tag}' hinzugefügt.")
    except IndexError:
        update.message.reply_text("Verwendung: /add <wallet> <tag>")

# Wallet entfernen
def remove_wallet(update, context):
    try:
        wallet = context.args[0]
        if wallet in tracked_wallets:
            del tracked_wallets[wallet]
            update.message.reply_text(f"Wallet {wallet} entfernt.")
        else:
            update.message.reply_text("Wallet nicht gefunden.")
    except IndexError:
        update.message.reply_text("Verwendung: /rm <wallet>")

# Auflistung
def list_wallets(update, context):
    if not tracked_wallets:
        update.message.reply_text("Keine Wallets getrackt.")
    else:
        msg = "Getrackte Wallets:\n"
        for wallet, data in tracked_wallets.items():
            msg += f"{data['tag']}: {wallet}\n"
        update.message.reply_text(msg)

# Telegram Bot Setup
def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", add_wallet))
    dp.add_handler(CommandHandler("rm", remove_wallet))
    dp.add_handler(CommandHandler("list", list_wallets))

    updater.start_polling()
    print("Bot läuft...")

    # Polling Loop alle 60 Sekunden
    while True:
        for wallet, data in tracked_wallets.items():
            tag = data['tag']
            sol_balance = check_balance(wallet)
            txs = get_latest_tx(wallet)
            if txs and txs != data["last_tx"]:
                msg = f"🔍 Neue Aktivität bei {tag}:\n{txs}"
                bot.send_message(chat_id=CHANNEL_ID, text=msg)
                tracked_wallets[wallet]["last_tx"] = txs
        time.sleep(60)

# Dummy-Funktion für TX & Balance
def check_balance(wallet):
    try:
        r = requests.get(f"https://api.mainnet-beta.solana.com", timeout=5)
        return "1.23 SOL"  # Simuliert
    except Exception:
        return "?"

def get_latest_tx(wallet):
    return "Buy: BONK\nhttps://dexscreener.com/solana/bonk"

if __name__ == '__main__':
    main()
