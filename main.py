import os
import logging
from fastapi import FastAPI
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === Konfiguration ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("RailwayStaticUrl") + "/" + BOT_TOKEN
app = FastAPI()
logging.basicConfig(level=logging.INFO)

# === Bot-Funktionen ===
wallets = {}
OWN_WR, OWN_ROI = range(2)
own_filters = {}

# === Start-Handler ===
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📋 Getrackte Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("➖ Wallet entfernen", callback_data="remove_wallet")],
        [InlineKeyboardButton("💰 Gewinn eintragen", callback_data="add_profit")],
        [InlineKeyboardButton("🧠 SmartFinder", callback_data="smartfinder_menu")],
    ]
    await update.message.reply_text(
        "Willkommen beim Tracker-Bot.", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === /list Handler ===
async def list_wallets(update: Update, context: CallbackContext):
    if not wallets:
        await update.effective_chat.send_message("Noch keine Wallets getrackt.")
        return
    for wallet, data in wallets.items():
        pnl = data.get("pnl", 0.0)
        wins = data.get("wins", 0)
        losses = data.get("losses", 0)
        color = "🟢" if pnl > 0 else "🔴"
        await update.effective_chat.send_message(
            f"{wallet} [{data['tag']}]\nWR({wins}/{wins+losses}) PnL({color} {abs(pnl):.2f} sol)"
        )

# === /add Handler ===
async def add_wallet(update: Update, context: CallbackContext):
    try:
        wallet = context.args[0]
        tag = " ".join(context.args[1:]) or "📈 Manuell"
        wallets[wallet] = {"tag": tag, "pnl": 0.0, "wins": 0, "losses": 0}
        await update.message.reply_text(f"Wallet {wallet} hinzugefügt mit Tag: {tag}")
    except:
        await update.message.reply_text("❌ Nutzung: /add <WALLET> <TAG>")

# === /rm Handler ===
async def remove_wallet(update: Update, context: CallbackContext):
    try:
        wallet = context.args[0]
        if wallet in wallets:
            del wallets[wallet]
            await update.message.reply_text(f"✅ Wallet {wallet} entfernt.")
        else:
            await update.message.reply_text("❌ Diese Wallet ist nicht getrackt.")
    except:
        await update.message.reply_text("❌ Nutzung: /rm <WALLET>")

# === /profit Handler ===
async def add_profit(update: Update, context: CallbackContext):
    try:
        wallet = context.args[0]
        amount = float(context.args[1])
        if wallet not in wallets:
            await update.message.reply_text("❌ Diese Wallet ist nicht getrackt.")
            return
        wallets[wallet]["pnl"] += amount
        if amount > 0:
            wallets[wallet]["wins"] += 1
        else:
            wallets[wallet]["losses"] += 1
        await update.message.reply_text(
            f"✅ Gewinn/Verlust aktualisiert für {wallet} um {amount} sol."
        )
    except:
        await update.message.reply_text("❌ Nutzung: /profit <WALLET> <+/-BETRAG>")

# === SmartFinder Menü ===
async def smartfinder_menu(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("🚀 Moonbags", callback_data="preset_moonbags"),
            InlineKeyboardButton("⚡ Scalping", callback_data="preset_scalping"),
        ],
        [InlineKeyboardButton("🎛️ Eigene Filter", callback_data="preset_own")],
    ]
    await update.callback_query.edit_message_text(
        "Wähle einen SmartFinder-Modus:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# === Own-Modus Start ===
async def handle_preset_own(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🧠 Gib minimale Winrate (%) ein:")
    return OWN_WR

async def own_wr_input(update: Update, context: CallbackContext):
    try:
        wr = int(update.message.text.replace("%", "").strip())
        context.user_data["own_wr"] = wr
        await update.message.reply_text("Jetzt minimale ROI (%) eingeben:")
        return OWN_ROI
    except:
        await update.message.reply_text("❌ Ungültige Eingabe. Zahl oder Prozentwert erwartet.")
        return OWN_WR

async def own_roi_input(update: Update, context: CallbackContext):
    try:
        roi = int(update.message.text.replace("%", "").strip())
        chat_id = update.effective_chat.id
        own_filters[chat_id] = {"wr": context.user_data["own_wr"], "roi": roi}
        await update.message.reply_text(
            f"✅ Eigene Filter gesetzt: WR ≥ {context.user_data['own_wr']}%, ROI ≥ {roi}%"
        )
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Ungültige Eingabe. Zahl oder Prozentwert erwartet.")
        return OWN_ROI

# === Callback Query Handler ===
async def callback_router(update: Update, context: CallbackContext):
    data = update.callback_query.data
    if data == "list_wallets":
        await list_wallets(update, context)
    elif data == "add_wallet":
        await update.callback_query.message.reply_text("Nutze bitte /add <WALLET> <TAG>")
    elif data == "remove_wallet":
        await update.callback_query.message.reply_text("Nutze bitte /rm <WALLET>")
    elif data == "add_profit":
        await update.callback_query.message.reply_text("Nutze bitte /profit <WALLET> <+/-BETRAG>")
    elif data == "smartfinder_menu":
        await smartfinder_menu(update, context)
    elif data == "preset_own":
        return await handle_preset_own(update, context)
    else:
        await update.callback_query.message.reply_text("❌ Unbekannter Button.")

# === Smart Wallet Scanner Dummy-Job ===
def scan_smart_wallets():
    logging.info("✅ Dummy Smart Wallet Scan ausgeführt")

# === Main ===
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_wallet))
    application.add_handler(CommandHandler("rm", remove_wallet))
    application.add_handler(CommandHandler("list", list_wallets))
    application.add_handler(CommandHandler("profit", add_profit))
    application.add_handler(CallbackQueryHandler(callback_router))

    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(handle_preset_own, pattern="^preset_own$")],
            states={
                OWN_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr_input)],
                OWN_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi_input)],
            },
            fallbacks=[],
        )
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scan_smart_wallets, "interval", minutes=30, id="smart_wallet_scanner")
    scheduler.start()

    await application.bot.set_webhook(url=WEBHOOK_URL)
    await application.run_webhook(
        listen="0.0.0.0",
        port=8080,
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL,
    )

# === FastAPI Root ===
@app.get("/")
async def root():
    return {"status": "ok"}

import asyncio
if __name__ == "__main__":
    asyncio.run(main())