import os
import json
import logging
from fastapi import FastAPI
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Init
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("RailwayStaticUrl") + "/" + BOT_TOKEN

application = Application.builder().token(BOT_TOKEN).build()
app = FastAPI()
scheduler = AsyncIOScheduler()

wallets = {}  # format: {wallet: {"tag": str, "profit": float, "wins": int, "losses": int}}
MODE_STATE = 1
custom_filters = {}  # for /own mode

# Dummy Smart Wallet Generator
def scan_wallets(min_wr=60, min_roi=5):
    return [
        {
            "wallet": "ABC123",
            "wr": 72,
            "roi": 18,
            "balance": 4.32,
            "age": 12,
            "pnl": "+0.8 SOL",
            "token": "WEN",
            "dex": "https://dexscreener.com/solana/abc123"
        }
    ] if min_wr <= 72 and min_roi <= 18 else []

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("💼 Wallets", callback_data="list")],
        [InlineKeyboardButton("➕ Add Wallet", callback_data="add")],
        [InlineKeyboardButton("📈 SmartFinder", callback_data="smartfinder")],
        [InlineKeyboardButton("💰 Profit", callback_data="profit")]
    ]
    await update.message.reply_text("Willkommen zum Tracker!", reply_markup=InlineKeyboardMarkup(buttons))

# /add <wallet> <tag>
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        tag = " ".join(context.args[1:]) if len(context.args) > 1 else ""
        wallets[wallet] = {"tag": tag, "profit": 0, "wins": 0, "losses": 0}
        await update.message.reply_text(f"✅ Wallet {wallet} mit Tag '{tag}' hinzugefügt.")
    except:
        await update.message.reply_text("⚠️ Usage: /add <wallet> <tag>")

# /rm <wallet>
async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in wallets:
            del wallets[wallet]
            await update.message.reply_text(f"🗑️ Wallet {wallet} entfernt.")
        else:
            await update.message.reply_text("Wallet nicht gefunden.")
    except:
        await update.message.reply_text("⚠️ Usage: /rm <wallet>")

# /list
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not wallets:
        await update.message.reply_text("📭 Keine Wallets getrackt.")
        return
    msg = "📊 Getrackte Wallets:\n\n"
    for wallet, data in wallets.items():
        wr_total = data["wins"] + data["losses"]
        wr = f'WR({data["wins"]}/{wr_total})' if wr_total else "WR(0/0)"
        pnl = f'PnL({data["profit"]:+.2f} sol)'
        pnl_color = "🟢" if data["profit"] > 0 else "🔴" if data["profit"] < 0 else "⚪️"
        msg += f"• {wallet} [{data['tag']}]\n→ {wr}, {pnl_color} {pnl}\n\n"
    await update.message.reply_text(msg)

# /profit <wallet> <+/-amount>
async def set_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        amount = float(context.args[1])
        if wallet not in wallets:
            await update.message.reply_text("⚠️ Wallet nicht gefunden.")
            return
        wallets[wallet]["profit"] += amount
        if amount > 0:
            wallets[wallet]["wins"] += 1
        else:
            wallets[wallet]["losses"] += 1
        await update.message.reply_text(f"📈 Neuer Profit für {wallet}: {wallets[wallet]['profit']:+.2f} sol")
    except:
        await update.message.reply_text("⚠️ Usage: /profit <wallet> <+/-amount>")

# /smartfinder
async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("🚀 Moonbags", callback_data="mode_moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
        [InlineKeyboardButton("🛠️ Own Filter", callback_data="mode_own")]
    ]
    await update.callback_query.message.reply_text("Wähle einen Modus:", reply_markup=InlineKeyboardMarkup(buttons))

# SmartFinder Handler
async def run_smartfinder():
    for mode in ["moonbags", "scalping", "own"]:
        if mode == "moonbags":
            found = scan_wallets(min_wr=60, min_roi=15)
        elif mode == "scalping":
            found = scan_wallets(min_wr=70, min_roi=5)
        elif mode == "own" and "min_wr" in custom_filters:
            found = scan_wallets(custom_filters["min_wr"], custom_filters["min_roi"])
        else:
            continue

        for wallet in found:
            msg = f"📡 Neue Wallet entdeckt:\n• {wallet['wallet']}\n"
            msg += f"WR: {wallet['wr']}% | ROI: {wallet['roi']}%\n"
            msg += f"💰 {wallet['balance']} SOL | ⏳ {wallet['age']} Tage\n"
            msg += f"📈 Token: {wallet['token']}\n🔗 [Dexscreener]({wallet['dex']})"
            btn = InlineKeyboardMarkup.from_button(InlineKeyboardButton("Dann mal los!", callback_data=f"track_{wallet['wallet']}"))
            await application.bot.send_message(chat_id=CHANNEL_ID, text=msg, reply_markup=btn, parse_mode="Markdown")

# /own
async def own_mode_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Mindest-Winrate (%):")
    return MODE_STATE

async def own_mode_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.replace("%", ""))
        context.user_data["min_wr"] = wr
        await update.message.reply_text("Mindest-ROI (%):")
        return ConversationHandler.END
    except:
        await update.message.reply_text("Ungültige Eingabe. Bitte Zahl eingeben.")
        return MODE_STATE

@application.post("/" + BOT_TOKEN)
async def webhook(update: dict):
    await application.update_queue.put(Update.de_json(update, application.bot))

# Callback Dispatcher
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "list":
        await list_wallets(update.callback_query, context)
    elif data == "add":
        await update.callback_query.message.reply_text("Nutze /add <wallet> <tag>")
    elif data == "profit":
        await update.callback_query.message.reply_text("Nutze /profit <wallet> <+/-Betrag>")
    elif data == "smartfinder":
        await smartfinder_menu(update, context)
    elif data.startswith("mode_own"):
        return await own_mode_entry(update, context)
    elif data.startswith("mode_"):
        await update.callback_query.message.reply_text("Modus aktiviert.")
    elif data.startswith("track_"):
        wallet = data.replace("track_", "")
        wallets[wallet] = {"tag": "🚀 AutoDetected", "profit": 0, "wins": 0, "losses": 0}
        await update.callback_query.message.reply_text(f"📍 Wallet {wallet} wird jetzt getrackt.")

# Setup
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", remove_wallet))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", set_profit))
application.add_handler(CallbackQueryHandler(callback_handler))

application.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(own_mode_entry, pattern="^mode_own$")],
    states={MODE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_mode_wr)]},
    fallbacks=[],
    name="own_mode",
    persistent=False,
))

scheduler.add_job(run_smartfinder, "interval", minutes=30)
scheduler.start()