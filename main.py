import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ConversationHandler, ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL")

app = FastAPI()
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# Speicher
tracked_wallets = {}  # wallet -> tag
manual_profits = {}   # wallet -> float
winloss_stats = {}    # wallet -> {"win": int, "loss": int}
user_filters = {"wr": 60, "roi": 5}

# Buttons
def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_help")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_help")],
        [InlineKeyboardButton("🚀 Smart Finder", callback_data="smartfinder_menu")]
    ])

def get_smartfinder_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌕 Moonbags", callback_data="moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="scalping")],
        [InlineKeyboardButton("🎯 Own Filter", callback_data="own_filter")]
    ])

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Willkommen! Wähle eine Funktion:",
        reply_markup=get_main_buttons(),
        parse_mode=ParseMode.HTML
    )

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) == 3:
        wallet, tag = parts[1], parts[2]
        tracked_wallets[wallet] = tag
        winloss_stats[wallet] = {"win": 0, "loss": 0}
        await update.message.reply_text(f"✅ Wallet <code>{wallet}</code> getrackt.", parse_mode=ParseMode.HTML)
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
            await update.message.reply_text("🗑️ Wallet entfernt.")
        else:
            await update.message.reply_text("❌ Wallet nicht gefunden.")
    else:
        await update.message.reply_text("⚠️ Format: /rm WALLET")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await update.message.reply_text("ℹ️ Keine Wallets getrackt.")
        return

    msg = "📋 <b>Getrackte Wallets:</b>\n"
    for idx, (wallet, tag) in enumerate(tracked_wallets.items(), 1):
        bird_link = f"https://birdeye.so/address/{wallet}?chain=solana"
        profit = manual_profits.get(wallet, 0)
        stats = winloss_stats.get(wallet, {"win": 0, "loss": 0})
        win, loss = stats["win"], stats["loss"]

        wr = f"<b>WR(</b><span style='color:green'>{win}</span>/<span style='color:red'>{loss}</span><b>)</b>"
        pnl = f"<b> | PnL(</b><span style='color:{'green' if profit >= 0 else 'red'}'>{profit:.2f} sol</span><b>)</b>"

        msg += f"\n<b>{idx}.</b> <a href='{bird_link}'>{wallet}</a> – <i>{tag}</i>\n{wr}{pnl}\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) == 3:
        wallet, profit_str = parts[1], parts[2]
        if wallet not in tracked_wallets:
            await update.message.reply_text("❌ Diese Wallet wird nicht getrackt.")
            return
        if profit_str.startswith("+") or profit_str.startswith("-"):
            try:
                profit = float(profit_str)
                manual_profits[wallet] = profit
                await update.message.reply_text(
                    f"💰 Manuell eingetragener Profit für <code>{wallet}</code>: <b>{profit} sol</b>",
                    parse_mode=ParseMode.HTML
                )
            except ValueError:
                await update.message.reply_text("❌ Ungültiger Betrag. Beispiel: /profit WALLET +12.3")
        else:
            await update.message.reply_text("⚠️ Format: /profit WALLET +/-BETRAG")
    else:
        await update.message.reply_text("⚠️ Format: /profit WALLET +/-BETRAG")

# SmartFinder + ConversationHandler
ASK_WR, ASK_ROI = range(2)

async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("🎯 Wähle deinen Modus:", reply_markup=get_smartfinder_buttons())

async def moonbags_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_filters["wr"], user_filters["roi"] = 70, 10
    await update.message.reply_text("🌕 Moonbags-Modus aktiviert.")

async def scalping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_filters["wr"], user_filters["roi"] = 60, 5
    await update.message.reply_text("⚡ Scalping-Modus aktiviert.")

async def own_filter_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Gib deine gewünschte Winrate in % an:")
    return ASK_WR

async def own_filter_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_filters["wr"] = int(update.message.text.replace("%", ""))
        await update.message.reply_text("Gib nun deinen gewünschten ROI in % an:")
        return ASK_ROI
    except:
        await update.message.reply_text("❌ Bitte gültige Winrate angeben.")
        return ASK_WR

async def own_filter_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_filters["roi"] = int(update.message.text.replace("%", ""))
        await update.message.reply_text(
            f"✅ Eigene Filter aktiviert: WR ≥ {user_filters['wr']}%, ROI ≥ {user_filters['roi']}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Bitte gültigen ROI angeben.")
        return ASK_ROI

# Callback Buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    await update.callback_query.answer()
    if data == "add_help":
        await update.callback_query.message.reply_text("📥 Nutze /add WALLET TAG")
    elif data == "list":
        await list_wallets(update.callback_query, context)
    elif data == "profit_help":
        await update.callback_query.message.reply_text("➕ Nutze /profit WALLET +/-BETRAG")
    elif data == "smartfinder_menu":
        await smartfinder_menu(update, context)
    elif data == "moonbags":
        await moonbags_command(update.callback_query, context)
    elif data == "scalping":
        await scalping_command(update.callback_query, context)
    elif data == "own_filter":
        return await own_filter_start(update, context)

# Cronjob Dummy Smart Wallet Discovery
async def auto_discover_wallets():
    dummy_wallet = "DemoSmartWalletXYZ"
    bird_link = f"https://birdeye.so/address/{dummy_wallet}?chain=solana"
    msg = (
        f"📡 <a href='{bird_link}'>{dummy_wallet}</a> – 3.7 SOL – AccountAge: 92 Tage\n"
        f"Winrate: 75% | ROI: 12% | 7d PnL: +8.1 sol\n"
        f"7d Tokens: 14 | All Tokens: 38 | Hodl Tokens: 6\n"
        f"Lifetime PnL: +19.4 sol"
    )
    await bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode=ParseMode.HTML,
                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Dann mal los", callback_data="track_demo")]]))

# Setup
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", remove_wallet))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit_command))
application.add_handler(CommandHandler("smartfinder", smartfinder_menu))
application.add_handler(CallbackQueryHandler(button_callback))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(own_filter_start, pattern="^own_filter$")],
    states={
        ASK_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_filter_wr)],
        ASK_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_filter_roi)],
    },
    fallbacks=[],
)
application.add_handler(conv_handler)

scheduler = AsyncIOScheduler()
scheduler.add_job(auto_discover_wallets, "interval", minutes=30)
scheduler.start()

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return {"ok": True}

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=f"https://{RAILWAY_STATIC_URL}/"
    )