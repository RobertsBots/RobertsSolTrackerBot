import os
import logging
import asyncio
import aiohttp
from telegram import (
    BotCommand,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Init
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
tracked_wallets = {}
wallet_stats = {}  # Für WR & Profit
SCAN_INTERVAL = 60  # Sekunden

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 📦 Nachricht senden
async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: str, text: str):
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)


# 📋 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("➕ Add", callback_data="help_add"),
            InlineKeyboardButton("🗑️ Remove", callback_data="help_rm"),
        ],
        [
            InlineKeyboardButton("📋 List", callback_data="cmd_list"),
            InlineKeyboardButton("💰 Profit", callback_data="help_profit"),
        ],
    ]
    await update.message.reply_text("🤖 Wähle einen Befehl:", reply_markup=InlineKeyboardMarkup(keyboard))


# 🔘 Button Reaktion
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "help_add":
        await query.message.reply_text("➕ Um eine Wallet hinzuzufügen, nutze:\n<code>/add WALLET TAG</code>", parse_mode=ParseMode.HTML)
    elif data == "help_rm":
        await query.message.reply_text("🗑️ Um eine Wallet zu entfernen, nutze:\n<code>/rm WALLET</code>", parse_mode=ParseMode.HTML)
    elif data == "cmd_list":
        await list_wallets(update, context)
    elif data == "help_profit":
        await query.message.reply_text("💰 Um Profit manuell zu setzen:\n<code>/profit WALLET +/-BETRAG</code>", parse_mode=ParseMode.HTML)


# ➕ Wallet hinzufügen
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) == 2:
        wallet, tag = args
        tracked_wallets[wallet] = tag
        wallet_stats.setdefault(wallet, {"wins": 0, "losses": 0, "pnl": 0.0})
        await send_message(context, update.effective_chat.id, f"✅ Wallet <b>{wallet}</b> mit Tag <b>{tag}</b> hinzugefügt.")
    else:
        await send_message(context, update.effective_chat.id, "⚠️ Format: /add WALLET TAG")


# 🗑️ Wallet entfernen
async def rm_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) == 1:
        wallet = args[0]
        if wallet in tracked_wallets:
            del tracked_wallets[wallet]
            wallet_stats.pop(wallet, None)
            await send_message(context, update.effective_chat.id, f"🗑️ Wallet <b>{wallet}</b> entfernt.")
        else:
            await send_message(context, update.effective_chat.id, f"❌ Wallet <b>{wallet}</b> nicht gefunden.")
    else:
        await send_message(context, update.effective_chat.id, "⚠️ Format: /rm WALLET")


# 📋 List anzeigen
async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_wallets:
        await send_message(context, update.effective_chat.id, "ℹ️ Keine Wallets getrackt.")
        return

    message = "📋 <b>Getrackte Wallets:</b>\n"
    for i, (wallet, tag) in enumerate(tracked_wallets.items(), 1):
        stats = wallet_stats.get(wallet, {"wins": 0, "losses": 0, "pnl": 0})
        wr_green = f"<b><font color='green'>{stats['wins']}</font></b>"
        wr_red = f"<b><font color='red'>{stats['losses']}</font></b>"
        pnl_color = "green" if stats["pnl"] >= 0 else "red"
        pnl_value = f"{abs(stats['pnl']):.2f} sol"
        message += (
            f"\n<b>{i}.</b> <a href='https://birdeye.so/address/{wallet}?chain=solana'>{tag}</a>\n"
            f"• <code>{wallet}</code>\n"
            f"• WR({wr_green}/{wr_red}) | <b><font color='{pnl_color}'>PnL({'+' if stats['pnl'] >= 0 else '-'}{pnl_value})</font></b>\n"
        )
    await send_message(context, update.effective_chat.id, message)


# 💰 Profit manuell eintragen
async def set_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) == 2 and (args[1].startswith("+") or args[1].startswith("-")):
        wallet, value = args
        try:
            profit = float(value)
            wallet_stats.setdefault(wallet, {"wins": 0, "losses": 0, "pnl": 0.0})
            wallet_stats[wallet]["pnl"] += profit
            await send_message(context, update.effective_chat.id, f"💰 Neuer Profit für <b>{wallet}</b> gesetzt: {profit:+.2f} sol")
        except ValueError:
            await send_message(context, update.effective_chat.id, "⚠️ Bitte gib einen gültigen Profitbetrag an (z. B. +1.2 oder -0.5).")
    else:
        await send_message(context, update.effective_chat.id, "⚠️ Format: /profit WALLET +/-BETRAG")


# 🔁 Periodischer Scanner (alle 60s)
async def scanner(app: Application):
    async with aiohttp.ClientSession() as session:
        while True:
            for wallet in tracked_wallets:
                url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{wallet}"
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # Hier müsste eine Logik rein, um Käufe/Verkäufe zu identifizieren
                            # und Win/Loss zuzuordnen.
                            # Beispiel-Schema:
                            # wallet_stats[wallet]["wins"] += 1
                            # → await app.bot.send_message(...)

                except Exception as e:
                    logger.warning(f"Fehler beim Scannen von {wallet}: {e}")
            await asyncio.sleep(SCAN_INTERVAL)


# 🛠️ Undefinierte Nachrichten ignorieren
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith("/"):
        await send_message(context, update.effective_chat.id, "❌ Befehl nicht erkannt. Nutze /start für Hilfe.")
    else:
        pass  # Ignorieren


# 🚀 Start
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_wallet))
    application.add_handler(CommandHandler("rm", rm_wallet))
    application.add_handler(CommandHandler("list", list_wallets))
    application.add_handler(CommandHandler("profit", set_profit))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Scanner
    application.job_queue.run_once(lambda ctx: asyncio.create_task(scanner(application)), when=0)

    # Webhook starten
    PORT = int(os.getenv("PORT", "8000"))
    await application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://{os.getenv('RAILWAY_STATIC_URL')}/"
    )


if __name__ == "__main__":
    asyncio.run(main())