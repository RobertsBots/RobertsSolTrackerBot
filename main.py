import os
import json
import asyncio
from fastapi import FastAPI, Request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters
)

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

app = FastAPI()
user_states = {}
tracked_wallets = {}
user_own_filter = {}

WR_INPUT, ROI_INPUT = range(2)

application = Application.builder().token(TOKEN).build()


# === COMMAND HANDLERS ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📬 Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="show_list")],
        [InlineKeyboardButton("🗑 Wallet entfernen", callback_data="remove_wallet")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="enter_profit")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Willkommen beim Solana Wallet Tracker!\nWähle unten eine Funktion aus:", reply_markup=reply_markup)


async def smartfinder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🟡 Moonbags", callback_data="moonbags")],
        [InlineKeyboardButton("⚡️ Scalping", callback_data="scalping")],
        [InlineKeyboardButton("🛠 Own", callback_data="own")]
    ]
    await query.edit_message_text("Wähle einen SmartFinder-Modus:", reply_markup=InlineKeyboardMarkup(keyboard))


# === SMARTFINDER LOGIK ===

async def moonbags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_own_filter[update.effective_user.id] = {"wr": 70, "roi": 20}
    await update.callback_query.edit_message_text("🟡 Moonbag-Suche aktiviert (WR≥70%, ROI≥20%)")


async def scalping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_own_filter[update.effective_user.id] = {"wr": 60, "roi": 5}
    await update.callback_query.edit_message_text("⚡️ Scalping-Suche aktiviert (WR≥60%, ROI≥5%)")


async def own(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🛠 Gib deine gewünschte Mindest-Winrate (%) ein:")
    return WR_INPUT


async def own_wr_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(str(update.message.text).replace("%", "").strip())
        context.user_data["own_wr"] = wr
        await update.message.reply_text("🔧 Gib deinen gewünschten Mindest-ROI (%) ein:")
        return ROI_INPUT
    except ValueError:
        await update.message.reply_text("❌ Bitte eine gültige Zahl für WR eingeben.")
        return WR_INPUT


async def own_roi_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(str(update.message.text).replace("%", "").strip())
        wr = context.user_data["own_wr"]
        user_own_filter[update.effective_user.id] = {"wr": wr, "roi": roi}
        await update.message.reply_text(f"✅ Eigene Filter gesetzt: WR≥{wr}%, ROI≥{roi}%")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Bitte eine gültige Zahl für ROI eingeben.")
        return ROI_INPUT


# === DUMMY SUCHE (alle 30min in Realität ersetzen) ===

async def dummy_wallet_scan():
    while True:
        for user_id, filters in user_own_filter.items():
            # Dummy wallet
            wr, roi = filters["wr"], filters["roi"]
            if wr >= 60 and roi >= 5:
                text = (
                    f"<b>💼 Smart Wallet gefunden!</b>\n"
                    f"<a href='https://birdeye.so/address/FakeWallet'>FakeWallet</a> - 12.3 SOL - 41 Tage\n"
                    f"WinRate: 68% | ROI: 15% | 7d PnL: +2.3 SOL\n"
                    f"7d Tokens: 5 | All Tokens: 48 | Hodl Tokens: 4\n"
                    f"Lifetime PnL: +12.7 SOL"
                )
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🚀 Dann mal los", callback_data="track:FakeWallet")]]
                )
                try:
                    await application.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    print("Error sending smart wallet:", e)
        await asyncio.sleep(1800)  # alle 30min


# === CALLBACKS ===

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data == "add_wallet":
        await update.callback_query.message.reply_text("🔹 Bitte gib die Wallet-Adresse ein:")
    elif data == "show_list":
        await update.callback_query.message.reply_text("📋 (Demo) Liste wird hier angezeigt.")
    elif data == "remove_wallet":
        await update.callback_query.message.reply_text("🗑 (Demo) Bitte gib die Wallet zum Entfernen ein.")
    elif data == "enter_profit":
        await update.callback_query.message.reply_text("➕ (Demo) Bitte gib die Wallet & Profit ein.")
    elif data == "smartfinder_menu":
        await smartfinder_menu(update, context)
    elif data == "moonbags":
        await moonbags(update, context)
    elif data == "scalping":
        await scalping(update, context)
    elif data == "own":
        return await own(update, context)
    elif data.startswith("track:"):
        wallet = data.split("track:")[1]
        await update.callback_query.message.reply_text(f"✅ Wallet <code>{wallet}</code> wurde zum Tracking hinzugefügt!", parse_mode=ParseMode.HTML)


# === TELEGRAM ROUTE ===

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return {"ok": True}


# === MAIN ===

if __name__ == "__main__":
    from threading import Thread
    import uvicorn

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_buttons))
    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(own, pattern="^own$")],
        states={
            WR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr_input)],
            ROI_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi_input)],
        },
        fallbacks=[]
    ))

    async def run():
        await application.initialize()
        await application.start()
        asyncio.create_task(dummy_wallet_scan())
        await application.updater.start_polling()
        await application.updater.idle()

    Thread(target=lambda: asyncio.run(run())).start()
    uvicorn.run(app, host="0.0.0.0", port=8080)