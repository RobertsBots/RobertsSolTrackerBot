import os
import asyncio
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# === ENV & Global ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"https://roberts-sol-tracker-bot-production.up.railway.app{WEBHOOK_PATH}"

app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()
WALLETS = {}
SMART_MODE = {"mode": None, "wr": 60, "roi": 10}
WAITING_FOR_WR, WAITING_FOR_ROI = range(2)

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📮 Wallet hinzufügen", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list_wallets")],
        [InlineKeyboardButton("🗑️ Wallet entfernen", callback_data="remove_wallet")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="add_profit")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Willkommen beim Solana Wallet Tracker!\nWähle unten eine Funktion aus:", reply_markup=reply_markup)

# === BUTTON CALLBACKS ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_wallet":
        await query.message.reply_text("/add <wallet> <tag>")
    elif query.data == "list_wallets":
        await list_wallets(query, context)
    elif query.data == "remove_wallet":
        await query.message.reply_text("/rm <wallet>")
    elif query.data == "add_profit":
        await query.message.reply_text("/profit <wallet> <+/-betrag>")
    elif query.data == "smartfinder":
        keyboard = [
            [InlineKeyboardButton("🌕 Moonbags", callback_data="mode_moonbags")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
            [InlineKeyboardButton("🛠️ Own", callback_data="mode_own")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Wähle einen SmartFinder-Modus:", reply_markup=markup)
    elif query.data == "mode_moonbags":
        SMART_MODE["mode"] = "moonbags"
        SMART_MODE["wr"], SMART_MODE["roi"] = 75, 25
        await query.message.reply_text("✅ Moonbags-Suche aktiviert!")
    elif query.data == "mode_scalping":
        SMART_MODE["mode"] = "scalping"
        SMART_MODE["wr"], SMART_MODE["roi"] = 60, 5
        await query.message.reply_text("✅ Scalping-Suche aktiviert!")
    elif query.data == "mode_own":
        SMART_MODE["mode"] = "own"
        await query.message.reply_text("Gib gewünschte Mindest-Winrate (%) ein:")
        return WAITING_FOR_WR

# === /add ===
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet, tag = context.args
        WALLETS[wallet] = {"tag": tag, "pnl": 0, "wins": 0, "losses": 0}
        await update.message.reply_text(f"✅ Wallet {wallet} mit Tag {tag} hinzugefügt.")
    except:
        await update.message.reply_text("❌ Nutze: /add <wallet> <tag>")

# === /rm ===
async def rm_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        if wallet in WALLETS:
            del WALLETS[wallet]
            await update.message.reply_text(f"🗑️ Wallet {wallet} entfernt.")
        else:
            await update.message.reply_text("❌ Nicht gefunden.")
    except:
        await update.message.reply_text("❌ Nutze: /rm <wallet>")

# === /list ===
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📋 Getrackte Wallets:\n\n"
    for w, d in WALLETS.items():
        wr_total = d['wins'] + d['losses']
        wr_str = f"WR(<b><span style='color:green'>{d['wins']}</span>/<span style='color:red'>{d['losses']}</span></b>)"
        pnl_color = "green" if d["pnl"] >= 0 else "red"
        pnl_str = f"<b><span style='color:{pnl_color}'>{d['pnl']} sol</span></b>"
        text += f"• {w} [{d['tag']}]\n{wr_str} | PnL: {pnl_str}\n\n"
    await update.message.reply_text(text or "Keine Wallets.", parse_mode=ParseMode.HTML)

# === /profit ===
async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wallet = context.args[0]
        value = context.args[1]
        if not value.startswith(("+", "-")):
            return await update.message.reply_text("❌ Bitte + oder - vor dem Betrag angeben.")
        if wallet not in WALLETS:
            return await update.message.reply_text("❌ Wallet nicht gefunden.")
        amount = float(value)
        WALLETS[wallet]["pnl"] += amount
        if amount >= 0:
            WALLETS[wallet]["wins"] += 1
        else:
            WALLETS[wallet]["losses"] += 1
        await update.message.reply_text("✅ Profit aktualisiert.")
    except:
        await update.message.reply_text("❌ Nutze: /profit <wallet> <+/-betrag>")

# === /own Dialog ===
async def own_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    SMART_MODE["mode"] = "own"
    await update.message.reply_text("🛠️ Gib deine gewünschte Mindest-Winrate (%) ein:")
    return WAITING_FOR_WR

async def own_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text)
        SMART_MODE["wr"] = wr
        await update.message.reply_text("✅ Jetzt gewünschte Mindest-ROI (%) eingeben:")
        return WAITING_FOR_ROI
    except:
        await update.message.reply_text("❌ Ungültig. Gib bitte eine Zahl ein.")
        return WAITING_FOR_WR

async def own_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text)
        SMART_MODE["roi"] = roi
        await update.message.reply_text(f"✅ Eigene Suche aktiviert: WR ≥ {SMART_MODE['wr']}%, ROI ≥ {SMART_MODE['roi']}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Ungültig. Gib bitte eine Zahl ein.")
        return WAITING_FOR_ROI

# === HANDLER-SETUP ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_wallet))
application.add_handler(CommandHandler("rm", rm_wallet))
application.add_handler(CommandHandler("list", list_wallets))
application.add_handler(CommandHandler("profit", profit))
application.add_handler(CommandHandler("own", own_start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("own", own_start)],
    states={
        WAITING_FOR_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr)],
        WAITING_FOR_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi)]
    },
    fallbacks=[]
))

# === WEBHOOK ===
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return "OK"

@app.on_event("startup")
async def startup_event():
    await application.bot.set_webhook(url=WEBHOOK_URL)
    await application.initialize()
    await application.start()
    print("Bot gestartet.")

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()

# === RUN ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)