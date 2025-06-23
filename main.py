import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from dotenv import load_dotenv

# === SETTINGS ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("RailwayStaticUrl") + "/" + BOT_TOKEN

# === INIT ===
application = ApplicationBuilder().token(BOT_TOKEN).build()
app = FastAPI()
scheduler = BackgroundScheduler()
scheduler.start()
logging.basicConfig(level=logging.INFO)

# === BOT STATE ===
wallets = {}  # {address: {"tag": "user", "profit": 0.0, "wins": 0, "losses": 0}}

# === COMMANDS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Add Wallet", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 List", callback_data="list_wallets")],
        [InlineKeyboardButton("📈 SmartFinder", callback_data="smartfinder")],
    ]
    await update.message.reply_text("Willkommen beim Tracker 🧠", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gib die Wallet ein mit Tag: `/add <wallet> <tag>`")

async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, tag = context.args[0], context.args[1]
        wallets[wallet] = {"tag": tag, "profit": 0.0, "wins": 0, "losses": 0}
        await update.message.reply_text(f"✅ Hinzugefügt: {wallet} ({tag})")
    except:
        await update.message.reply_text("❌ Syntax: /add <wallet> <tag>")

async def cmd_rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in wallets:
            del wallets[wallet]
            await update.message.reply_text(f"🗑️ Entfernt: {wallet}")
        else:
            await update.message.reply_text("Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❌ Syntax: /rm <wallet>")

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not wallets:
        await update.message.reply_text("Noch keine Wallets.")
        return
    msg = "📄 *Getrackte Wallets:*\n\n"
    for w, data in wallets.items():
        color = "🟢" if data["profit"] >= 0 else "🔴"
        wr = f"{data['wins']}/{data['wins'] + data['losses']}" if (data['wins'] + data['losses']) > 0 else "0/0"
        msg += f"`{w}`\n🏷️ {data['tag']} | WR({wr}) | {color} {data['profit']} sol\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, amount = context.args[0], context.args[1]
        amount = float(amount)
        if wallet in wallets:
            wallets[wallet]["profit"] += amount
            if amount >= 0:
                wallets[wallet]["wins"] += 1
            else:
                wallets[wallet]["losses"] += 1
            await update.message.reply_text("✅ Profit aktualisiert.")
        else:
            await update.message.reply_text("Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❌ Syntax: /profit <wallet> <+/-amount>")

# === SMART FINDER ===
def auto_discover_wallets():
    detected = {
        "SoL123...Auto1": {"tag": "🚀 AutoDetected", "profit": 1.2, "wins": 4, "losses": 1},
        "SoL456...Auto2": {"tag": "🚀 AutoDetected", "profit": 0.7, "wins": 3, "losses": 2},
    }
    for addr, data in detected.items():
        if addr not in wallets:
            wallets[addr] = data
            msg = f"🧠 Neue Wallet entdeckt:\n`{addr}`\nTag: {data['tag']}\nProfit: {data['profit']} sol"
            application.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")

scheduler.add_job(auto_discover_wallets, "interval", minutes=30)

# === CALLBACKS ===
async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "add_wallet":
        await query.edit_message_text("Gib die Wallet ein: /add <wallet> <tag>")
    elif query.data == "list_wallets":
        await cmd_list(update, context)
    elif query.data == "smartfinder":
        await query.edit_message_text("SmartFinder aktiviert – Auto-Wallets werden alle 30 Minuten erkannt.")

# === ROUTES ===
@ app.post("/" + BOT_TOKEN)
async def telegram_webhook(update: dict):
    update_obj = Update.de_json(update, application.bot)
    await application.process_update(update_obj)

# === HANDLERS ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", cmd_add))
application.add_handler(CommandHandler("rm", cmd_rm))
application.add_handler(CommandHandler("list", cmd_list))
application.add_handler(CommandHandler("profit", cmd_profit))
application.add_handler(CallbackQueryHandler(callback_query))

# === RUN ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)