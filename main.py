import os
import logging
from fastapi import FastAPI, Request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)
from apscheduler.schedulers.background import BackgroundScheduler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Token und Channel
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
WEBHOOK_URL = os.environ["RAILWAY_STATIC_URL"]

# Wallet Speicher
wallets = {}  # Format: wallet_address: {"tag": str, "profit": float, "wins": int, "losses": int}

# FastAPI Setup
app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    await bot_app.update_queue.put(Update.de_json(data, bot_app.bot))
    return {"ok": True}

# Telegram Bot Setup
bot_app = Application.builder().token(BOT_TOKEN).build()

# Konversation — /own
SET_WINRATE, SET_ROI = range(2)
user_filters = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("📈 SmartFinder", callback_data="smartfinder")],
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 Getrackte Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("💰 Profit eintragen", callback_data="manual_profit")],
    ]
    await update.message.reply_text("Willkommen beim RobertsSolTrackerBot 👇", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "smartfinder":
        buttons = [
            [InlineKeyboardButton("🚀 Moonbags", callback_data="mode_moonbags")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
            [InlineKeyboardButton("🔧 Eigene Filter", callback_data="mode_own")],
        ]
        await query.edit_message_text("Wähle den SmartFinder-Modus 👇", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "mode_own":
        await query.message.reply_text("Mindest-Winrate in % eingeben (z. B. 70):")
        return SET_WINRATE

async def set_winrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.replace("%", "").strip())
        context.user_data["winrate"] = wr
        await update.message.reply_text("Mindest-ROI in % eingeben (z. B. 15):")
        return SET_ROI
    except:
        await update.message.reply_text("❌ Bitte eine gültige Zahl eingeben.")
        return SET_WINRATE

async def set_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.replace("%", "").strip())
        chat_id = update.message.chat_id
        user_filters[chat_id] = {"wr": context.user_data["winrate"], "roi": roi}
        await update.message.reply_text(f"✅ Eigene Filter gesetzt: WR ≥ {context.user_data['winrate']}%, ROI ≥ {roi}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Bitte eine gültige Zahl eingeben.")
        return SET_ROI

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        tag = " ".join(context.args[1:]) if len(context.args) > 1 else "🧐"
        wallets[wallet] = {"tag": tag, "profit": 0.0, "wins": 0, "losses": 0}
        await update.message.reply_text(f"✅ Wallet getrackt: {wallet} mit Tag '{tag}'")
    except:
        await update.message.reply_text("❌ Bitte nutze /add <WALLET> <TAG>")

async def rm_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in wallets:
            del wallets[wallet]
            await update.message.reply_text(f"🗑️ Wallet entfernt: {wallet}")
        else:
            await update.message.reply_text("❌ Diese Wallet wird nicht getrackt.")
    except:
        await update.message.reply_text("❌ Bitte nutze /rm <WALLET>")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not wallets:
        await update.message.reply_text("📭 Keine Wallets werden derzeit getrackt.")
        return

    msg = "📊 Getrackte Wallets:\n"
    for w, data in wallets.items():
        profit = data["profit"]
        wr = f"{data['wins']}/{data['wins'] + data['losses']}" if data['wins'] + data['losses'] > 0 else "0/0"
        color_pnl = "🟢" if profit >= 0 else "🔴"
        color_wr = "🟢" if data["wins"] >= data["losses"] else "🔴"
        msg += f"\n{data['tag']} — `{w}`\nWR({color_wr}{wr}) | PnL({color_pnl}{abs(profit):.2f} SOL)\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def manual_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        value = context.args[1]
        if wallet not in wallets:
            await update.message.reply_text("❌ Diese Wallet wird nicht getrackt.")
            return
        if not (value.startswith("+") or value.startswith("-")):
            await update.message.reply_text("❌ Bitte gib + oder - vor dem Betrag an.")
            return
        amount = float(value)
        wallets[wallet]["profit"] += amount
        if amount > 0:
            wallets[wallet]["wins"] += 1
        else:
            wallets[wallet]["losses"] += 1
        await update.message.reply_text("✅ Manuell aktualisiert.")
    except:
        await update.message.reply_text("❌ Nutze /profit <wallet> <+/-betrag>")

def auto_discover_wallets():
    dummy_wallets = [
        ("AutoWallet1", "🚀 AutoDetected"),
        ("AutoWallet2", "🚀 AutoDetected")
    ]
    for w, tag in dummy_wallets:
        if w not in wallets:
            wallets[w] = {"tag": tag, "profit": 0.0, "wins": 0, "losses": 0}
            msg = f"🔍 Neue Smart Wallet entdeckt!\n{tag} — `{w}`"
            bot_app.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("add", add_wallet))
bot_app.add_handler(CommandHandler("rm", rm_wallet))
bot_app.add_handler(CommandHandler("list", list_wallets))
bot_app.add_handler(CommandHandler("profit", manual_profit))
bot_app.add_handler(CallbackQueryHandler(handle_buttons))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_buttons, pattern="mode_own")],
    states={
        SET_WINRATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_winrate)],
        SET_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_roi)],
    },
    fallbacks=[],
    per_message=True,
)
bot_app.add_handler(conv_handler)

# Scheduler für AutoDiscovery
scheduler = BackgroundScheduler()
scheduler.add_job(auto_discover_wallets, "interval", minutes=30)
scheduler.start()
logger.info("✅ Scheduler gestartet")

# Start Webhook
bot_app.run_webhook(
    listen="0.0.0.0",
    port=8080,
    webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    allowed_updates=Update.ALL_TYPES,
)