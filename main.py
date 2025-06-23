import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes,
    CallbackQueryHandler, ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("RailwayStaticUrl") + "/" + TOKEN

app = FastAPI()
application = Application.builder().token(TOKEN).build()

wallets = {}
profit_data = {}
user_filters = {}
scanner_enabled = False

MIN_WINRATE, MIN_ROI = range(2)

# Dummy Smart Wallets
dummy_wallets = [
    {"address": "SoLWin123", "winrate": 65, "roi": 12, "pnl": 2.5, "age": 19, "tag": "🚀 AutoDetected"},
    {"address": "MoonBagz1", "winrate": 78, "roi": 25, "pnl": 4.1, "age": 51, "tag": "🌕 Moonbags"},
]

@app.post(f"/{TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

@application.on_startup
async def startup(_: Application):
    await application.bot.set_webhook(url=WEBHOOK_URL)

def wallet_stats(wallet):
    wins = profit_data.get(wallet, {}).get("wins", 0)
    losses = profit_data.get(wallet, {}).get("losses", 0)
    pnl = profit_data.get(wallet, {}).get("pnl", 0)
    pnl_color = "🟢" if pnl >= 0 else "🔴"
    return f"WR({wins}/{losses}) | PnL({pnl_color} {abs(pnl):.2f} sol)"

def track_wallet(address, tag):
    if address not in wallets:
        wallets[address] = tag
        profit_data[address] = {"wins": 0, "losses": 0, "pnl": 0}
        return True
    return False

async def send_wallet_discovery(wallet):
    text = (
        f"💡 *Neue Smart Wallet entdeckt!*\n"
        f"• Wallet: `{wallet['address']}`\n"
        f"• Tag: {wallet['tag']}\n"
        f"• WR: {wallet['winrate']}%\n"
        f"• ROI: {wallet['roi']}%\n"
        f"• Age: {wallet['age']} Tage\n"
        f"• PnL: {wallet['pnl']} sol"
    )
    keyboard = [[InlineKeyboardButton("✅ Tracken", callback_data=f"track:{wallet['address']}|{wallet['tag']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await application.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown", reply_markup=reply_markup)

async def smart_wallet_scan():
    if not scanner_enabled:
        return
    for wallet in dummy_wallets:
        min_wr = user_filters.get("min_wr", 60)
        min_roi = user_filters.get("min_roi", 5)
        if wallet["winrate"] >= min_wr and wallet["roi"] >= min_roi:
            if wallet["address"] not in wallets:
                track_wallet(wallet["address"], wallet["tag"])
                await send_wallet_discovery(wallet)

@application.job_queue.run_repeating(interval=1800, first=10)
async def run_scanner(context: ContextTypes.DEFAULT_TYPE):
    await smart_wallet_scan()

@application.command_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📜 List", callback_data="list")],
        [InlineKeyboardButton("➕ Profit", callback_data="profit")],
        [InlineKeyboardButton("🧠 SmartFinder", callback_data="smartfinder")]
    ]
    await update.message.reply_text("Willkommen beim SolTrackerBot!", reply_markup=InlineKeyboardMarkup(keyboard))

@application.callback_query_handler
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "list":
        await cmd_list(update, context)
    elif data == "profit":
        await update.callback_query.message.reply_text("Nutze /profit <wallet> <+/-betrag>")
    elif data == "smartfinder":
        keyboard = [
            [InlineKeyboardButton("🌕 Moonbags", callback_data="moonbags")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="scalping")],
            [InlineKeyboardButton("⚙️ Own", callback_data="own")]
        ]
        await update.callback_query.message.reply_text("Wähle Modus:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("track:"):
        addr, tag = data.split(":")[1].split("|")
        if track_wallet(addr, tag):
            await update.callback_query.message.reply_text(f"✅ Tracking gestartet für {addr}")
        else:
            await update.callback_query.message.reply_text(f"🔁 {addr} wird bereits getrackt.")

@application.command_handler
async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📋 Getrackte Wallets:\n"
    for w, tag in wallets.items():
        msg += f"• `{w}` – {tag}\n  {wallet_stats(w)}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

@application.command_handler
async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2 or args[1][0] not in "+-":
        await update.message.reply_text("❗ Format: /profit <wallet> <+/-betrag>")
        return
    wallet = args[0]
    amount = float(args[1])
    if wallet not in profit_data:
        profit_data[wallet] = {"wins": 0, "losses": 0, "pnl": 0}
    profit_data[wallet]["pnl"] += amount
    if amount > 0:
        profit_data[wallet]["wins"] += 1
    else:
        profit_data[wallet]["losses"] += 1
    await update.message.reply_text(f"💰 Profit aktualisiert: {wallet_stats(wallet)}")

@application.command_handler
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Format: /add <wallet> <tag>")
        return
    address, tag = context.args
    if track_wallet(address, tag):
        await update.message.reply_text(f"✅ Wallet {address} getrackt mit Tag: {tag}")
    else:
        await update.message.reply_text("🔁 Diese Wallet wird bereits getrackt.")

@application.command_handler
async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /rm <wallet>")
        return
    wallet = context.args[0]
    if wallet in wallets:
        del wallets[wallet]
        await update.message.reply_text("❌ Wallet entfernt.")
    else:
        await update.message.reply_text("Wallet nicht gefunden.")

@application.conversation_handler(
    entry_points=[CallbackQueryHandler(lambda u, c: u.data == "own", pattern="own"), CommandHandler("own", lambda u, c: u.message.reply_text("Min. Winrate (z. B. 60%)?") or MIN_WINRATE)],
    states={
        MIN_WINRATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_winrate(u, c))],
        MIN_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_roi(u, c))]
    },
    fallbacks=[]
)
async def handle_winrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.replace("%", ""))
        user_filters["min_wr"] = wr
        await update.message.reply_text("Min. ROI (z. B. 10%)?")
        return MIN_ROI
    except:
        await update.message.reply_text("❌ Ungültige Zahl.")
        return MIN_WINRATE

async def handle_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.replace("%", ""))
        user_filters["min_roi"] = roi
        global scanner_enabled
        scanner_enabled = True
        await update.message.reply_text(f"✅ Filter gesetzt. Scanner aktiv!")
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Ungültige Zahl.")
        return MIN_ROI

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)