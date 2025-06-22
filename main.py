import os
import pytz
import logging
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from wallet_checker import check_wallets

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

logging.basicConfig(level=logging.INFO)
scheduler = BackgroundScheduler(timezone=pytz.utc)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""👋 Willkommen beim Solana Wallet Tracker Bot!
Verwende /add <wallet> <tag>, um eine Wallet zu überwachen.
Verwende /rm <wallet>, um sie zu entfernen.
Verwende /list, um alle getrackten Wallets anzuzeigen.""")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", check_wallets.add_wallet))
    app.add_handler(CommandHandler("rm", check_wallets.remove_wallet))
    app.add_handler(CommandHandler("list", check_wallets.list_wallets))

    scheduler.add_job(check_wallets.check_wallets, "interval", seconds=60)
    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()