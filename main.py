import os
import json
import asyncio
import random
from fastapi import FastAPI
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# Env
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://dein-bot.up.railway.app/")

# FastAPI Setup
app = FastAPI()

# Telegram Bot Setup
application = Application.builder().token(BOT_TOKEN).build()

# SmartFinder Status
SCANNER_MODES = {
    "moonbags": {"wr": 60, "roi": 25},
    "scalping": {"wr": 70, "roi": 10},
    "own": {"wr": None, "roi": None}
}
current_mode = None
scanner_active = False
tracked_wallets = {}
own_filters = {"wr": None, "roi": None}

# Dummy SmartWallets
def get_dummy_wallets():
    return [
        {
            "wallet": "4xyzABC123...mn", "sol": 22.5, "age": "120d",
            "wr": 66, "roi": 32, "pnl": "+41", "tokens7d": 8,
            "tokensTotal": 42, "hodl": 5, "lifetime": "+97"
        },
        {
            "wallet": "7qrsLMN555...yz", "sol": 13.8, "age": "40d",
            "wr": 61, "roi": 18, "pnl": "+17", "tokens7d": 4,
            "tokensTotal": 11, "hodl": 2, "lifetime": "+31"
        },
    ]

# Speicherung
def save_data():
    with open("wallets.json", "w") as f:
        json.dump(tracked_wallets, f)

def load_data():
    global tracked_wallets
    if os.path.exists("wallets.json"):
        with open("wallets.json") as f:
            tracked_wallets = json.load(f)

@app.on_event("startup")
async def startup_event():
    load_data()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.bot.send_message(
        chat_id=CHANNEL_ID,
        text="✅ <b>RobertsSolTrackerBot ist bereit!</b>",
        parse_mode=ParseMode.HTML
    )

@app.post("/")
async def telegram_webhook(update: dict):
    await application.update_queue.put(Update.de_json(update, application.bot))

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📩 Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list_wallets")],
        [InlineKeyboardButton("🗑 Wallet entfernen", callback_data="remove_wallet")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="add_profit")],
        [InlineKeyboardButton("🚀 Smart Finder", callback_data="smart_finder")],
    ]
    await update.message.reply_text(
        "👋 Willkommen beim Solana Wallet Tracker!\nWähle unten eine Funktion aus:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# InlineButton Router
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd_map = {
        "add_wallet": "/add",
        "list_wallets": "/list",
        "remove_wallet": "/rm",
        "add_profit": "/profit",
        "smart_finder": "/smartfinder"
    }
    await query.message.chat.send_message(cmd_map[query.data])

# /add <wallet> <tag>
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, tag = context.args[0], context.args[1]
        tracked_wallets[wallet] = {"tag": tag, "pnl": 0.0, "wins": 0, "losses": 0}
        save_data()
        await update.message.reply_text(f"✅ Wallet {wallet} wurde als '{tag}' hinzugefügt.")
    except:
        await update.message.reply_text("❗️Format: /add <wallet> <tag>")

# /list
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await update.message.reply_text("📭 Noch keine Wallets getrackt.")
        return
    msg = ""
    for wallet, data in tracked_wallets.items():
        wr_total = data.get("wins", 0) + data.get("losses", 0)
        wr = f"WR({data.get('wins',0)}/{wr_total})"
        pnl = data.get("pnl", 0)
        pnl_str = f"<b>PnL({pnl:+.2f} sol)</b>"
        color = "🟢" if pnl >= 0 else "🔴"
        msg += f"{data['tag']}: {wallet}\n{wr} | {color} {pnl_str}\n\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# /rm <wallet>
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in tracked_wallets:
            del tracked_wallets[wallet]
            save_data()
            await update.message.reply_text(f"🗑 Wallet {wallet} entfernt.")
        else:
            await update.message.reply_text("❗️Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❗️Format: /rm <wallet>")

# /profit <wallet> <+/-betrag>
async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, amount = context.args[0], float(context.args[1])
        if wallet in tracked_wallets:
            tracked_wallets[wallet]["pnl"] += amount
            if amount >= 0:
                tracked_wallets[wallet]["wins"] += 1
            else:
                tracked_wallets[wallet]["losses"] += 1
            save_data()
            await update.message.reply_text(f"💰 Gewinn/Verlust von {amount:+.2f} sol eingetragen.")
        else:
            await update.message.reply_text("❗️Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❗️Format: /profit <wallet> <+/-betrag>")

# SmartFinder Buttons
async def smartfinder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌕 Moonbags", callback_data="set_moonbags")],
        [InlineKeyboardButton("⚡️ Scalping", callback_data="set_scalping")],
        [InlineKeyboardButton("⚙️ Own", callback_data="set_own")],
    ]
    await update.message.reply_text(
        "🔎 Wähle einen Filter-Modus für die Smart Wallet Suche:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Callback für SmartFinder
async def smartfinder_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_mode, scanner_active
    query = update.callback_query
    await query.answer()
    if query.data == "set_moonbags":
        current_mode = "moonbags"
        scanner_active = True
        await query.edit_message_text("✅ Moonbags-Modus aktiviert.")
    elif query.data == "set_scalping":
        current_mode = "scalping"
        scanner_active = True
        await query.edit_message_text("✅ Scalping-Modus aktiviert.")
    elif query.data == "set_own":
        current_mode = "own"
        scanner_active = True
        await query.edit_message_text("✅ Eigene Filter aktiviert. Bitte /own verwenden.")

# /own Interaktiv
OWN_WR, OWN_ROI = range(2)
async def own(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔧 Gib deine Mindest-Winrate ein (z.B. 60):")
    return OWN_WR

async def own_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    own_filters["wr"] = int(update.message.text)
    await update.message.reply_text("📈 Gib nun deinen Mindest-ROI ein (z.B. 15):")
    return OWN_ROI

async def own_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    own_filters["roi"] = int(update.message.text)
    await update.message.reply_text(f"✅ Eigene Filter gesetzt: WR ≥ {own_filters['wr']}%, ROI ≥ {own_filters['roi']}%")
    return ConversationHandler.END

# Automatischer Scanner
async def smart_wallet_scan(context: ContextTypes.DEFAULT_TYPE):
    if not scanner_active or not current_mode:
        return
    wallets = get_dummy_wallets()
    filters = SCANNER_MODES[current_mode]
    if current_mode == "own":
        filters = own_filters
    for w in wallets:
        if w["wr"] >= filters["wr"] and w["roi"] >= filters["roi"]:
            msg = (
                f"<b>{w['wallet']}</b> (<a href='https://birdeye.so/wallet/{w['wallet']}'>birdeye</a>) – {w['sol']} SOL – {w['age']}\n"
                f"📊 WR: {w['wr']}% | ROI: {w['roi']}% | 7d PnL: {w['pnl']} sol\n"
                f"📦 7d Tokens: {w['tokens7d']} | Total: {w['tokensTotal']} | Hodl: {w['hodl']}\n"
                f"📈 Lifetime PnL: {w['lifetime']}\n"
            )
            keyboard = [[InlineKeyboardButton("Dann mal los 🚀", callback_data=f"track_{w['wallet']}")]]
            await context.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode=ParseMode.HTML,
                                           reply_markup=InlineKeyboardMarkup(keyboard))

# Tracking Button für SmartWallet
async def track_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_id = update.callback_query.data.replace("track_", "")
    tracked_wallets[wallet_id] = {"tag": "🚀 AutoDetected", "pnl": 0.0, "wins": 0, "losses": 0}
    save_data()
    await update.callback_query.answer("Wallet wird jetzt getrackt!")
    await update.callback_query.edit_message_text(f"📥 Wallet {wallet_id} wurde getrackt.")

# Handler Setup
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("rm", remove))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit))
application.add_handler(CommandHandler("smartfinder", smartfinder))
application.add_handler(CommandHandler("moonbags", lambda u, c: smartfinder_buttons(u, c)))
application.add_handler(CommandHandler("scalping", lambda u, c: smartfinder_buttons(u, c)))
application.add_handler(CommandHandler("own", own))
application.add_handler(CallbackQueryHandler(button_handler, pattern="^(add_wallet|list_wallets|remove_wallet|add_profit|smart_finder)$"))
application.add_handler(CallbackQueryHandler(smartfinder_buttons, pattern="^(set_moonbags|set_scalping|set_own)$"))
application.add_handler(CallbackQueryHandler(track_wallet_callback, pattern="^track_"))

application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("own", own)],
    states={
        OWN_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr)],
        OWN_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi)],
    },
    fallbacks=[]
))

# Cronjob alle 30 Minuten
scheduler = AsyncIOScheduler()
scheduler.add_job(lambda: smart_wallet_scan(application), 'interval', minutes=30)
scheduler.start()

# Start App
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)