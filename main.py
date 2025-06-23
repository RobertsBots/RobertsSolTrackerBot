import os
import json
import asyncio
import logging
from typing import Dict, Tuple
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL")

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

wallets: Dict[str, Dict] = {}
user_filters: Dict[str, Dict[str, int]] = {}
conversation_states: Dict[str, Dict[str, str]] = {}

# Conversation steps
ASK_WR, ASK_ROI = range(2)

# Logging
logging.basicConfig(level=logging.INFO)

# Dummy Smart Wallet Discovery (ersetzen durch echte API bei Bedarf)
def discover_smart_wallets(min_wr=60, min_roi=5):
    return [
        {
            "address": "SmartWalletXYZ123",
            "wr": 67,
            "roi": 22,
            "age": "11d",
            "sol": "1.23",
            "token": "XYZ",
        }
    ]

async def post_wallet_to_channel(wallet):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Dann mal los 🚀", callback_data=f"track_{wallet['address']}")]]
    )
    message = f"""🚨 Neue Smart Wallet entdeckt:

💼 Address: `{wallet['address']}`
📈 Winrate: {wallet['wr']} %
📊 ROI: {wallet['roi']} %
👴 Wallet Age: {wallet['age']}
💰 Balance: {wallet['sol']} SOL
🪙 Token: {wallet['token']}

👉 Jetzt übernehmen?"""
    await application.bot.send_message(
        chat_id=CHANNEL_ID,
        text=message,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )

async def auto_discover_wallets():
    logging.info("⏱ Auto-Discovery gestartet...")
    for user_id, filters in user_filters.items():
        wr = filters.get("wr", 60)
        roi = filters.get("roi", 10)
        wallets = discover_smart_wallets(min_wr=wr, min_roi=roi)
        for wallet in wallets:
            await post_wallet_to_channel(wallet)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("Wallet entfernen", callback_data="remove_wallet")],
        [InlineKeyboardButton("Profit eintragen", callback_data="add_profit")],
        [InlineKeyboardButton("SmartFinder starten", callback_data="smartfinder_menu")],
    ]
    await update.message.reply_text(
        "Willkommen beim Solana Wallet Tracker Bot!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("track_"):
        wallet = query.data.split("track_")[1]
        wallets[wallet] = {"tag": "🚀 AutoDetected"}
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"✅ Neue Wallet übernommen: `{wallet}`",
            parse_mode="Markdown",
        )
    elif query.data == "smartfinder_menu":
        keyboard = [
            [InlineKeyboardButton("🌕 Moonbags", callback_data="smart_moonbags")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="smart_scalping")],
            [InlineKeyboardButton("⚙️ Eigene Filter", callback_data="smart_own")],
        ]
        await query.edit_message_text(
            text="Wähle deinen SmartFinder-Modus:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif query.data == "smart_own":
        await query.message.reply_text("Bitte gib die minimale Winrate ein (z. B. 60):")
        return ASK_WR
    return ConversationHandler.END

async def ask_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.replace("%", ""))
        context.user_data["wr"] = wr
        await update.message.reply_text("Und jetzt den minimalen ROI? (z. B. 10):")
        return ASK_ROI
    except:
        await update.message.reply_text("❌ Ungültige Eingabe. Bitte eine Zahl eingeben:")
        return ASK_WR

async def ask_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.replace("%", ""))
        wr = context.user_data["wr"]
        user_id = str(update.effective_user.id)
        user_filters[user_id] = {"wr": wr, "roi": roi}
        await update.message.reply_text(
            f"✅ Eigene Filter gesetzt: WR ≥ {wr} %, ROI ≥ {roi} %"
        )
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Ungültige Eingabe. Bitte eine Zahl eingeben:")
        return ASK_ROI

@app.post("/" + BOT_TOKEN)
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_discover_wallets, "interval", minutes=30, id="auto_discover_wallets")
    scheduler.start()
    logging.info("✅ Scheduler gestartet")

def main():
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^smart_own$")],
        states={
            ASK_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_wr)],
            ASK_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_roi)],
        },
        fallbacks=[],
        per_message=True,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(conv_handler)

    # Start via webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=f"{RAILWAY_STATIC_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()