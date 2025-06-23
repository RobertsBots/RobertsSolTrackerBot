import os
import json
import logging
from fastapi import FastAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import aiohttp

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Data store
WALLETS_FILE = "wallets.json"
if not os.path.exists(WALLETS_FILE):
    with open(WALLETS_FILE, "w") as f:
        json.dump({}, f)

# Load wallets
def load_wallets():
    with open(WALLETS_FILE, "r") as f:
        return json.load(f)

def save_wallets(data):
    with open(WALLETS_FILE, "w") as f:
        json.dump(data, f)

# App
app = FastAPI()

# Telegram Bot init
bot_app = Application.builder().token(BOT_TOKEN).build()

# States
SET_WR, SET_ROI = range(2)

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📈 SmartFinder starten", callback_data="smartfinder")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Willkommen bei RobertsSolTrackerBot!", reply_markup=reply_markup)

# /add
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        tag = " ".join(context.args[1:])
        data = load_wallets()
        data[wallet] = {"tag": tag, "pnl": 0.0, "wins": 0, "losses": 0}
        save_wallets(data)
        await update.message.reply_text(f"✅ {wallet} mit Tag '{tag}' hinzugefügt.")
    except:
        await update.message.reply_text("⚠️ Format: /add <WALLET> <TAG>")

# /rm
async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        data = load_wallets()
        if wallet in data:
            del data[wallet]
            save_wallets(data)
            await update.message.reply_text(f"🗑️ Wallet {wallet} entfernt.")
        else:
            await update.message.reply_text("⚠️ Wallet nicht gefunden.")
    except:
        await update.message.reply_text("⚠️ Format: /rm <WALLET>")

# /list
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_wallets()
    if not data:
        await update.message.reply_text("📭 Keine Wallets getrackt.")
        return
    msg = ""
    for wallet, info in data.items():
        wr_total = info.get("wins", 0) + info.get("losses", 0)
        wr = f"{info.get('wins', 0)}/{wr_total}" if wr_total else "0/0"
        pnl = info.get("pnl", 0.0)
        pnl_str = f"PnL({pnl:+.2f} sol)"
        pnl_str = f"🟢 {pnl_str}" if pnl >= 0 else f"🔴 {pnl_str}"
        wr_str = f"WR({info.get('wins', 0)}/{wr_total})"
        msg += f"💼 {wallet} [{info.get('tag')}]\n{wr_str} | {pnl_str}\n\n"
    await update.message.reply_text(msg.strip())

# /profit
async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        amount = float(context.args[1])
        data = load_wallets()
        if wallet not in data:
            await update.message.reply_text("❌ Wallet nicht gefunden.")
            return
        data[wallet]["pnl"] += amount
        if amount >= 0:
            data[wallet]["wins"] += 1
        else:
            data[wallet]["losses"] += 1
        save_wallets(data)
        await update.message.reply_text(f"✅ Profit von {amount:+.2f} sol für {wallet} gespeichert.")
    except:
        await update.message.reply_text("⚠️ Format: /profit <WALLET> <+/-BETRAG>")

# SmartFinder Menü
async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🚀 Moonbags", callback_data="moonbags")],
        [InlineKeyboardButton("🧠 Eigene Filter", callback_data="own")]
    ]
    await query.edit_message_text("Wähle deinen SmartFinder-Modus:", reply_markup=InlineKeyboardMarkup(keyboard))

# /own Callback
async def own_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("📊 Gib deine minimale Winrate in % ein:")
    return SET_WR

# own WR
async def set_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.strip('% '))
        context.user_data["min_wr"] = wr
        await update.message.reply_text("Jetzt gib deine minimale ROI ein (z.B. 10):")
        return SET_ROI
    except:
        await update.message.reply_text("⚠️ Bitte eine gültige Zahl eingeben.")
        return SET_WR

# own ROI
async def set_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.strip('% '))
        context.user_data["min_roi"] = roi
        await update.message.reply_text(f"✅ Eigene Filter gesetzt: WR ≥ {context.user_data['min_wr']}%, ROI ≥ {roi}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("⚠️ Bitte eine gültige Zahl eingeben.")
        return SET_ROI

# AutoScanner
async def scan_wallets(context: ContextTypes.DEFAULT_TYPE):
    # Dummy Wallets
    smart_wallets = {
        "So1SmartW1": {"tag": "Auto 🚀", "wr": 70, "roi": 15},
        "So1SmartW2": {"tag": "Auto 🚀", "wr": 85, "roi": 22},
    }
    data = load_wallets()
    for wallet, info in smart_wallets.items():
        if wallet not in data:
            data[wallet] = {"tag": info["tag"], "pnl": 0.0, "wins": 0, "losses": 0}
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"📡 Neue Smart Wallet entdeckt:\n\n💼 {wallet}\n🏷️ {info['tag']}\n📊 WR {info['wr']}% | ROI {info['roi']}%",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Jetzt tracken", callback_data=f"track_{wallet}")]
                ])
            )
    save_wallets(data)

# Track-Button
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("track_"):
        wallet = query.data.split("_")[1]
        data = load_wallets()
        if wallet not in data:
            data[wallet] = {"tag": "Auto 🚀", "pnl": 0.0, "wins": 0, "losses": 0}
            save_wallets(data)
            await query.edit_message_text(f"✅ {wallet} wird nun getrackt.")

# Webhook route
@app.post("/")
async def telegram_webhook(update: dict):
    await bot_app.update_queue.put(Update.de_json(update, bot_app.bot))
    return {"ok": True}

# Scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(scan_wallets, trigger=IntervalTrigger(minutes=30), args=[bot_app])
scheduler.start()

# Handlers
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("own", own_callback), CallbackQueryHandler(own_callback, pattern="own")],
    states={
        SET_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_wr)],
        SET_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_roi)],
    },
    fallbacks=[],
    per_message=True
)

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("add", add_wallet))
bot_app.add_handler(CommandHandler("rm", remove_wallet))
bot_app.add_handler(CommandHandler("list", list_wallets))
bot_app.add_handler(CommandHandler("profit", profit))
bot_app.add_handler(CallbackQueryHandler(smartfinder_menu, pattern="smartfinder"))
bot_app.add_handler(CallbackQueryHandler(button_handler, pattern="track_.*"))
bot_app.add_handler(conv_handler)

# Start bot
if __name__ == "__main__":
    import asyncio
    import uvicorn
    bot_app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=WEBHOOK_URL
    )