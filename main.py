import os
import asyncio
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

# Local memory
wallets = {}
profits = {}
winloss = {}
user_filter = {}
smartfinder_mode = {}

WR_INPUT, ROI_INPUT = range(2)

# Telegram Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Wallet eintragen", callback_data="add_wallet")],
        [InlineKeyboardButton("➖ Wallet entfernen", callback_data="rm_wallet")],
        [InlineKeyboardButton("📋 Liste", callback_data="list_wallets")],
        [InlineKeyboardButton("💰 Profit", callback_data="enter_profit")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder_menu")]
    ]
    await update.message.reply_text("👋 Willkommen beim Tracker-Bot!", reply_markup=InlineKeyboardMarkup(keyboard))

# Buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "add_wallet":
        await query.edit_message_text("Nutze: /add <WALLET> <TAG>")
    elif data == "rm_wallet":
        await query.edit_message_text("Nutze: /rm <WALLET>")
    elif data == "list_wallets":
        if not wallets:
            await query.edit_message_text("📭 Keine Wallets getrackt.")
            return
        text = "📋 Getrackte Wallets:\n"
        for i, (w, t) in enumerate(wallets.items(), 1):
            pnl = profits.get(w, 0)
            wr = winloss.get(w, {"win": 0, "loss": 0})
            text += f"\n{i}. <code>{w}</code> – <i>{t}</i>\n"
            text += f"WR(<b><span style='color:green'>{wr['win']}</span>/<span style='color:red'>{wr['loss']}</span></b>) | "
            text += f"PnL(<b><span style='color:{'green' if pnl >=0 else 'red'}'>{pnl:.2f} sol</span></b>)\n"
        await query.edit_message_text(text, parse_mode=constants.ParseMode.HTML)

    elif data == "enter_profit":
        await query.edit_message_text("Nutze: /profit <WALLET> <+/–BETRAG>")

    elif data == "smartfinder_menu":
        keyboard = [
            [InlineKeyboardButton("🌕 Moonbags", callback_data="mode:moonbags")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="mode:scalping")],
            [InlineKeyboardButton("🛠 Own", callback_data="mode:own")]
        ]
        await query.edit_message_text("Wähle einen Modus:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("mode:"):
        mode = data.split(":")[1]
        uid = query.from_user.id
        smartfinder_mode[uid] = mode
        if mode == "own":
            await query.edit_message_text("Gib deine gewünschte Mindest-Winrate (%) ein:")
            return WR_INPUT
        await query.edit_message_text(f"✅ Modus {mode} aktiviert.")

    elif data.startswith("track:"):
        addr = data.split(":")[1]
        wallets[addr] = f"Auto-{addr[-4:]}"
        await context.bot.send_message(CHANNEL_ID, f"🎯 Tracking aktiviert für {addr}")

    return ConversationHandler.END

# /add /rm /profit
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("/add"):
        _, w, t = text.split()
        wallets[w] = t
        winloss[w] = {"win": 0, "loss": 0}
        await update.message.reply_text(f"✅ Wallet {w} als {t} hinzugefügt.")
    elif text.startswith("/rm"):
        _, w = text.split()
        wallets.pop(w, None)
        profits.pop(w, None)
        winloss.pop(w, None)
        await update.message.reply_text(f"🗑️ Wallet {w} entfernt.")
    elif text.startswith("/profit"):
        _, w, val = text.split()
        try:
            val = float(val)
            profits[w] = val
            await update.message.reply_text(f"💰 Neuer PnL für {w}: {val} sol")
        except:
            await update.message.reply_text("❌ Format: /profit WALLET +/-BETRAG")

# WR + ROI Dialog
async def own_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.replace("%", "").strip())
        context.user_data["wr"] = wr
        await update.message.reply_text("Und nun dein gewünschter ROI (%)?")
        return ROI_INPUT
    except:
        await update.message.reply_text("Bitte gültige Zahl eingeben:")
        return WR_INPUT

async def own_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.replace("%", "").strip())
        uid = update.message.from_user.id
        user_filter[uid] = {"wr": context.user_data["wr"], "roi": roi}
        smartfinder_mode[uid] = "own"
        await update.message.reply_text(f"✅ SmartFinder aktiviert:\nWR ≥ {context.user_data['wr']}%\nROI ≥ {roi}%")
        return ConversationHandler.END
    except:
        await update.message.reply_text("Bitte gültige Zahl eingeben:")
        return ROI_INPUT

# Dummy Smart Wallet Scan
async def scan_smart_wallets(app: Application):
    while True:
        await asyncio.sleep(1800)  # 30 Min
        for uid, mode in smartfinder_mode.items():
            filters = user_filter.get(uid, {"wr": 60, "roi": 10})
            wallet = f"8saD...gTq{uid%10}"
            msg = f"""🧠 <b>Neue Smart Wallet entdeckt:</b>\n
🔗 <a href="https://birdeye.so/address/{wallet}?chain=solana">{wallet}</a> – 4.3 SOL – 23 Tage alt  
📈 Winrate: {filters['wr']}% | ROI: {filters['roi']}% | 7d PnL: +2.1 sol  
📊 7d Tokens: 13 | All: 55 | Hodl: 5  
📦 Lifetime PnL: +19.2 sol"""

            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("Dann mal los 🚀", callback_data=f"track:{wallet}")]
            ])
            await app.bot.send_message(CHANNEL_ID, text=msg, parse_mode=constants.ParseMode.HTML, reply_markup=btn)

# FastAPI Webhook
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return {"ok": True}

# Telegram Setup
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="mode:own")],
    states={
        WR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr)],
        ROI_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi)],
    },
    fallbacks=[], per_message=True
))

# Startup
@app.on_event("startup")
async def startup():
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    asyncio.create_task(scan_smart_wallets(application))
    await application.initialize()
    await application.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)