import os
import json
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
)
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

# ========== Konfiguration ==========
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = f"https://{os.getenv('RAILWAY_STATIC_URL')}/"

bot = Bot(token=TOKEN)
app = FastAPI()

# ========== Datenstrukturen ==========
tracked_wallets = {}        # { wallet: tag }
manual_profits = {}         # { wallet: float }
winloss_stats = {}          # { wallet: {"win": x, "loss": y} }
own_filter = {"wr": 60, "roi": 5}

# ========== SmartFinder Dummy ==========
async def find_smart_wallets():
    # Hier ersetzt du später den Dummy durch echte API-Anbindung (Dune, Solana etc.)
    return [
        {
            "wallet": "F4k3Sm4rtW4ll3t111",
            "balance": "12.45 SOL",
            "account_age": "97d",
            "winrate": 73,
            "roi": 18,
            "pnl_7d": "+38.6",
            "tokens_7d": "9",
            "tokens_total": "42",
            "tokens_hodl": "5",
            "pnl_lifetime": "+289.1"
        }
    ]

# ========== UI: Tastaturen ==========
def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_help")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_help")],
        [InlineKeyboardButton("🧠 SmartFinder", callback_data="smartfinder_menu")]
    ])

def smartfinder_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Moonbags", callback_data="moonbags"),
            InlineKeyboardButton("⚡ Scalping", callback_data="scalping")
        ],
        [InlineKeyboardButton("🎛️ Own", callback_data="own")],
    ])

# ========== Handler ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Willkommen beim Solana Wallet Tracker!</b>\nWähle unten eine Funktion aus:",
        reply_markup=start_keyboard(),
        parse_mode=constants.ParseMode.HTML
    )

async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "add_help":
        await query.message.reply_text("📥 /add WALLET TAG")
    elif query.data == "list":
        await handle_list(query.message.chat_id)
    elif query.data == "profit_help":
        await query.message.reply_text("➕ /profit WALLET +/-BETRAG")
    elif query.data == "smartfinder_menu":
        await query.message.reply_text("🧠 Wähle einen Modus:", reply_markup=smartfinder_keyboard())
    elif query.data == "moonbags":
        own_filter.update({"wr": 60, "roi": 20})
        await query.message.reply_text("🚀 Moonbags-Modus aktiviert.")
    elif query.data == "scalping":
        own_filter.update({"wr": 65, "roi": 5})
        await query.message.reply_text("⚡ Scalping-Modus aktiviert.")
    elif query.data == "own":
        await query.message.reply_text("📊 Sende deine Wunsch-Winrate (z. B. 70):")
        return 1

async def receive_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        own_filter["wr"] = int(update.message.text.strip().replace("%", ""))
        await update.message.reply_text("📈 Jetzt bitte den Mindest-ROI eingeben (z. B. 10):")
        return 2
    except:
        await update.message.reply_text("❌ Bitte nur eine Zahl (z. B. 70)")
        return 1

async def receive_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        own_filter["roi"] = int(update.message.text.strip().replace("%", ""))
        await update.message.reply_text(
            f"✅ Eigene Filter gesetzt: WR ≥ {own_filter['wr']}%, ROI ≥ {own_filter['roi']}%\n/scanner zum Starten!"
        )
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Bitte nur eine Zahl (z. B. 10)")
        return 2

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("⚠️ Format: /add WALLET TAG")
        return
    wallet, tag = parts[1], parts[2]
    tracked_wallets[wallet] = tag
    winloss_stats[wallet] = {"win": 0, "loss": 0}
    await update.message.reply_text(f"✅ Wallet {wallet} mit Tag <b>{tag}</b> hinzugefügt.", parse_mode=constants.ParseMode.HTML)

async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) != 2:
        await update.message.reply_text("⚠️ Format: /rm WALLET")
        return
    wallet = parts[1]
    if wallet in tracked_wallets:
        del tracked_wallets[wallet]
        manual_profits.pop(wallet, None)
        winloss_stats.pop(wallet, None)
        await update.message.reply_text(f"🗑️ Wallet {wallet} entfernt.")
    else:
        await update.message.reply_text("❌ Wallet nicht gefunden.")

async def profit_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("⚠️ Format: /profit WALLET +/-BETRAG")
        return
    wallet, profit_str = parts[1], parts[2]
    if wallet not in tracked_wallets:
        await update.message.reply_text("❌ Wallet nicht gefunden.")
        return
    if profit_str.startswith("+") or profit_str.startswith("-"):
        try:
            manual_profits[wallet] = float(profit_str)
            await update.message.reply_text(f"💰 Profit für {wallet} gesetzt: {profit_str} sol")
        except:
            await update.message.reply_text("❌ Ungültiger Betrag.")
    else:
        await update.message.reply_text("⚠️ Format: /profit WALLET +/-BETRAG")

async def handle_list(chat_id):
    if not tracked_wallets:
        await bot.send_message(chat_id=chat_id, text="ℹ️ Keine Wallets getrackt.")
        return
    msg = "📋 <b>Getrackte Wallets:</b>\n"
    for i, (wallet, tag) in enumerate(tracked_wallets.items(), 1):
        bird = f"https://birdeye.so/address/{wallet}?chain=solana"
        wr = winloss_stats.get(wallet, {"win": 0, "loss": 0})
        pnl = manual_profits.get(wallet, 0)
        msg += f"\n<b>{i}.</b> <a href='{bird}'>{wallet}</a> – <i>{tag}</i>\n"
        msg += f"<b>WR(</b><span style='color:green'>{wr['win']}</span>/<span style='color:red'>{wr['loss']}</span><b>)</b>"
        msg += f"<b> | PnL(</b><span style='color:{'green' if pnl >= 0 else 'red'}'>{pnl:.2f} sol</span><b>)</b>\n"
    await bot.send_message(chat_id=chat_id, text=msg, parse_mode=constants.ParseMode.HTML)

async def run_scanner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallets = await find_smart_wallets()
    for w in wallets:
        if w["winrate"] >= own_filter["wr"] and w["roi"] >= own_filter["roi"]:
            link = f"https://birdeye.so/address/{w['wallet']}?chain=solana"
            msg = (
                f"<a href='{link}'>{w['wallet']}</a> – {w['balance']} – {w['account_age']}\n"
                f"Winrate: {w['winrate']}% | ROI: {w['roi']}% | 7d PnL: {w['pnl_7d']} sol\n"
                f"7d Tokens: {w['tokens_7d']} | All Tokens: {w['tokens_total']} | Hodl Tokens: {w['tokens_hodl']}\n"
                f"Lifetime PnL: {w['pnl_lifetime']} sol"
            )
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 Dann mal los", callback_data=f"track_{w['wallet']}")]])
            await bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=btn, parse_mode=constants.ParseMode.HTML)

async def button_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.callback_query.data.split("_")[1]
    tracked_wallets[wallet] = "🚀 AutoDetected"
    winloss_stats[wallet] = {"win": 0, "loss": 0}
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(f"📌 Wallet {wallet} getrackt.")

# ========== Setup ==========
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(url=WEBHOOK_URL)

@app.post("/")
async def telegram_webhook(request: Request):
    data = await request.json()
    await application.update_queue.put(Update.de_json(data, bot))
    return {"ok": True}

application = Application.builder().token(TOKEN).build()

application.add_handler(CallbackQueryHandler(help_button))
application.add_handler(CallbackQueryHandler(button_track, pattern="^track_"))
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", remove_wallet))
application.add_handler(CommandHandler("profit", profit_entry))
application.add_handler(CommandHandler("list", lambda u, c: handle_list(u.effective_chat.id)))
application.add_handler(CommandHandler("scanner", run_scanner))

# ConversationHandler für /own
own_conv = ConversationHandler(
    entry_points=[CommandHandler("own", help_button), CallbackQueryHandler(help_button, pattern="own")],
    states={
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wr)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_roi)],
    },
    fallbacks=[],
)
application.add_handler(own_conv)

application.run_webhook(
    listen="0.0.0.0",
    port=int(os.getenv("PORT", 8000)),
    webhook_url=WEBHOOK_URL
)