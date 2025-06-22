import os
import asyncio
import random
from fastapi import FastAPI, Request
from telegram import (
    Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

app = FastAPI()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
bot = Bot(token=BOT_TOKEN)

# === Datenstrukturen ===
tracked_wallets = {}
manual_profits = {}
winloss_stats = {}
user_filters = {}
scanner_mode = {}

WAITING_FOR_WR, WAITING_FOR_ROI = range(2)

def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_help")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_help")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Willkommen beim Solana Wallet Tracker!\nWähle unten eine Funktion aus:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_buttons()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_id = query.data
    chat_id = query.message.chat.id

    if data_id == "add_help":
        await bot.send_message(chat_id, "📥 Format:\n<code>/add WALLET TAG</code>", parse_mode=ParseMode.HTML)
    elif data_id == "list":
        await handle_list(chat_id)
    elif data_id == "profit_help":
        await bot.send_message(chat_id, "➕ Format:\n<code>/profit WALLET +/-BETRAG</code>", parse_mode=ParseMode.HTML)
    elif data_id == "smartfinder":
        keyboard = [
            [InlineKeyboardButton("🌕 Moonbags", callback_data="sf_moonbags")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="sf_scalping")],
            [InlineKeyboardButton("🛠️ Eigene Filter", callback_data="sf_own")]
        ]
        await bot.send_message(chat_id, "🧠 Wähle einen Modus:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data_id == "sf_moonbags":
        user_filters[chat_id] = {"wr": 75, "roi": 25}
        scanner_mode[chat_id] = "moonbags"
        await bot.send_message(chat_id, "🌕 Moonbags-Filter aktiviert: WR ≥ 75%, ROI ≥ 25%")
    elif data_id == "sf_scalping":
        user_filters[chat_id] = {"wr": 60, "roi": 5}
        scanner_mode[chat_id] = "scalping"
        await bot.send_message(chat_id, "⚡ Scalping-Filter aktiviert: WR ≥ 60%, ROI ≥ 5%")
    elif data_id == "sf_own":
        await bot.send_message(chat_id, "🛠️ Gib deine gewünschte Mindest-Winrate (%) ein:")
        return WAITING_FOR_WR
    elif data_id.startswith("track:"):
        wallet = data_id.split(":")[1]
        tracked_wallets[wallet] = "🚀 AutoDetected"
        winloss_stats[wallet] = {"win": 0, "loss": 0}
        await bot.send_message(chat_id, f"✅ Wallet <code>{wallet}</code> wird jetzt getrackt.", parse_mode=ParseMode.HTML)

async def own_wr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("%", "")
    if not text.isdigit():
        await update.message.reply_text("❌ Bitte gültige Zahl wie 70 oder 70%.")
        return WAITING_FOR_WR
    context.user_data["own_wr"] = int(text)
    await update.message.reply_text("📈 Jetzt bitte ROI (%) eingeben:")
    return WAITING_FOR_ROI

async def own_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("%", "")
    if not text.isdigit():
        await update.message.reply_text("❌ Bitte gültige Zahl wie 10 oder 20%.")
        return WAITING_FOR_ROI
    user_id = update.message.chat.id
    wr = context.user_data["own_wr"]
    roi = int(text)
    user_filters[user_id] = {"wr": wr, "roi": roi}
    scanner_mode[user_id] = "own"
    await update.message.reply_text(f"✅ Eigene Filter gesetzt: WR ≥ {wr}%, ROI ≥ {roi}%")
    return ConversationHandler.END

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) == 3:
        wallet, tag = parts[1], parts[2]
        tracked_wallets[wallet] = tag
        winloss_stats[wallet] = {"win": 0, "loss": 0}
        await update.message.reply_text(f"✅ Wallet <code>{wallet}</code> mit Tag <b>{tag}</b> hinzugefügt.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("⚠️ Format: /add WALLET TAG")

async def rm_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) == 2:
        wallet = parts[1]
        if wallet in tracked_wallets:
            del tracked_wallets[wallet]
            manual_profits.pop(wallet, None)
            winloss_stats.pop(wallet, None)
            await update.message.reply_text(f"🗑️ Wallet <code>{wallet}</code> entfernt.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text("❌ Wallet nicht gefunden.")
    else:
        await update.message.reply_text("⚠️ Format: /rm WALLET")

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()
    if len(parts) == 3:
        wallet, profit_str = parts[1], parts[2]
        if wallet not in tracked_wallets:
            await update.message.reply_text("❌ Diese Wallet wird nicht getrackt.")
            return
        if profit_str.startswith("+") or profit_str.startswith("-"):
            try:
                profit_val = float(profit_str)
                manual_profits[wallet] = profit_val
                if profit_val >= 0:
                    winloss_stats[wallet]["win"] += 1
                else:
                    winloss_stats[wallet]["loss"] += 1
                await update.message.reply_text(
                    f"💰 Profit für <code>{wallet}</code>: <b>{profit_val} sol</b>",
                    parse_mode=ParseMode.HTML
                )
            except ValueError:
                await update.message.reply_text("❌ Ungültiger Betrag. Beispiel: /profit WALLET +12.3")
        else:
            await update.message.reply_text("⚠️ Format: /profit WALLET +/-BETRAG")
    else:
        await update.message.reply_text("⚠️ Format: /profit WALLET +/-BETRAG")

async def handle_list(chat_id: int):
    if not tracked_wallets:
        await bot.send_message(chat_id, "ℹ️ Keine Wallets getrackt.")
        return
    msg = "📋 <b>Getrackte Wallets:</b>\n"
    for idx, (wallet, tag) in enumerate(tracked_wallets.items(), 1):
        link = f"https://birdeye.so/address/{wallet}?chain=solana"
        profit = manual_profits.get(wallet, 0)
        stats = winloss_stats.get(wallet, {"win": 0, "loss": 0})
        wr = f"<b>WR(</b><span style='color:green'>{stats['win']}</span>/<span style='color:red'>{stats['loss']}</span><b>)</b>"
        pnl = f"<b>| PnL(</b><span style='color:{'green' if profit>=0 else 'red'}'>{profit:.2f} sol</span><b>)</b>"
        msg += f"\n<b>{idx}.</b> <a href='{link}'>{wallet}</a> – <i>{tag}</i>\n{wr} {pnl}\n"
    await bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML)

# === Dummy Wallets finden ===
async def scan_for_smart_wallets():
    while True:
        await asyncio.sleep(1800)  # 30 Minuten
        for user_id, filters in user_filters.items():
            wr_min = filters.get("wr", 60)
            roi_min = filters.get("roi", 5)
            for i in range(2):
                wallet = f"AutoWallet{random.randint(1000,9999)}"
                wr = random.randint(50, 90)
                roi = random.randint(0, 40)
                if wr >= wr_min and roi >= roi_min:
                    msg = (
                        f"<b>{wallet}</b> – {round(random.uniform(1, 8),2)} SOL – {random.randint(30, 300)} Tage\n"
                        f"WinRate: {wr}% | ROI: {roi}% | 7d PnL: +{round(random.uniform(0, 5),2)} sol\n"
                        f"7d Tokens: {random.randint(2, 5)} | All Tokens: {random.randint(5, 20)} | Hodl Tokens: {random.randint(1, 4)}\n"
                        f"Lifetime PnL: +{round(random.uniform(1, 10),2)} sol"
                    )
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Dann mal los 🚀", callback_data=f"track:{wallet}")]])
                    await bot.send_message(user_id, msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# === Webhook Handler ===
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    await application.update_queue.put(update)
    return {"ok": True}

# === Init App ===
if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder
    import uvicorn

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_wallet))
    application.add_handler(CommandHandler("rm", rm_wallet))
    application.add_handler(CommandHandler("profit", profit))
    application.add_handler(CommandHandler("list", lambda u, c: asyncio.create_task(handle_list(u.message.chat.id))))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^sf_own$")],
        states={
            WAITING_FOR_WR: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_wr)],
            WAITING_FOR_ROI: [MessageHandler(filters.TEXT & ~filters.COMMAND, own_roi)],
        },
        fallbacks=[]
    ))

    async def run():
        await application.initialize()
        await application.start()
        await bot.set_webhook(url=WEBHOOK_URL)
        asyncio.create_task(scan_for_smart_wallets())
        print("✅ Bot live & Scanner aktiv.")

    asyncio.run(run())
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))