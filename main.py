import os
import json
import logging
import httpx
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ConversationHandler, ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL")

wallets = {}
user_filters = {}
smartfinder_mode = None

logging.basicConfig(level=logging.INFO)
fastapi_app = FastAPI()
scheduler = AsyncIOScheduler()

application = Application.builder().token(BOT_TOKEN).build()

# --- STATE HANDLER IDs ---
WINRATE, ROI = range(2)

# --- Webhook Route ---
@fastapi_app.post("/" + BOT_TOKEN)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application._bot)
    await application.update_queue.put(update)
    return {"ok": True}

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 Wallet-Liste", callback_data="list_wallets")],
        [InlineKeyboardButton("📈 Profit manuell setzen", callback_data="manual_profit")],
        [InlineKeyboardButton("🧠 SmartFinder starten", callback_data="smartfinder")],
    ]
    await update.message.reply_text("Willkommen beim 🧠 RobertsSolTrackerBot", reply_markup=InlineKeyboardMarkup(keyboard))

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Verwendung: /add <WALLET> <TAG>")
        return
    wallet, tag = args[0], " ".join(args[1:])
    wallets[wallet] = {"tag": tag, "pnl": 0.0, "wins": 0, "losses": 0}
    await context.bot.send_message(chat_id=CHANNEL_ID, text=f"👀 Tracking gestartet für: `{wallet}`\n🏷️ {tag}", parse_mode="Markdown")

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Verwendung: /rm <WALLET>")
        return
    wallet = args[0]
    if wallet in wallets:
        del wallets[wallet]
        await update.message.reply_text(f"✅ {wallet} entfernt.")
    else:
        await update.message.reply_text("Wallet nicht gefunden.")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not wallets:
        await update.message.reply_text("Keine Wallets getrackt.")
        return
    text = ""
    for wallet, data in wallets.items():
        pnl_color = "🟢" if data["pnl"] >= 0 else "🔴"
        wr_color = "🟢" if data["wins"] >= data["losses"] else "🔴"
        wr_total = data["wins"] + data["losses"]
        wr_display = f"{wr_color} WR({data['wins']}/{wr_total})"
        text += f"🏷️ {data['tag']}\n🔗 `{wallet}`\n{wr_display} | {pnl_color} PnL({data['pnl']:.2f} sol)\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def set_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Verwendung: /profit <wallet> <+/-betrag>")
        return
    wallet, value = args[0], args[1]
    try:
        amount = float(value)
    except ValueError:
        await update.message.reply_text("Ungültiger Betrag.")
        return
    if wallet not in wallets:
        await update.message.reply_text("Wallet nicht gefunden.")
        return
    wallets[wallet]["pnl"] += amount
    if amount >= 0:
        wallets[wallet]["wins"] += 1
    else:
        wallets[wallet]["losses"] += 1
    await update.message.reply_text(f"✅ PnL für {wallet} aktualisiert.")

# --- SmartFinder ---
async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Moonbags", callback_data="mode_moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
        [InlineKeyboardButton("🔧 Own Filter", callback_data="mode_own")],
    ]
    await update.callback_query.message.reply_text("Wähle SmartFinder-Modus:", reply_markup=InlineKeyboardMarkup(keyboard))

async def own_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Eigener Modus aktiv.\nGib Mindest-Winrate ein (z. B. 60%)")
    return WINRATE

async def winrate_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.replace("%", ""))
        user_filters["winrate"] = wr
        await update.message.reply_text("Gib nun Mindest-ROI ein (z. B. 10%)")
        return ROI
    except:
        await update.message.reply_text("Bitte gültige Zahl eingeben.")
        return WINRATE

async def roi_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.replace("%", ""))
        user_filters["roi"] = roi
        global smartfinder_mode
        smartfinder_mode = "own"
        await update.message.reply_text(f"✅ Eigener SmartFinder aktiv: WR ≥ {user_filters['winrate']}% | ROI ≥ {roi}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("Bitte gültige Zahl eingeben.")
        return ROI

# --- SmartFinder Worker ---
async def auto_discover_wallets():
    logging.info("🔎 Running SmartFinder...")
    found = [
        {"wallet": "SmartWallet1", "wr": 70, "roi": 12.3, "sol": 4.1, "tag": "🚀 Auto"},
        {"wallet": "SmartWallet2", "wr": 62, "roi": 9.4, "sol": 1.7, "tag": "🚀 Auto"},
    ]
    for wallet in found:
        wr_min = user_filters.get("winrate", 60)
        roi_min = user_filters.get("roi", 5)
        if wallet["wr"] >= wr_min and wallet["roi"] >= roi_min:
            if wallet["wallet"] not in wallets:
                wallets[wallet["wallet"]] = {
                    "tag": wallet["tag"],
                    "pnl": 0.0,
                    "wins": 0,
                    "losses": 0
                }
                text = f"🎯 Smart Wallet entdeckt!\n\n🔗 `{wallet['wallet']}`\n📊 WR: {wallet['wr']}% | ROI: {wallet['roi']}% | Balance: {wallet['sol']} sol\n🏷️ {wallet['tag']}"
                keyboard = [[InlineKeyboardButton("Jetzt tracken ✅", callback_data=f"track_{wallet['wallet']}")]]
                await application.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "add_wallet":
        await query.message.reply_text("Nutze `/add <wallet> <tag>`")
    elif data == "list_wallets":
        await list_wallets(update, context)
    elif data == "manual_profit":
        await query.message.reply_text("Nutze `/profit <wallet> <+/-betrag>`")
    elif data == "smartfinder":
        await smartfinder_menu(update, context)
    elif data.startswith("mode_"):
        mode = data.split("_")[1]
        global smartfinder_mode
        if mode == "own":
            return await own_start(update, context)
        smartfinder_mode = mode
        await query.message.reply_text(f"✅ SmartFinder-Modus aktiviert: {mode.upper()}")
    elif data.startswith("track_"):
        wallet = data.split("_", 1)[1]
        wallets[wallet] = {"tag": "🚀 Auto", "pnl": 0.0, "wins": 0, "losses": 0}
        await query.message.reply_text(f"✅ Tracking für {wallet} aktiviert.")

# --- Scheduler Setup ---
scheduler.add_job(auto_discover_wallets, trigger=IntervalTrigger(minutes=30))
scheduler.start()
logging.info("✅ Scheduler gestartet")

# --- Handlers registrieren ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("rm", rm))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", set_profit))
application.add_handler(CallbackQueryHandler(button_handler))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(own_start, pattern="mode_own")],
    states={
        WINRATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, winrate_input)],
        ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, roi_input)],
    },
    fallbacks=[],
)
application.add_handler(conv_handler)

# --- Start Webhook ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)