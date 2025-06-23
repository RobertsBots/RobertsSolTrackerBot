import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ========== DATENSPEICHERUNG ==========

tracked_wallets = {}  # wallet: tag
manual_profits = {}   # wallet: float
winloss_stats = {}    # wallet: {"win": int, "loss": int}
user_filters = {"wr": 60, "roi": 10}
scanner_active = False

# ========== FASTAPI SETUP ==========

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # ✅ DEINE CHANNEL_ID
STATIC_URL = os.getenv("RailwayStaticUrl")
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"{STATIC_URL}{WEBHOOK_PATH}"

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()
scheduler = AsyncIOScheduler()

# ========== BUTTONS & KEYBOARDS ==========

def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_help")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_help")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder")]
    ])

def get_smartfinder_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Moonbags", callback_data="mode_moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
        [InlineKeyboardButton("🔧 Own", callback_data="mode_own")]
    ])

# ========== BEFEHLE ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Willkommen beim Solana Wallet Tracker Bot!\nWähle unten eine Funktion:",
        reply_markup=get_main_buttons(),
        parse_mode=ParseMode.HTML
    )

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) == 3:
        wallet, tag = parts[1], parts[2]
        tracked_wallets[wallet] = tag
        winloss_stats[wallet] = {"win": 0, "loss": 0}
        await update.message.reply_text(f"✅ Wallet <code>{wallet}</code> mit Tag <b>{tag}</b> hinzugefügt.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("⚠️ Format: /add WALLET TAG")

async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) == 2:
        wallet = parts[1]
        if wallet in tracked_wallets:
            del tracked_wallets[wallet]
            manual_profits.pop(wallet, None)
            winloss_stats.pop(wallet, None)
            await update.message.reply_text(f"🗑️ Wallet <code>{wallet}</code> entfernt.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text("❌ Wallet nicht gefunden.")
    else:
        await update.message.reply_text("⚠️ Format: /rm WALLET")

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) == 3:
        wallet, profit_str = parts[1], parts[2]
        if wallet not in tracked_wallets:
            await update.message.reply_text("❌ Diese Wallet wird nicht getrackt.")
            return
        if profit_str.startswith("+") or profit_str.startswith("-"):
            try:
                profit_value = float(profit_str)
                manual_profits[wallet] = profit_value
                await update.message.reply_text(f"💰 Profit für <code>{wallet}</code>: <b>{profit_value} sol</b>", parse_mode=ParseMode.HTML)
            except ValueError:
                await update.message.reply_text("❌ Ungültiger Betrag. Beispiel: /profit WALLET +12.3")
        else:
            await update.message.reply_text("⚠️ Format: /profit WALLET +/-BETRAG")
    else:
        await update.message.reply_text("⚠️ Format: /profit WALLET +/-BETRAG")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await update.message.reply_text("ℹ️ Keine Wallets getrackt.")
        return

    msg = "📋 <b>Getrackte Wallets:</b>\n"
    for idx, (wallet, tag) in enumerate(tracked_wallets.items(), 1):
        link = f"https://birdeye.so/address/{wallet}?chain=solana"
        profit = manual_profits.get(wallet, 0.0)
        stats = winloss_stats.get(wallet, {"win": 0, "loss": 0})
        wr = f"<b>WR(</b><span style='color:green'>{stats['win']}</span>/<span style='color:red'>{stats['loss']}</span><b>)</b>"
        pnl = f"<b> | PnL(</b><span style='color:{'green' if profit >= 0 else 'red'}'>{profit:.2f} sol</span><b>)</b>"
        msg += f"\n<b>{idx}.</b> <a href='{link}'>{wallet}</a> – <i>{tag}</i>\n{wr}{pnl}\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# ========== CALLBACKS & SMARTFINDER PLACEHOLDER ==========

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat.id

    if data == "add_help":
        await query.edit_message_text("📥 Um eine Wallet hinzuzufügen:\n<code>/add WALLET TAG</code>", parse_mode=ParseMode.HTML)
    elif data == "list":
        await list_wallets(update, context)
    elif data == "profit_help":
        await query.edit_message_text("➕ Um Profit einzutragen:\n<code>/profit WALLET +/-BETRAG</code>", parse_mode=ParseMode.HTML)
    elif data == "smartfinder":
        await query.edit_message_text("🧠 Wähle deinen Modus:", reply_markup=get_smartfinder_buttons())
    elif data.startswith("mode_"):
        mode = data.replace("mode_", "")
        await query.edit_message_text(f"✅ Modus <b>{mode.capitalize()}</b> aktiviert.\nSmartFinder wird nun alle 30 Minuten nach passenden Wallets suchen.", parse_mode=ParseMode.HTML)

# ========== STARTUP & WEBHOOK ==========

@app.on_event("startup")
async def on_startup():
    scheduler.start()
    await application.bot.set_webhook(WEBHOOK_URL)

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# ========== BOT HANDLER REGISTRIERUNG ==========

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", remove_wallet))
application.add_handler(CommandHandler("profit", profit))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CallbackQueryHandler(callback_handler))

# ========== STARTEN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)