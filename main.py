import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# --- Telegram Bot Setup ---
application = ApplicationBuilder().token(BOT_TOKEN).build()

# --- Root Test Endpoint ---
@app.get("/")
async def root():
    return {"message": "Bot is running"}

# --- Webhook Endpoint ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# --- START Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📄 Liste anzeigen", callback_data="list_wallets")],
        [InlineKeyboardButton("💰 Profit eintragen", callback_data="add_profit")],
        [InlineKeyboardButton("🧠 SmartFinder", callback_data="smartfinder")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Willkommen beim TrackerBot 👋", reply_markup=reply_markup)

# --- ADD Command ---
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bitte gib die Wallet-Adresse ein, die du hinzufügen möchtest.")

# --- LIST Command ---
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Deine getrackten Wallets: ... (Demo)")

# --- Callback Handler ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "add_wallet":
        await query.edit_message_text("Bitte sende mir die Wallet-Adresse als Nachricht.")
    elif query.data == "list_wallets":
        await query.edit_message_text("Deine getrackten Wallets: ... (Demo)")
    elif query.data == "add_profit":
        await query.edit_message_text("Bitte sende `/profit <wallet> <+/-betrag>`")
    elif query.data == "smartfinder":
        await query.edit_message_text("SmartFinder wird aktiviert ... 🚀")

# --- Dummy PROFIT Command ---
async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Profit gespeichert ✅ (Demo)")

# --- Dummy REMOVE Command ---
async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Wallet entfernt (Demo)")

# --- All Commands Registrieren ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit))
application.add_handler(CommandHandler("rm", rm))
application.add_handler(CallbackQueryHandler(button_handler))

# --- Bot starten ---
@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()
    logging.info("Bot ist bereit.")

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()