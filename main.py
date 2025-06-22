import os
import asyncio
import logging
import json
import aiohttp
from typing import Dict
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_HOST = os.getenv("RailwayStaticUrl")
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Daten
tracked_wallets: Dict[str, Dict] = {}
wallet_stats: Dict[str, Dict] = {}
own_filters: Dict[str, Dict] = {}
SELECTING_WR, SELECTING_ROI = range(2)

# FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Bot läuft"}

# Telegram-Logik
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Wallet tracken", callback_data='add_wallet')],
        [InlineKeyboardButton("🗑️ Wallet entfernen", callback_data='rm_wallet')],
        [InlineKeyboardButton("📋 Getrackte Wallets", callback_data='list_wallets')],
        [InlineKeyboardButton("📈 Gewinn eintragen", callback_data='add_profit')],
        [InlineKeyboardButton("🚀 SmartFinder starten", callback_data='smartfinder')],
    ]
    await update.message.reply_text(
        "Willkommen beim Solana Wallet Tracker Bot!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "add_wallet":
        await query.edit_message_text("Bitte sende mir die Wallet-Adresse + Tag:\n`/add <wallet> <tag>`")
    elif query.data == "rm_wallet":
        await query.edit_message_text("Bitte sende mir den Befehl zum Entfernen:\n`/rm <wallet>`")
    elif query.data == "list_wallets":
        await list_wallets(update, context)
    elif query.data == "add_profit":
        await query.edit_message_text("Bitte nutze `/profit <wallet> <+/-betrag>`")
    elif query.data == "smartfinder":
        await show_smartfinder_menu(update, context)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, tag = context.args[0], " ".join(context.args[1:])
        tracked_wallets[wallet] = {"tag": tag}
        wallet_stats[wallet] = {"win": 0, "loss": 0, "pnl": 0}
        await context.bot.send_message(CHANNEL_ID, f"👀 Tracking gestartet für {wallet} ({tag})")
    except:
        await update.message.reply_text("❌ Fehler beim Hinzufügen. Verwende: /add <wallet> <tag>")

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in tracked_wallets:
            tracked_wallets.pop(wallet)
            wallet_stats.pop(wallet)
            await update.message.reply_text(f"🗑️ Nicht mehr getrackt: {wallet}")
        else:
            await update.message.reply_text("❌ Diese Wallet wird nicht getrackt.")
    except:
        await update.message.reply_text("❌ Fehler beim Entfernen. Verwende: /rm <wallet>")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await update.message.reply_text("📭 Keine Wallets getrackt.")
        return
    lines = []
    for wallet, info in tracked_wallets.items():
        stats = wallet_stats.get(wallet, {"win": 0, "loss": 0, "pnl": 0})
        wr = f"WR({stats['win']}/{stats['loss']})"
        pnl = stats["pnl"]
        pnl_text = f"PnL({pnl} sol)"
        line = f"• {wallet} ({info['tag']})\n   {wr}   {pnl_text}"
        lines.append(line)
    await update.message.reply_text("\n\n".join(lines))

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, amount = context.args[0], context.args[1]
        if wallet not in wallet_stats:
            await update.message.reply_text("❌ Diese Wallet wird nicht getrackt.")
            return
        if amount.startswith("+"):
            wallet_stats[wallet]["pnl"] += float(amount[1:])
            wallet_stats[wallet]["win"] += 1
        elif amount.startswith("-"):
            wallet_stats[wallet]["pnl"] -= float(amount[1:])
            wallet_stats[wallet]["loss"] += 1
        else:
            await update.message.reply_text("❗ Bitte + oder - vor dem Betrag angeben.")
            return
        await update.message.reply_text(f"✅ PnL aktualisiert für {wallet}")
    except:
        await update.message.reply_text("❌ Fehler. Nutze `/profit <wallet> <+/-betrag>`")

async def show_smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Moonbags", callback_data='mode_moonbags')],
        [InlineKeyboardButton("⚡ Scalping", callback_data='mode_scalping')],
        [InlineKeyboardButton("⚙️ Eigene Filter", callback_data='mode_own')],
    ]
    await update.callback_query.edit_message_text("Wähle einen SmartFinder-Modus:", reply_markup=InlineKeyboardMarkup(keyboard))

async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "mode_own":
        await query.edit_message_text("Gib deine gewünschte Mindest-Winrate in % ein (z. B. 65):")
        return SELECTING_WR
    elif query.data == "mode_moonbags":
        own_filters["mode"] = {"wr": 70, "roi": 40}
        await query.edit_message_text("🚀 Moonbags-Modus aktiviert.")
    elif query.data == "mode_scalping":
        own_filters["mode"] = {"wr": 60, "roi": 10}
        await query.edit_message_text("⚡ Scalping-Modus aktiviert.")
    return ConversationHandler.END

async def wr_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.replace("%", "").strip())
        context.user_data["wr"] = wr
        await update.message.reply_text("Und jetzt deine Mindest-ROI in % (z. B. 20):")
        return SELECTING_ROI
    except:
        await update.message.reply_text("❌ Bitte eine gültige Zahl eingeben.")

async def roi_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.replace("%", "").strip())
        own_filters["mode"] = {"wr": context.user_data["wr"], "roi": roi}
        await update.message.reply_text(f"⚙️ Eigene Filter gesetzt: WR ≥ {context.user_data['wr']} %, ROI ≥ {roi} %")
    except:
        await update.message.reply_text("❌ Ungültige ROI-Eingabe.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Abgebrochen.")
    return ConversationHandler.END

# Dummy Smart Wallet Scan
async def smart_wallet_scanner():
    if "mode" not in own_filters:
        return
    wr_min = own_filters["mode"]["wr"]
    roi_min = own_filters["mode"]["roi"]
    dummy_wallets = [
        {"wallet": "So1....ABC", "wr": 75, "roi": 42, "age": "7d", "balance": "3.21", "token": "ABC"},
        {"wallet": "So1....DEF", "wr": 58, "roi": 18, "age": "3d", "balance": "1.76", "token": "DEF"},
    ]
    for w in dummy_wallets:
        if w["wr"] >= wr_min and w["roi"] >= roi_min:
            msg = (
                f"🧠 Smart Wallet entdeckt!\n"
                f"📈 WR: {w['wr']} %, ROI: {w['roi']} %\n"
                f"⏳ Age: {w['age']} | 💰 Balance: {w['balance']} SOL\n"
                f"🪙 Token: {w['token']}\n"
                f"[Dexscreener](https://dexscreener.com/solana/{w['token'].lower()})"
            )
            await bot.send_message(CHANNEL_ID, msg, parse_mode='Markdown')

# Bot starten
async def main():
    global bot
    application = Application.builder().token(BOT_TOKEN).build()
    bot = application.bot

    # Handler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(mode_callback)],
        states={
            SELECTING_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, wr_input)],
            SELECTING_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, roi_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("rm", rm))
    application.add_handler(CommandHandler("list", list_wallets))
    application.add_handler(CommandHandler("profit", profit))
    application.add_handler(conv_handler)

    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(smart_wallet_scanner, 'interval', minutes=30)
    scheduler.start()

    # Webhook starten
    await application.initialize()
    await application.bot.set_webhook(url=WEBHOOK_URL)
    await application.start()
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=8080,
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL,
    )
    await application.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())