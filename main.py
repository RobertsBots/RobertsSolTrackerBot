import os
import asyncio
import logging
from typing import Dict, Tuple
from fastapi import FastAPI, Request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Telegram Setup
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Data Store
wallets: Dict[str, Dict] = {}
user_filters: Dict[int, Dict] = {}
OWN_WR, OWN_ROI = range(2)

# FastAPI Webhook
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# Telegram Commands
async def start(update: Update, context: CallbackContext):
    buttons = [
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("🗑 Wallet entfernen", callback_data="remove")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder")]
    ]
    await update.message.reply_text("Willkommen beim 🛰 RobertsSolTrackerBot:", reply_markup=InlineKeyboardMarkup(buttons))

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "list":
        await list_wallets(update, context)
    elif data == "remove":
        await update.effective_chat.send_message("Sende /rm <wallet> zum Entfernen.")
    elif data == "profit":
        await update.effective_chat.send_message("Sende /profit <wallet> <+/-betrag>")
    elif data == "smartfinder":
        buttons = [
            [InlineKeyboardButton("🌕 Moonbags", callback_data="sf_moonbags")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="sf_scalping")],
            [InlineKeyboardButton("🛠 Own", callback_data="sf_own")]
        ]
        await query.edit_message_text("Wähle einen SmartFinder-Modus:", reply_markup=InlineKeyboardMarkup(buttons))
    elif data.startswith("sf_own"):
        await query.edit_message_text("🛠 Gib deine gewünschte Mindest-Winrate (%) ein:")
        return OWN_WR
    elif data.startswith("sf_moonbags"):
        user_filters[update.effective_user.id] = {"wr": 60, "roi": 25}
        await update.effective_chat.send_message("🌕 Moonbags-Scanner aktiviert.")
    elif data.startswith("sf_scalping"):
        user_filters[update.effective_user.id] = {"wr": 65, "roi": 5}
        await update.effective_chat.send_message("⚡ Scalping-Scanner aktiviert.")

    return ConversationHandler.END

async def own_wr(update: Update, context: CallbackContext):
    try:
        wr = int(update.message.text.strip('% '))
        user_filters[update.effective_user.id] = {"wr": wr}
        await update.message.reply_text("Gib nun deine gewünschte Mindest-ROI (%) ein:")
        return OWN_ROI
    except:
        await update.message.reply_text("⚠ Bitte eine gültige Zahl angeben (z.B. 70)")
        return OWN_WR

async def own_roi(update: Update, context: CallbackContext):
    try:
        roi = int(update.message.text.strip('% '))
        uid = update.effective_user.id
        user_filters[uid]["roi"] = roi
        await update.message.reply_text(f"🛠 Eigener Scanner aktiviert mit WR ≥ {user_filters[uid]['wr']}% und ROI ≥ {roi}%.")
        return ConversationHandler.END
    except:
        await update.message.reply_text("⚠ Bitte eine gültige Zahl angeben (z.B. 15)")
        return OWN_ROI

async def add_wallet(update: Update, context: CallbackContext):
    try:
        addr, tag = context.args[0], context.args[1]
        wallets[addr] = {"tag": tag, "pnl": 0.0, "wr": (0, 0)}
        await update.message.reply_text(f"✅ Wallet {addr} mit Tag '{tag}' hinzugefügt.")
    except:
        await update.message.reply_text("⚠ Nutzung: /add <wallet> <tag>")

async def remove_wallet(update: Update, context: CallbackContext):
    try:
        addr = context.args[0]
        if addr in wallets:
            del wallets[addr]
            await update.message.reply_text(f"🗑 Wallet {addr} entfernt.")
        else:
            await update.message.reply_text("⚠ Wallet nicht gefunden.")
    except:
        await update.message.reply_text("⚠ Nutzung: /rm <wallet>")

async def list_wallets(update: Update, context: CallbackContext):
    if not wallets:
        await update.effective_chat.send_message("📭 Keine Wallets getrackt.")
        return
    msg = "📋 Getrackte Wallets:\n"
    for addr, data in wallets.items():
        pnl = data.get("pnl", 0.0)
        green = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
        wins, losses = data.get("wr", (0, 0))
        msg += f"\n💼 {addr} ({data['tag']})\n{green} PnL: {abs(pnl)} sol | WR({wins}/{losses})\n"
    await update.effective_chat.send_message(msg)

async def profit_entry(update: Update, context: CallbackContext):
    try:
        addr, val = context.args[0], context.args[1]
        if addr not in wallets:
            await update.message.reply_text("⚠ Wallet nicht gefunden.")
            return
        pnl = float(val.replace('+','').replace('sol',''))
        wallets[addr]["pnl"] += pnl
        if pnl >= 0:
            wallets[addr]["wr"] = (wallets[addr]["wr"][0] + 1, wallets[addr]["wr"][1])
        else:
            wallets[addr]["wr"] = (wallets[addr]["wr"][0], wallets[addr]["wr"][1] + 1)
        await update.message.reply_text("✅ Profit aktualisiert.")
    except:
        await update.message.reply_text("⚠ Nutzung: /profit <wallet> <+/-betrag>")

# Dummy Smart Wallet Scanner
async def smart_wallet_scanner():
    test_wallets = [
        {"addr": "So1TestWalletX", "wr": 68, "roi": 22, "age": "12d", "token": "XYZ"},
        {"addr": "So1TestWalletY", "wr": 75, "roi": 35, "age": "8d", "token": "LFG"}
    ]
    for user_id, filt in user_filters.items():
        for w in test_wallets:
            if w["wr"] >= filt["wr"] and w["roi"] >= filt["roi"]:
                text = f"""📡 *Gefundene Smart Wallet*:\n\n💼 `{w['addr']}`\n🧪 Token: {w['token']}\n📈 WR: {w['wr']}% | ROI: {w['roi']}%\n🕐 Age: {w['age']}\n\n👉 [Chart](https://dexscreener.com/solana/{w['token'].lower()})"""
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Dann mal los", callback_data=f"add_{w['addr']}")]])
                await application.bot.send_message(chat_id=int(CHANNEL_ID), text=text, parse_mode="Markdown", reply_markup=btn)

async def handle_wallet_button(update: Update, context: CallbackContext):
    data = update.callback_query.data
    if data.startswith("add_"):
        addr = data.split("_")[1]
        wallets[addr] = {"tag": "🚀 AutoDetected", "pnl": 0.0, "wr": (0, 0)}
        await update.callback_query.answer("Wallet wurde getrackt!")
        await update.callback_query.edit_message_text(f"✅ Wallet `{addr}` wird nun getrackt.", parse_mode="Markdown")

# Setup Telegram App
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", remove_wallet))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit_entry))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(CallbackQueryHandler(handle_wallet_button, pattern="^add_.*$"))

conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="^sf_own$")],
    states={
        OWN_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr)],
        OWN_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi)],
    },
    fallbacks=[],
)
application.add_handler(conv)

# Scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(smart_wallet_scanner, "interval", minutes=30)
scheduler.start()

# Webhook starten
async def main():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    await application.updater.start_polling()
    await application.run_webhook(webhook_path="/webhook", port=8080)

if __name__ == "__main__":
    asyncio.run(main())