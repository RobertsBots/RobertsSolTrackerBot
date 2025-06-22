import os
import logging
import asyncio
import json
import httpx
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WEBHOOK_HOST = os.getenv("RAILWAY_STATIC_URL")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", default=8000))

wallets = {}
smartfinder_config = {"mode": None, "wr": 60, "roi": 5}

# LOGGING
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# FASTAPI SERVER
app = FastAPI()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return {"ok": True}

@app.get("/")
def root():
    return {"message": "Bot is running!"}

# === Bot-Funktionen ===

def format_wallet_info(address, data):
    wr = data.get("wr", [0, 0])
    pnl = data.get("pnl", 0)
    wr_str = f'WR({wr[0]}/{wr[1]})'
    pnl_str = f'PnL({"+" if pnl >= 0 else ""}{round(pnl, 2)} sol)'
    return f'{address} — {wr_str} | {pnl_str} | {data.get("tag", "")}'

def wr_color_string(wr):
    return f'WR(<b><span style="color:green">{wr[0]}</span>/<span style="color:red">{wr[1]}</span></b>)'

def pnl_color_string(pnl):
    if pnl > 0:
        return f'<b><span style="color:green">PnL(+{round(pnl,2)} sol)</span></b>'
    elif pnl < 0:
        return f'<b><span style="color:red">PnL({round(pnl,2)} sol)</span></b>'
    else:
        return f'PnL(0 sol)'

async def send_wallets_to_channel(found_wallets, application):
    for wallet in found_wallets:
        address = wallet["address"]
        tag = wallet["tag"]
        wr = wallet["wr"]
        roi = wallet["roi"]
        pnl = wallet["pnl"]
        age = wallet["age"]
        token = wallet["token"]

        text = (
            f"🚨 <b>Neue Smart Wallet gefunden!</b>\n"
            f"<code>{address}</code>\n"
            f"🏷️ {tag}\n"
            f"📈 {wr_color_string(wr)} | ROI: {roi}%\n"
            f"{pnl_color_string(pnl)}\n"
            f"🧓 Account Age: {age}d\n"
            f"🪙 Token: {token}\n"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Dann mal los 🚀", callback_data=f"track_{address}_{tag}")]
        ])

        await application.bot.send_message(chat_id=CHANNEL_ID, text=text, reply_markup=keyboard, parse_mode="HTML")

# === Befehle ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("📈 SmartFinder starten", callback_data="smartfinder")],
    ]
    await update.message.reply_text("Willkommen! Wähle eine Aktion:", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        address = context.args[0]
        tag = context.args[1] if len(context.args) > 1 else ""
        wallets[address] = {"tag": tag, "wr": [0, 0], "pnl": 0}
        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"✅ Wallet <code>{address}</code> hinzugefügt ({tag})", parse_mode="HTML")
    except:
        await update.message.reply_text("❌ Nutzung: /add <WALLET> <TAG>")

async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        address = context.args[0]
        if address in wallets:
            del wallets[address]
            await update.message.reply_text(f"🗑️ Wallet <code>{address}</code> entfernt.", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❌ Nutzung: /rm <WALLET>")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not wallets:
        await update.message.reply_text("📭 Keine Wallets getrackt.")
        return
    msg = "📋 <b>Getrackte Wallets:</b>\n"
    for addr, data in wallets.items():
        wr = wr_color_string(data["wr"])
        pnl = pnl_color_string(data["pnl"])
        msg += f"— <code>{addr}</code>\n{wr} | {pnl} | {data['tag']}\n\n"
    await update.message.reply_text(msg, parse_mode="HTML")

async def set_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        address = context.args[0]
        value = context.args[1]
        if not value.startswith(("+", "-")):
            raise Exception
        value = float(value)
        if address in wallets:
            wallets[address]["pnl"] += value
            if value > 0:
                wallets[address]["wr"][0] += 1
            else:
                wallets[address]["wr"][1] += 1
            await update.message.reply_text(f"✅ PnL für {address} aktualisiert.")
        else:
            await update.message.reply_text("❌ Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❌ Nutzung: /profit <wallet> <+/-betrag>")

# === SmartFinder Dialog ===

WR, ROI = range(2)

async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Moonbags", callback_data="mode_moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
        [InlineKeyboardButton("⚙️ Own", callback_data="mode_own")],
    ]
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("🔎 Wähle einen Modus:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("🔎 Wähle einen Modus:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    query = update.callback_query
    data = query.data
    if data == "mode_moonbags":
        smartfinder_config["mode"] = "moonbags"
        smartfinder_config["wr"] = 70
        smartfinder_config["roi"] = 30
        await query.edit_message_text("🚀 Moonbags Modus aktiviert!")
    elif data == "mode_scalping":
        smartfinder_config["mode"] = "scalping"
        smartfinder_config["wr"] = 60
        smartfinder_config["roi"] = 10
        await query.edit_message_text("⚡ Scalping Modus aktiviert!")
    elif data == "mode_own":
        await query.edit_message_text("Gib die Mindest-Winrate ein (z.B. 60%):")
        return WR

    return ConversationHandler.END

async def wr_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.replace("%", ""))
        context.user_data["wr"] = wr
        await update.message.reply_text("Und jetzt den Mindest-ROI (z.B. 15):")
        return ROI
    except:
        await update.message.reply_text("❌ Bitte gültige Winrate eingeben.")
        return WR

async def roi_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.replace("%", ""))
        smartfinder_config["mode"] = "own"
        smartfinder_config["wr"] = context.user_data["wr"]
        smartfinder_config["roi"] = roi
        await update.message.reply_text(f"✅ Eigener SmartFinder aktiviert mit WR ≥ {smartfinder_config['wr']}% und ROI ≥ {roi}%.")
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Bitte gültigen ROI eingeben.")
        return ROI

# === CallbackHandler ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "list":
        await list_wallets(update, context)
    elif data == "smartfinder":
        await smartfinder_menu(update, context)
    elif data.startswith("track_"):
        _, addr, tag = data.split("_", 2)
        wallets[addr] = {"tag": tag, "wr": [0, 0], "pnl": 0}
        await query.edit_message_text(f"✅ Wallet <code>{addr}</code> wird jetzt getrackt!", parse_mode="HTML")

# === Dummy Wallet Discovery (alle 30min) ===

async def smart_wallet_scanner():
    wr = smartfinder_config["wr"]
    roi = smartfinder_config["roi"]
    # Dummy Wallets:
    dummy = [{
        "address": "DummyWallet123",
        "tag": "🚀 AutoDetected",
        "wr": [12, 4],
        "roi": 22,
        "pnl": 4.2,
        "age": 7,
        "token": "BONK",
    }]
    await send_wallets_to_channel(dummy, application)

# === Setup ===

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", remove_wallet))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", set_profit))
application.add_handler(CallbackQueryHandler(button_handler))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_mode_selection, pattern="^mode_own$"), CommandHandler("own", smartfinder_menu)],
    states={
        WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, wr_input)],
        ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, roi_input)],
    },
    fallbacks=[],
)
application.add_handler(conv_handler)

# Scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(smart_wallet_scanner, trigger=IntervalTrigger(minutes=30), id="smart_wallet_scanner")
scheduler.start()

# Start Webhook
application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=WEBHOOK_URL,
    allowed_updates=Update.ALL_TYPES,
)