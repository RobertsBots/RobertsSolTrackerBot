import os
import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
RAILWAY_STATIC_URL = os.environ.get("RAILWAY_STATIC_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tracked_wallets = {}
wallet_stats = {}
user_filters = {}

fastapi_app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# ==== /start ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Wallet hinzufügen ➕", callback_data='add_wallet')],
        [InlineKeyboardButton("SmartFinder 🧠", callback_data='smartfinder')],
        [InlineKeyboardButton("Profit eintragen 💰", callback_data='enter_profit')],
        [InlineKeyboardButton("Getrackte Wallets 📋", callback_data='list_wallets')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Willkommen beim TrackerBot 👋", reply_markup=reply_markup)

# ==== /add ====
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Verwendung: /add <WALLET> <TAG>")
        return
    wallet, tag = context.args
    tracked_wallets[wallet] = tag
    wallet_stats[wallet] = {'wins': 0, 'losses': 0, 'pnl': 0}
    await update.message.reply_text(f"✅ Wallet {wallet} ({tag}) hinzugefügt.")

# ==== /rm ====
async def rm_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Verwendung: /rm <WALLET>")
        return
    wallet = context.args[0]
    if wallet in tracked_wallets:
        del tracked_wallets[wallet]
        wallet_stats.pop(wallet, None)
        await update.message.reply_text(f"❌ Wallet {wallet} entfernt.")
    else:
        await update.message.reply_text("Wallet nicht gefunden.")

# ==== /list ====
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await update.message.reply_text("Keine Wallets getrackt.")
        return
    text = "📊 Getrackte Wallets:\n\n"
    for wallet, tag in tracked_wallets.items():
        stats = wallet_stats.get(wallet, {'wins': 0, 'losses': 0, 'pnl': 0})
        wr = f"{stats['wins']}/{stats['wins'] + stats['losses']}"
        pnl = stats['pnl']
        wr_display = f"WR({wr})"
        pnl_display = f"PnL({pnl:+.2f} sol)"
        text += f"🧠 {tag}\n{wallet}\n{wr_display} {pnl_display}\n\n"
    await update.message.reply_text(text)

# ==== /profit ====
async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Verwendung: /profit <WALLET> <+/-BETRAG>")
        return
    wallet, amount_str = context.args
    try:
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("Ungültiger Betrag.")
        return
    if wallet not in wallet_stats:
        wallet_stats[wallet] = {'wins': 0, 'losses': 0, 'pnl': 0}
    wallet_stats[wallet]['pnl'] += amount
    if amount > 0:
        wallet_stats[wallet]['wins'] += 1
    else:
        wallet_stats[wallet]['losses'] += 1
    await update.message.reply_text(f"📈 Profit für {wallet} aktualisiert: {amount:+.2f} sol")

# ==== SmartFinder Menü ====
async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Moonbags", callback_data='moonbags')],
        [InlineKeyboardButton("⚡ Scalping", callback_data='scalping')],
        [InlineKeyboardButton("🎯 Own", callback_data='own')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text("SmartFinder Menü:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("SmartFinder Menü:", reply_markup=reply_markup)

# ==== /own Dialog ====
SET_WR, SET_ROI = range(2)

async def own_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Eigene Mindest-Winrate (%) eingeben:")
    return SET_WR

async def set_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.strip().replace("%", ""))
        context.user_data['wr'] = wr
        await update.message.reply_text("Mindest-ROI (%) eingeben:")
        return SET_ROI
    except:
        await update.message.reply_text("Bitte gültige Zahl eingeben.")
        return SET_WR

async def set_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.strip().replace("%", ""))
        user_id = update.message.from_user.id
        user_filters[user_id] = {'wr': context.user_data['wr'], 'roi': roi}
        await update.message.reply_text(f"✅ Eigene Filter gesetzt: WR ≥ {context.user_data['wr']}%, ROI ≥ {roi}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("Bitte gültige Zahl eingeben.")
        return SET_ROI

# ==== Auto-Discovery Dummy Funktion ====
async def auto_discover_wallets():
    dummy_wallet = f"DummyWallet_{datetime.utcnow().timestamp()}"
    tag = "🚀 AutoDetected"
    tracked_wallets[dummy_wallet] = tag
    wallet_stats[dummy_wallet] = {'wins': 1, 'losses': 0, 'pnl': 1.23}
    msg = f"📡 Neue Wallet entdeckt:\n{dummy_wallet}\nTag: {tag}\nWR(1/1) PnL(+1.23 sol)"
    await application.bot.send_message(chat_id=CHANNEL_ID, text=msg)

# ==== Scheduler ====
scheduler = AsyncIOScheduler()
scheduler.add_job(auto_discover_wallets, 'interval', minutes=30)
scheduler.start()

# ==== Webhook-Handler ====
@fastapi_app.post("/" + BOT_TOKEN)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# ==== Handler Registrieren ====
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", rm_wallet))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit))
application.add_handler(CommandHandler("smartfinder", smartfinder_menu))
application.add_handler(CallbackQueryHandler(smartfinder_menu, pattern="smartfinder"))
application.add_handler(CallbackQueryHandler(own_callback, pattern="own"))
application.add_handler(CallbackQueryHandler(add_wallet, pattern="add_wallet"))
application.add_handler(CallbackQueryHandler(list_wallets, pattern="list_wallets"))
application.add_handler(CallbackQueryHandler(profit, pattern="enter_profit"))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(own_callback, pattern="own")],
    states={
        SET_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_wr)],
        SET_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_roi)],
    },
    fallbacks=[],
)
application.add_handler(conv_handler)

# ==== Start ====
if __name__ == "__main__":
    import uvicorn
    asyncio.get_event_loop().create_task(application.initialize())
    asyncio.get_event_loop().create_task(application.start())
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)