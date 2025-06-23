import os
import asyncio
import logging
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler,
    ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === Konfiguration ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # z. B. "-4690026526"
WEBHOOK_URL = os.getenv("RailwayStaticUrl") + "/" + BOT_TOKEN

# === FastAPI Setup ===
app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# === In-Memory Datenbank ===
tracked_wallets = {}
wallet_profits = {}
wallet_results = {}
scanner_filters = {}

# === Logging ===
logging.basicConfig(level=logging.INFO)

# === States für ConversationHandler ===
ASK_WR, ASK_ROI = range(2)

# === Befehle ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 SmartFinder", callback_data="smartfinder")],
        [InlineKeyboardButton("📋 Getrackte Wallets", callback_data="list")],
        [InlineKeyboardButton("➕ Profit manuell", callback_data="manual_profit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Willkommen beim Solana Wallet Tracker!", reply_markup=reply_markup)

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Nutzung: /add WALLET TAG")
        return
    wallet, tag = context.args[0], context.args[1]
    tracked_wallets[wallet] = tag
    wallet_results[wallet] = {'wins': 0, 'losses': 0}
    wallet_profits[wallet] = 0
    await update.message.reply_text(f"✅ Wallet {wallet} mit Tag '{tag}' getrackt.")

async def rm_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Nutzung: /rm WALLET")
        return
    wallet = context.args[0]
    if wallet in tracked_wallets:
        del tracked_wallets[wallet]
        wallet_profits.pop(wallet, None)
        wallet_results.pop(wallet, None)
        await update.message.reply_text(f"🗑️ Wallet {wallet} entfernt.")
    else:
        await update.message.reply_text("❌ Wallet nicht gefunden.")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await update.message.reply_text("Keine Wallets getrackt.")
        return
    msg = "📋 *Getrackte Wallets:*\n\n"
    for wallet, tag in tracked_wallets.items():
        result = wallet_results.get(wallet, {'wins': 0, 'losses': 0})
        wr = f"WR({result['wins']}/{result['wins'] + result['losses']})"
        pnl = wallet_profits.get(wallet, 0)
        pnl_str = f"PnL(+{pnl} sol)" if pnl >= 0 else f"PnL({pnl} sol)"
        pnl_str = f"💚 {pnl_str}" if pnl >= 0 else f"❤️ {pnl_str}"
        msg += f"• {wallet} `{tag}`\n{wr} {pnl_str}\n\n"
    await update.message.reply_markdown(msg)

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Nutzung: /profit WALLET +/-BETRAG")
        return
    wallet, raw = context.args[0], context.args[1]
    if wallet not in tracked_wallets:
        await update.message.reply_text("❌ Wallet nicht getrackt.")
        return
    try:
        if raw.startswith("+") or raw.startswith("-"):
            delta = float(raw)
        else:
            await update.message.reply_text("Bitte + oder - angeben (z. B. /profit WALLET +1.5)")
            return
        wallet_profits[wallet] = wallet_profits.get(wallet, 0) + delta
        if delta > 0:
            wallet_results[wallet]['wins'] += 1
        else:
            wallet_results[wallet]['losses'] += 1
        await update.message.reply_text("✅ Profit aktualisiert.")
    except:
        await update.message.reply_text("❌ Ungültiger Betrag.")

# === SmartFinder Menü ===
async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🚀 Moonbags", callback_data="moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="scalping")],
        [InlineKeyboardButton("⚙️ Eigene Filter", callback_data="own")]
    ]
    await query.edit_message_text("Wähle SmartFinder-Modus:", reply_markup=InlineKeyboardMarkup(keyboard))

# === Eigene Filter setzen ===
async def own_filter_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Gib die minimale Winrate ein (z. B. 70):")
    return ASK_WR

async def ask_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["min_wr"] = int(update.message.text.strip("% "))
    await update.message.reply_text("Gib den minimalen ROI ein (z. B. 10):")
    return ASK_ROI

async def save_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["min_roi"] = int(update.message.text.strip("% "))
    user_id = update.effective_user.id
    scanner_filters[user_id] = {
        "wr": context.user_data["min_wr"],
        "roi": context.user_data["min_roi"]
    }
    await update.message.reply_text(f"✅ Eigene Filter gespeichert: WR ≥ {context.user_data['min_wr']}%, ROI ≥ {context.user_data['min_roi']}%")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Abgebrochen.")
    return ConversationHandler.END

# === Webhook FastAPI Route ===
@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# === Auto-Scan Dummy Job (alle 30min) ===
async def smart_wallet_scanner():
    dummy_wallet = "ExampleSmartWallet123"
    tracked_wallets[dummy_wallet] = "🚀 AutoDetected"
    wallet_profits[dummy_wallet] = 0
    wallet_results[dummy_wallet] = {"wins": 0, "losses": 0}
    await application.bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"🧠 Neue Smart Wallet entdeckt:\n{dummy_wallet}\nTag: 🚀 AutoDetected"
    )

scheduler = AsyncIOScheduler()
scheduler.add_job(smart_wallet_scanner, "interval", minutes=30)

# === Bot Setup ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", rm_wallet))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit))
application.add_handler(CallbackQueryHandler(smartfinder_menu, pattern="smartfinder"))
application.add_handler(CallbackQueryHandler(own_filter_start, pattern="own"))

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, ask_roi)],
    states={ASK_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_roi)],
            ASK_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_filter)]},
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=True
)
application.add_handler(conv_handler)

# === Start Webhook & Scheduler ===
async def main():
    scheduler.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()  # failsafe fallback
    await application.updater.idle()

if __name__ == "__main__":
    import uvicorn
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())