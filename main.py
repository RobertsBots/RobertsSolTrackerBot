import os
import logging
import asyncio
import json
import random
from datetime import datetime
from fastapi import FastAPI, Request
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = f"https://{os.environ.get('RAILWAY_STATIC_URL')}/webhook"
CHANNEL_ID = os.environ.get("CHANNEL_ID", "-4690026526")

app = FastAPI()
logging.basicConfig(level=logging.INFO)

wallets = {}
profit_data = {}
own_filters = {"wr": 60, "roi": 5}

START_WR, START_ROI = range(2)

def build_wallet_message(wallet, tag="🚀 AutoDetected"):
    return (
        f"<b>{wallet}</b> (🔗 <a href='https://birdeye.so/address/{wallet}?chain=solana'>Birdeye</a>) - 💰 {random.randint(3,15)} SOL - ⌛ {random.randint(30,400)}d\n"
        f"WinRate: <b>{random.randint(60,95)}%</b> | ROI: <b>{random.randint(5,25)}%</b> | 7d PnL: {random.randint(3,15)} SOL\n"
        f"7d Tokens: {random.randint(5,12)} | All Tokens: {random.randint(20,70)} | Hodl Tokens: {random.randint(2,5)}\n"
        f"Lifetime PnL: {random.randint(20,250)} SOL | Tracking: 👇"
    )

@app.post("/webhook")
async def telegram_webhook(update: Request):
    data = await update.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "Bot is running"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Wallet", callback_data="add"),
            InlineKeyboardButton("🧾 Wallet List", callback_data="list")
        ],
        [
            InlineKeyboardButton("💼 Profit Track", callback_data="profit"),
            InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder")
        ]
    ]
    await update.message.reply_text("Willkommen beim SolTrackerBot!", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "smartfinder":
        buttons = [
            [InlineKeyboardButton("🚀 Moonbags", callback_data="moonbags")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="scalping")],
            [InlineKeyboardButton("🧪 Own", callback_data="own")]
        ]
        await query.edit_message_text("Wähle einen SmartFinder-Modus:", reply_markup=InlineKeyboardMarkup(buttons))
    elif query.data == "moonbags":
        own_filters["wr"], own_filters["roi"] = 75, 10
        await query.edit_message_text("🚀 Moonbags Modus aktiviert.")
    elif query.data == "scalping":
        own_filters["wr"], own_filters["roi"] = 60, 3
        await query.edit_message_text("⚡ Scalping Modus aktiviert.")
    elif query.data == "own":
        await query.edit_message_text("🧪 Bitte sende deine gewünschte Mindest-Winrate (z. B. 65):")
        return START_WR

async def own_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        own_filters["wr"] = int(update.message.text)
        await update.message.reply_text("Jetzt bitte gewünschten ROI in Prozent (z. B. 10):")
        return START_ROI
    except:
        await update.message.reply_text("❌ Ungültige Eingabe. Bitte Zahl senden.")
        return START_WR

async def own_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        own_filters["roi"] = int(update.message.text)
        await update.message.reply_text(f"✅ Eigene Filter gesetzt: WR ≥ {own_filters['wr']}%, ROI ≥ {own_filters['roi']}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Ungültige Eingabe. Bitte Zahl senden.")
        return START_ROI

async def smartfinder_scan():
    wallet_id = f"{random.randint(100000,999999)}abcde"
    message = build_wallet_message(wallet_id)
    keyboard = [[InlineKeyboardButton("Dann mal los", callback_data=f"track_{wallet_id}")]]
    await application.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_track_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    wallet_id = query.data.split("_")[1]
    wallets[wallet_id] = "🚀 AutoDetected"
    await query.answer()
    await query.edit_message_text(f"✅ Wallet <b>{wallet_id}</b> wird jetzt getrackt.", parse_mode=ParseMode.HTML)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, tag = context.args[0], " ".join(context.args[1:])
        wallets[wallet] = tag
        await update.message.reply_text(f"✅ Wallet {wallet} hinzugefügt.")
    except:
        await update.message.reply_text("❌ Nutzung: /add WALLET TAG")

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in wallets:
            del wallets[wallet]
            await update.message.reply_text(f"❌ Wallet {wallet} entfernt.")
        else:
            await update.message.reply_text("Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❌ Nutzung: /rm WALLET")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not wallets:
        await update.message.reply_text("📭 Keine Wallets getrackt.")
        return
    msg = "<b>📋 Getrackte Wallets:</b>\n\n"
    for w, t in wallets.items():
        p = profit_data.get(w, 0)
        color = "🟢" if p >= 0 else "🔴"
        wr = f"{random.randint(60,95)}%"
        msg += f"{w} ({t})\nWR({wr}) | PnL({color}{abs(p)} SOL)\n\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, amount = context.args[0], context.args[1]
        if wallet not in wallets:
            await update.message.reply_text("Wallet nicht getrackt.")
            return
        value = float(amount.replace("+", "").replace("SOL", ""))
        profit_data[wallet] = profit_data.get(wallet, 0) + value
        await update.message.reply_text(f"✅ PnL für {wallet}: {profit_data[wallet]} SOL")
    except:
        await update.message.reply_text("❌ Nutzung: /profit WALLET +/-BETRAG")
    
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unbekannter Befehl.")

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler, pattern="^(smartfinder|moonbags|scalping|own)$"))
application.add_handler(CallbackQueryHandler(handle_track_wallet, pattern="^track_"))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("rm", rm))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit))
application.add_handler(MessageHandler(filters.COMMAND, unknown))

application.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="^own$")],
    states={
        START_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr)],
        START_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi)],
    },
    fallbacks=[],
))

scheduler = AsyncIOScheduler()
scheduler.add_job(smartfinder_scan, IntervalTrigger(minutes=30))
scheduler.start()

if __name__ == "__main__":
    import uvicorn
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        webhook_url=WEBHOOK_URL,
    )