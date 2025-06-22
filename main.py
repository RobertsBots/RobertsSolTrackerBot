import os
import time
import telegram
from telegram import InputFile
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telegram.Bot(token=TOKEN)

tracked_wallets = {}

def get_wallet_activity():
    # Platzhalterfunktion – echte Logik kommt später
    return [{"wallet": "ABC123...", "action": "BUY", "token": "BONK", "link": "https://dexscreener.com/"}]

def send_message(msg):
    bot.send_message(chat_id=CHANNEL_ID, text=msg)

def main():
    send_message("🤖 Bot ist jetzt aktiv und überwacht die Wallets.")
    while True:
        activity = get_wallet_activity()
        if activity:
            for act in activity:
                msg = f"📈 {act['wallet']} hat {act['action']} {act['token']} getradet\n👉 {act['link']}"
                send_message(msg)
        time.sleep(60)

if __name__ == "__main__":
    main()