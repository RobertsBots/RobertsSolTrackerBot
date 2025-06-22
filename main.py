import os
import json
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ContextTypes, ConversationHandler
)
from dotenv import load_dotenv

# 🔧 Logging
logging.basicConfig(level=logging.INFO)

# 🌐 Load env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. "https://deinprojekt.up.railway.app/webhook"

# 📦 Datenhaltung
tracked_wallets = {}  # wallet: {"tag": ..., "pnl": ..., "wr": (x, y)}
own_filters = {"wr": 60, "roi": 10}
scanner_active = False

# ⚙️ FastAPI Init
app = FastAPI()

# 🤖 Telegram Init
application = Application.builder().token(TOKEN).build()

# 🟣 States
WR_INPUT, ROI_INPUT = range(2)

# 📩 Webhook-Route
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list_wallets")],
        [InlineKeyboardButton("🗑️ Wallet entfernen", callback_data="remove_wallet")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_wallet")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Willkommen beim TrackerBot!", reply_markup=reply_markup)


# 📜 /list
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await update.message.reply_text("Noch keine Wallets getrackt.")
        return
    for wallet, data in tracked_wallets.items():
        x, y = data.get("wr", (0, 0))
        pnl = data.get("pnl", 0)
        wr_str = f"WR({x}/{y})"
        pnl_str = f"PnL(+{pnl} sol)" if pnl >= 0 else f"PnL(-{abs(pnl)} sol)"
        msg = f"💼 {wallet} [{data['tag']}]\n{wr_str} | {pnl_str}"
        await update.message.reply_text(msg)


# ➕ /add
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, tag = context.args[0], context.args[1]
        tracked_wallets[wallet] = {"tag": tag, "pnl": 0, "wr": (0, 0)}
        await update.message.reply_text(f"✅ Wallet {wallet} mit Tag '{tag}' getrackt.")
    except:
        await update.message.reply_text("❌ Nutzung: /add <WALLET> <TAG>")


# ❌ /rm
async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in tracked_wallets:
            del tracked_wallets[wallet]
            await update.message.reply_text(f"🗑️ Wallet {wallet} entfernt.")
        else:
            await update.message.reply_text("❌ Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❌ Nutzung: /rm <WALLET>")


# 💸 /profit
async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, amount = context.args[0], context.args[1]
        if wallet not in tracked_wallets:
            await update.message.reply_text("❌ Wallet nicht getrackt.")
            return
        if not amount.startswith(("+", "-")):
            await update.message.reply_text("Bitte + oder - vor dem Betrag angeben.")
            return
        val = float(amount)
        tracked_wallets[wallet]["pnl"] += val
        await update.message.reply_text(f"📈 Neuer PnL für {wallet}: {tracked_wallets[wallet]['pnl']} sol")
    except:
        await update.message.reply_text("❌ Nutzung: /profit <wallet> <+/-betrag>")


# 🧠 Smart Finder Menü
async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌕 Moonbags", callback_data="mode_moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
        [InlineKeyboardButton("🛠️ Own", callback_data="mode_own")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Wähle einen SmartFinder-Modus:", reply_markup=reply_markup)


# ⚙️ /own Dialog
async def own_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🛠️ Gib deine gewünschte Mindest-Winrate (%) ein:")
    return WR_INPUT

async def wr_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(str(update.message.text).replace("%", ""))
        context.user_data["wr"] = wr
        await update.message.reply_text("🔧 Gib deinen gewünschten Mindest-ROI (%) ein:")
        return ROI_INPUT
    except:
        await update.message.reply_text("❌ Bitte gültige Zahl eingeben.")
        return WR_INPUT

async def roi_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(str(update.message.text).replace("%", ""))
        own_filters["wr"] = context.user_data["wr"]
        own_filters["roi"] = roi
        await update.message.reply_text(f"✅ Filter gesetzt: WR ≥ {own_filters['wr']}%, ROI ≥ {own_filters['roi']}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Bitte gültige Zahl eingeben.")
        return ROI_INPUT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Abgebrochen.")
    return ConversationHandler.END


# 📡 Dummy Scanner
async def scan_wallets():
    while True:
        if scanner_active:
            # Hier würdest du echte API Calls zu Dune oder Birdeye machen
            example_wallet = "ABC123"
            wr, roi, pnl = 75, 22, 3.5
            tokens_7d, tokens_all, tokens_hodl = 17, 48, 6
            account_age = "142d"
            balance = "12.4 SOL"
            link = f"https://birdeye.so/address/{example_wallet}?chain=solana"

            msg = (
                f"🔍 <a href='{link}'>{example_wallet}</a> – {balance} – {account_age}\n"
                f"📈 WinRate: {wr}% | ROI: {roi}% | 7d PnL: +{pnl} sol\n"
                f"📊 7d Tokens: {tokens_7d} | All Tokens: {tokens_all} | Hodl Tokens: {tokens_hodl}\n"
                f"💰 Lifetime PnL: +{pnl} sol"
            )
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("Dann mal los 🚀", callback_data=f"track_{example_wallet}")]
            ])
            await application.bot.send_message(
                chat_id=CHANNEL_ID, text=msg, parse_mode="HTML", reply_markup=button
            )
        await asyncio.sleep(1800)  # alle 30 Minuten


# 🧲 Track via Button
async def track_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    wallet = query.data.split("_")[1]
    tracked_wallets[wallet] = {"tag": "🚀 AutoDetected", "pnl": 0, "wr": (0, 0)}
    await query.edit_message_text(f"🎯 Wallet {wallet} wird jetzt getrackt.")


# 🧠 Button Routing
async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "list_wallets":
        await list_wallets(query, context)
    elif query.data == "remove_wallet":
        await query.message.reply_text("Nutze /rm <WALLET>")
    elif query.data == "profit_wallet":
        await query.message.reply_text("Nutze /profit <wallet> <+/-betrag>")
    elif query.data == "smartfinder_menu":
        await smartfinder_menu(update, context)
    elif query.data == "mode_moonbags":
        own_filters["wr"], own_filters["roi"] = 60, 30
        await query.edit_message_text("🌕 Moonbag-Modus aktiviert!")
    elif query.data == "mode_scalping":
        own_filters["wr"], own_filters["roi"] = 70, 10
        await query.edit_message_text("⚡ Scalping-Modus aktiviert!")
    elif query.data == "mode_own":
        return await own_entry(update, context)
    elif query.data.startswith("track_"):
        await track_wallet_callback(update, context)


# 🚀 Setup
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("rm", rm))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit))
application.add_handler(CallbackQueryHandler(button_router))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(own_entry, pattern="mode_own")],
    states={
        WR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, wr_input)],
        ROI_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, roi_input)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False
)
application.add_handler(conv_handler)

# 🛰️ Webhook starten
@app.on_event("startup")
async def on_startup():
    await application.bot.set_webhook(url=WEBHOOK_URL)
    asyncio.create_task(scan_wallets())
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

@app.on_event("shutdown")
async def on_shutdown():
    await application.updater.stop()
    await application.stop()
    await application.shutdown()