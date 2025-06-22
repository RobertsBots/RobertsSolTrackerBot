import os
import asyncio
from fastapi import FastAPI, Request
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WR_INPUT, ROI_INPUT = range(2)

app = FastAPI()
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

tracked_wallets = {}        # wallet -> tag
manual_profits = {}         # wallet -> float
winloss_stats = {}          # wallet -> {"win": int, "loss": int}
user_filters = {}           # user_id -> {"wr": int, "roi": int}


# === Webhook Route ===
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}


# === UI Buttons ===
def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_help")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_help")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder")]
    ])

def smartfinder_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 Moonbags", callback_data="moonbags")],
        [InlineKeyboardButton("⚡️ Scalping", callback_data="scalping")],
        [InlineKeyboardButton("🛠 Own", callback_data="own")]
    ])


# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Willkommen beim Solana Wallet Tracker!\nWähle unten eine Funktion aus:",
        reply_markup=main_buttons(),
        parse_mode=ParseMode.HTML
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "add_help":
        await query.message.reply_text("📥 Beispiel: /add <wallet> <tag>")
    elif data == "list":
        await handle_list(query.message.chat_id)
    elif data == "profit_help":
        await query.message.reply_text("➕ Beispiel: /profit <wallet> +12.5")
    elif data == "smartfinder":
        await query.message.reply_text("🔍 SmartFinder-Modus wählen:", reply_markup=smartfinder_buttons())
    elif data == "moonbags":
        user_filters[query.from_user.id] = {"wr": 70, "roi": 20}
        await query.message.reply_text("🟡 Moonbags aktiviert: WR≥70%, ROI≥20%")
    elif data == "scalping":
        user_filters[query.from_user.id] = {"wr": 60, "roi": 5}
        await query.message.reply_text("⚡️ Scalping aktiviert: WR≥60%, ROI≥5%")
    elif data == "own":
        await query.message.reply_text("🛠 Gib deine gewünschte Mindest-Winrate (%) ein:")
        return WR_INPUT

async def own_wr_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wr = int(update.message.text.strip('% '))
        context.user_data["wr"] = wr
        await update.message.reply_text("🔧 Gib deinen gewünschten Mindest-ROI (%) ein:")
        return ROI_INPUT
    except ValueError:
        await update.message.reply_text("❌ Ungültige Winrate. Bitte Zahl eingeben.")
        return WR_INPUT

async def own_roi_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        roi = int(update.message.text.strip('% '))
        user_id = update.effective_user.id
        user_filters[user_id] = {"wr": context.user_data["wr"], "roi": roi}
        await update.message.reply_text(f"✅ Filter gesetzt: WR≥{context.user_data['wr']}%, ROI≥{roi}%")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Ungültiger ROI. Bitte Zahl eingeben.")
        return ROI_INPUT


# === Befehle ===
async def handle_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, wallet, tag = update.message.text.split()
        tracked_wallets[wallet] = tag
        winloss_stats[wallet] = {"win": 0, "loss": 0}
        await update.message.reply_text(f"✅ Wallet <code>{wallet}</code> mit Tag <b>{tag}</b> hinzugefügt.", parse_mode=ParseMode.HTML)
    except:
        await update.message.reply_text("❌ Format: /add <wallet> <tag>")

async def handle_rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, wallet = update.message.text.split()
        if wallet in tracked_wallets:
            tracked_wallets.pop(wallet)
            manual_profits.pop(wallet, None)
            winloss_stats.pop(wallet, None)
            await update.message.reply_text(f"🗑 Wallet <code>{wallet}</code> entfernt.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text("❌ Wallet nicht gefunden.")
    except:
        await update.message.reply_text("❌ Format: /rm <wallet>")

async def handle_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, wallet, amount = update.message.text.split()
        amount = float(amount.replace('+', '').replace('sol', ''))
        manual_profits[wallet] = amount
        await update.message.reply_text(f"💰 Profit für {wallet} gesetzt: {amount} sol")
    except:
        await update.message.reply_text("❌ Format: /profit <wallet> +/-betrag")

async def handle_list(chat_id):
    if not tracked_wallets:
        await bot.send_message(chat_id, "ℹ️ Keine Wallets getrackt.")
        return

    msg = "📋 <b>Getrackte Wallets:</b>\n"
    for idx, (wallet, tag) in enumerate(tracked_wallets.items(), 1):
        bird_link = f"https://birdeye.so/address/{wallet}?chain=solana"
        profit = manual_profits.get(wallet, 0)
        stats = winloss_stats.get(wallet, {"win": 0, "loss": 0})
        win, loss = stats["win"], stats["loss"]

        wr = f"<b>WR(</b><span style='color:green'>{win}</span>/<span style='color:red'>{loss}</span><b>)</b>"
        pnl = f"<b> | PnL(</b><span style='color:{'green' if profit >= 0 else 'red'}'>{profit:.2f} sol</span><b>)</b>"

        msg += f"\n<b>{idx}.</b> <a href='{bird_link}'>{wallet}</a> – <i>{tag}</i>\n{wr}{pnl}\n"

    await bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML)


# === Background Scanner Dummy ===
async def smart_wallet_scanner():
    while True:
        for user_id, filters in user_filters.items():
            wr, roi = filters["wr"], filters["roi"]
            if wr >= 60 and roi >= 5:
                text = (
                    f"<b>🧠 Smart Wallet gefunden!</b>\n"
                    f"<a href='https://birdeye.so/address/FakeWallet123'>FakeWallet123</a> – 8.1 SOL – 103 Tage\n"
                    f"WinRate: {wr}% | ROI: {roi}% | 7d PnL: +2.3 sol\n"
                    f"7d Tokens: 5 | All Tokens: 19 | Hodl Tokens: 4\n"
                    f"Lifetime PnL: +12.7 sol"
                )
                await bot.send_message(CHANNEL_ID, text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(1800)


# === Initialisierung ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", handle_add))
application.add_handler(CommandHandler("rm", handle_rm))
application.add_handler(CommandHandler("profit", handle_profit))
application.add_handler(CallbackQueryHandler(handle_callback))

application.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_callback, pattern="^own$")],
    states={
        WR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr_input)],
        ROI_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi_input)],
    },
    fallbacks=[]
))

async def main():
    await application.initialize()
    await application.start()
    asyncio.create_task(smart_wallet_scanner())
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    import uvicorn
    asyncio.run(main())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))