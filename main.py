import logging
import os
import re
import asyncio
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
app = FastAPI()
scheduler = AsyncIOScheduler()

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Speicher ---
tracked_wallets: Dict[str, Dict] = {}
user_filters: Dict[int, Dict] = {}
STATE_WINRATE, STATE_ROI = range(2)

# --- Menü ---
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("🗑 Wallet entfernen", callback_data="rm")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder")]
    ])

def get_smartfinder_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌕 Moonbags", callback_data="mode_moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
        [InlineKeyboardButton("🛠 Own", callback_data="mode_own")]
    ])

# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Willkommen zum 🧠 Smart Wallet Tracker!", reply_markup=get_main_keyboard())

# --- List ---
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Noch keine Wallets getrackt.")
        return
    messages = []
    for wallet, data in tracked_wallets.items():
        tag = data.get("tag", "")
        pnl = data.get("pnl", 0.0)
        win = data.get("win", 0)
        loss = data.get("loss", 0)
        color = "🟢" if pnl >= 0 else "🔴"
        pnl_str = f"{color} PnL({pnl:+.2f} sol)"
        wr_str = f"WR({win}/{loss})"
        messages.append(f"💼 {wallet} [{tag}]\n{wr_str}\n{pnl_str}")
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("\n\n".join(messages))

# --- Add ---
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, tag = context.args[0], " ".join(context.args[1:])
        tracked_wallets[wallet] = {"tag": tag, "pnl": 0.0, "win": 0, "loss": 0}
        await update.message.reply_text(f"✅ {wallet} mit Tag [{tag}] getrackt.")
    except Exception:
        await update.message.reply_text("❌ Nutzung: /add <WALLET> <TAG>")

# --- Remove ---
async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in tracked_wallets:
            del tracked_wallets[wallet]
            await update.message.reply_text(f"🗑 {wallet} entfernt.")
        else:
            await update.message.reply_text("Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❌ Nutzung: /rm <WALLET>")

# --- Profit ---
async def profit_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, value = context.args[0], context.args[1]
        if wallet not in tracked_wallets:
            await update.message.reply_text("Wallet nicht gefunden.")
            return
        if not value.startswith(("+", "-")):
            await update.message.reply_text("❌ Bitte gib den Profit mit + oder - an, z. B. /profit <wallet> +1.2")
            return
        delta = float(value)
        tracked_wallets[wallet]["pnl"] += delta
        if delta >= 0:
            tracked_wallets[wallet]["win"] += 1
        else:
            tracked_wallets[wallet]["loss"] += 1
        await update.message.reply_text(f"📈 Profit für {wallet} aktualisiert.")
    except:
        await update.message.reply_text("❌ Nutzung: /profit <wallet> <+/-betrag>")

# --- SmartFinder Menü ---
async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Wähle einen SmartFinder-Modus:", reply_markup=get_smartfinder_keyboard())

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    mode = query.data
    user_id = query.from_user.id
    if mode == "mode_moonbags":
        user_filters[user_id] = {"wr": 70, "roi": 15}
        await query.answer("🌕 Moonbags aktiviert!")
    elif mode == "mode_scalping":
        user_filters[user_id] = {"wr": 60, "roi": 5}
        await query.answer("⚡ Scalping aktiviert!")
    elif mode == "mode_own":
        await query.message.reply_text("🛠 Gib deine gewünschte Mindest-Winrate (%) ein:")
        return STATE_WINRATE
    return ConversationHandler.END

async def own_wr_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    match = re.match(r"(\d+)", update.message.text)
    if not match:
        await update.message.reply_text("❌ Bitte gib eine gültige Zahl ein (z. B. 70)")
        return STATE_WINRATE
    wr = int(match.group(1))
    context.user_data["wr"] = wr
    await update.message.reply_text("🔢 Gib jetzt den gewünschten Mindest-ROI (%) ein:")
    return STATE_ROI

async def own_roi_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    match = re.match(r"(\d+)", update.message.text)
    if not match:
        await update.message.reply_text("❌ Bitte gib eine gültige Zahl ein (z. B. 15)")
        return STATE_ROI
    roi = int(match.group(1))
    wr = context.user_data["wr"]
    user_filters[user_id] = {"wr": wr, "roi": roi}
    await update.message.reply_text(f"✅ Eigener Filter gesetzt: WR ≥ {wr}%, ROI ≥ {roi}%")
    return ConversationHandler.END

# --- Smart Wallet Scanner (alle 30 Min) ---
async def smart_wallet_scanner():
    dummy_wallets = [
        {"wallet": "ABC123", "wr": 75, "roi": 20, "age": "7d", "token": "XYZ", "balance": 2.5},
        {"wallet": "DEF456", "wr": 60, "roi": 5, "age": "3d", "token": "SOL", "balance": 1.8},
    ]
    for user_id, filt in user_filters.items():
        for w in dummy_wallets:
            if w["wr"] >= filt["wr"] and w["roi"] >= filt["roi"]:
                wallet = w["wallet"]
                if wallet in tracked_wallets:
                    continue
                tracked_wallets[wallet] = {
                    "tag": "🚀 AutoDetected",
                    "pnl": 0.0,
                    "win": 0,
                    "loss": 0
                }
                msg = (
                    f"🚨 Neue smarte Wallet entdeckt:\n\n"
                    f"💼 {wallet}\n"
                    f"📈 WR: {w['wr']}%, ROI: {w['roi']}%\n"
                    f"📊 Balance: {w['balance']} sol\n"
                    f"⏳ Alter: {w['age']}, Token: {w['token']}\n"
                    f"🔗 https://dexscreener.com/solana/{w['token']}\n"
                )
                await context.bot.send_message(chat_id=CHANNEL_ID, text=msg)

# --- Webhook FastAPI Setup ---
@app.on_event("startup")
async def on_startup():
    scheduler.add_job(smart_wallet_scanner, "interval", minutes=30)
    scheduler.start()

# --- Bot Setup ---
def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_mode, pattern="^mode_"),
            CommandHandler("own", set_mode)
        ],
        states={
            STATE_WINRATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr_input)],
            STATE_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi_input)],
        },
        fallbacks=[],
        per_chat=True
    )

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("add", add_wallet))
    app_bot.add_handler(CommandHandler("rm", remove_wallet))
    app_bot.add_handler(CommandHandler("profit", profit_entry))
    app_bot.add_handler(conv_handler)
    app_bot.add_handler(CallbackQueryHandler(list_wallets, pattern="^list$"))
    app_bot.add_handler(CallbackQueryHandler(remove_wallet, pattern="^rm$"))
    app_bot.add_handler(CallbackQueryHandler(profit_entry, pattern="^profit$"))
    app_bot.add_handler(CallbackQueryHandler(smartfinder_menu, pattern="^smartfinder$"))

    app_bot.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=f"https://{os.getenv('RAILWAY_STATIC_URL')}/webhook",
        path="/webhook"
    )

if __name__ == "__main__":
    main()