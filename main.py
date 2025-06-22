import os
import json
import asyncio
import httpx
from fastapi import FastAPI, Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes, MessageHandler, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# Speicherstrukturen
tracked_wallets = {}         # {wallet: {"tag": str, "pnl": float, "wr": [wins, losses]}}
pending_filter_input = {}    # chat_id -> {"step": "wr"/"roi", "wr": int}
smartfinder_active = False
smartfinder_mode = None      # "moonbags", "scalping", "own"
custom_filters = {"wr": 60, "roi": 10}

# Hilfsfunktionen
def save_data():
    with open("wallets.json", "w") as f:
        json.dump(tracked_wallets, f)

def load_data():
    global tracked_wallets
    if os.path.exists("wallets.json"):
        with open("wallets.json", "r") as f:
            tracked_wallets = json.load(f)

def wallet_button_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📮 Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="show_list")],
        [InlineKeyboardButton("🗑️ Wallet entfernen", callback_data="rm_wallet")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="add_profit")],
        [InlineKeyboardButton("🚀 Smart Finder", callback_data="smart_finder")]
    ])

def smartfinder_submenu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌕 Moonbags", callback_data="moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="scalping")],
        [InlineKeyboardButton("🛠️ Eigene Filter", callback_data="own")]
    ])

# Telegram Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Willkommen beim Solana Wallet Tracker!\nWähle unten eine Funktion aus:",
        reply_markup=wallet_button_menu()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat.id

    if data == "add_wallet":
        await context.bot.send_message(chat_id, "Bitte sende mir die Wallet-Adresse + Tag:\nFormat: `<wallet> <tag>`")
    elif data == "show_list":
        if not tracked_wallets:
            await context.bot.send_message(chat_id, "Keine Wallets getrackt.")
        else:
            msg = "📋 <b>Getrackte Wallets:</b>\n\n"
            for w, info in tracked_wallets.items():
                wr = info.get("wr", [0, 0])
                pnl = info.get("pnl", 0)
                wr_str = f"WR({wr[0]}/{wr[1]})"
                pnl_str = f"PnL({pnl:+.2f} sol)"
                msg += f"<code>{w}</code> ({info['tag']})\n{wr_str} | {pnl_str}\n\n"
            await context.bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML)
    elif data == "rm_wallet":
        await context.bot.send_message(chat_id, "Bitte sende die Wallet-Adresse, die du entfernen möchtest.")
    elif data == "add_profit":
        await context.bot.send_message(chat_id, "Format: `/profit <wallet> <+/-betrag>`")
    elif data == "smart_finder":
        await context.bot.send_message(chat_id, "🧠 Wähle ein Filterprofil:", reply_markup=smartfinder_submenu())
    elif data == "moonbags":
        global smartfinder_mode
        smartfinder_mode = "moonbags"
        await context.bot.send_message(chat_id, "🌕 Moonbag-Filter aktiviert.")
    elif data == "scalping":
        smartfinder_mode = "scalping"
        await context.bot.send_message(chat_id, "⚡ Scalping-Filter aktiviert.")
    elif data == "own":
        pending_filter_input[str(chat_id)] = {"step": "wr"}
        await context.bot.send_message(chat_id, "📊 Bitte gib die gewünschte Mindest-Winrate ein (z. B. 60):")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    msg = update.message.text.strip()

    # Eigene Filter Schritt 1: Winrate
    if chat_id in pending_filter_input:
        step = pending_filter_input[chat_id]["step"]
        if step == "wr":
            try:
                wr = int(msg)
                pending_filter_input[chat_id] = {"step": "roi", "wr": wr}
                await update.message.reply_text("✅ Winrate gespeichert. Jetzt bitte den Mindest-ROI eingeben (z. B. 10):")
            except:
                await update.message.reply_text("❌ Ungültige Eingabe. Bitte eine ganze Zahl eingeben.")
            return
        elif step == "roi":
            try:
                roi = int(msg)
                wr = pending_filter_input[chat_id]["wr"]
                del pending_filter_input[chat_id]
                custom_filters["wr"] = wr
                custom_filters["roi"] = roi
                global smartfinder_mode
                smartfinder_mode = "own"
                await update.message.reply_text(f"✅ Eigene Filter aktiviert:\nWinrate ≥ {wr} % | ROI ≥ {roi} %")
            except:
                await update.message.reply_text("❌ Ungültiger ROI. Bitte eine ganze Zahl eingeben.")
            return

    # Add wallet
    if " " in msg:
        parts = msg.split()
        if len(parts) == 2:
            wallet, tag = parts
            tracked_wallets[wallet] = {"tag": tag, "pnl": 0.0, "wr": [0, 0]}
            save_data()
            await update.message.reply_text(f"✅ Wallet {wallet} ({tag}) hinzugefügt.")
            return
    elif msg.startswith("/profit"):
        try:
            _, wallet, value = msg.split()
            val = float(value)
            tracked_wallets[wallet]["pnl"] += val
            save_data()
            await update.message.reply_text(f"✅ PnL für {wallet} aktualisiert: {val:+.2f} sol")
        except:
            await update.message.reply_text("❌ Fehler beim Eintragen. Nutze: `/profit <wallet> <+/-betrag>`")

    elif msg in tracked_wallets:
        del tracked_wallets[msg]
        save_data()
        await update.message.reply_text(f"🗑️ Wallet {msg} entfernt.")

# Webhook-Funktion
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    load_data()
    await application.bot.send_message(
        chat_id=CHANNEL_ID,
        text="✅ <b>RobertsSolTrackerBot ist bereit!</b>",
        parse_mode=ParseMode.HTML
    )

# Telegram-Handler
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

# Start Bot mit Webhook
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)