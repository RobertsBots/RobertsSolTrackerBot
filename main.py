# ... IMPORTS
import os
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ParseMode

# INIT
app = FastAPI()
bot = Bot(token=os.getenv("BOT_TOKEN"))
channel_id = os.getenv("CHANNEL_ID")

# DATA
tracked_wallets = {}
manual_profits = {}
winloss_stats = {}
smartfinder_active = False
smartfinder_mode = "moonbags"
custom_filters = {"wr": 60, "roi": 10}
pending_filter_input = {}  # chat_id -> {"step": ..., "wr": ...}

# BUTTONS
def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_help")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("🧠 Smart Finder", callback_data="smartfinder")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_help")]
    ])

def get_smartfinder_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌕 Moonbags", callback_data="mode_moonbags")],
        [InlineKeyboardButton("⚡ Scalping", callback_data="mode_scalping")],
        [InlineKeyboardButton("⚙️ Eigene Filter", callback_data="mode_own")]
    ])

def smartfinder_filters():
    if smartfinder_mode == "moonbags": return {"wr": 65, "roi": 20}
    if smartfinder_mode == "scalping": return {"wr": 60, "roi": 5}
    return custom_filters

# STARTUP
@app.on_event("startup")
async def startup_event():
    await bot.set_my_commands([
        BotCommand("start", "Startmenü anzeigen"),
        BotCommand("add", "Wallet hinzufügen"),
        BotCommand("rm", "Wallet entfernen"),
        BotCommand("profit", "Profit eintragen"),
        BotCommand("list", "Wallet-Liste anzeigen"),
        BotCommand("smartfinder", "Smart Wallet Scanner öffnen"),
        BotCommand("smartfinder_start", "Scanner aktivieren"),
        BotCommand("smartfinder_stop", "Scanner deaktivieren"),
        BotCommand("moonbags", "Moonbags-Modus aktivieren"),
        BotCommand("scalping", "Scalping-Modus aktivieren"),
        BotCommand("own", "Eigene Filter setzen")
    ])
    await send_message(channel_id, "✅ <b>RobertsSolTrackerBot ist bereit!</b>")
    asyncio.create_task(smartfinder_loop())

# SCANNER
async def fetch_smart_wallets():
    return [{
        "wallet": "4abcSmartWallet",
        "winrate": 70,
        "roi": 22,
        "sol": 2.3,
        "age": 81,
        "pnl7d": "+58",
        "tok7d": 7,
        "tok_total": 19,
        "hodl": 2,
        "pnl_life": "+211"
    }]

async def smartfinder_loop():
    await asyncio.sleep(5)
    while True:
        if smartfinder_active:
            for entry in await fetch_smart_wallets():
                f = smartfinder_filters()
                if entry["winrate"] >= f["wr"] and entry["roi"] >= f["roi"]:
                    wallet = entry["wallet"]
                    if wallet not in tracked_wallets:
                        tracked_wallets[wallet] = "🚀 AutoDetected"
                        winloss_stats[wallet] = {"win": 0, "loss": 0}
                        await bot.send_message(
                            chat_id=channel_id,
                            text=(
                                f"<a href='https://birdeye.so/address/{wallet}?chain=solana'>{wallet}</a> – 💰 {entry['sol']} SOL – 🕓 {entry['age']} Tage alt\n"
                                f"📊 WR: {entry['winrate']} % | ROI: {entry['roi']} % | 7d PnL: {entry['pnl7d']} SOL\n"
                                f"🔄 7d Tokens: {entry['tok7d']} | All Tokens: {entry['tok_total']} | Hodl: {entry['hodl']}\n"
                                f"📈 Lifetime PnL: {entry['pnl_life']} SOL"
                            ),
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("🚀 Dann mal los", callback_data=f"track_{wallet}")]
                            ]),
                            parse_mode=ParseMode.HTML
                        )
        await asyncio.sleep(1800)

# WEBHOOK
@app.post("/")
async def telegram_webhook(req: Request):
    global smartfinder_active, smartfinder_mode, custom_filters
    data = await req.json()
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").strip().lower()

    if chat_id in pending_filter_input:
        step = pending_filter_input[chat_id]["step"]
        try:
            val = int(text)
            if step == "wr":
                pending_filter_input[chat_id] = {"step": "roi", "wr": val}
                await send_message(chat_id, "✅ Winrate gespeichert. Bitte gib nun den Mindest-ROI ein (z. B. 10):")
            elif step == "roi":
                wr = pending_filter_input[chat_id]["wr"]
                custom_filters = {"wr": wr, "roi": val}
                smartfinder_mode = "own"
                del pending_filter_input[chat_id]
                await send_message(chat_id, f"✅ Eigene Filter aktiviert:\nWR ≥ {wr} % | ROI ≥ {val} %")
        except:
            await send_message(chat_id, "❌ Ungültige Zahl. Bitte erneut eingeben.")
        return {"ok": True}

    if "callback_query" in data:
        q = data["callback_query"]
        chat_id = str(q["message"]["chat"]["id"])
        data_id = q["data"]
        if data_id == "add_help":
            await send_message(chat_id, "📥 Nutze: <code>/add WALLET TAG</code>")
        elif data_id == "list":
            await handle_list(chat_id)
        elif data_id == "profit_help":
            await send_message(chat_id, "➕ Nutze: <code>/profit WALLET +/-BETRAG</code>")
        elif data_id == "smartfinder":
            await send_message(chat_id, "🧠 Wähle SmartFinder-Modus:", reply_markup=get_smartfinder_buttons())
        elif data_id.startswith("mode_"):
            smartfinder_mode = data_id.split("_")[1]
            await send_message(chat_id, f"✅ Modus <b>{smartfinder_mode.title()}</b> aktiviert.")
        elif data_id.startswith("track_"):
            wallet = data_id.replace("track_", "")
            tracked_wallets[wallet] = "🚀 AutoTracked"
            winloss_stats[wallet] = {"win": 0, "loss": 0}
            await send_message(chat_id, f"✅ Wallet <code>{wallet}</code> wird nun getrackt.")
        return {"ok": True}

    if text.startswith("/start"):
        await send_message(chat_id, "👋 Willkommen!\nWähle unten:", reply_markup=get_main_buttons())
    elif text.startswith("/smartfinder"):
        await send_message(chat_id, "🧠 SmartFinder geöffnet.", reply_markup=get_smartfinder_buttons())
    elif text.startswith("/smartfinder_start"):
        smartfinder_active = True
        await send_message(chat_id, "✅ SmartFinder aktiviert.")
    elif text.startswith("/smartfinder_stop"):
        smartfinder_active = False
        await send_message(chat_id, "🛑 SmartFinder deaktiviert.")
    elif text.startswith("/moonbags"):
        smartfinder_mode = "moonbags"
        await send_message(chat_id, "🌕 Moonbags-Modus aktiviert.")
    elif text.startswith("/scalping"):
        smartfinder_mode = "scalping"
        await send_message(chat_id, "⚡ Scalping-Modus aktiviert.")
    elif text.startswith("/own"):
        pending_filter_input[chat_id] = {"step": "wr"}
        await send_message(chat_id, "📊 Bitte gib gewünschte Mindest-Winrate ein (z. B. 60):")
    elif text.startswith("/add"):
        parts = text.split()
        if len(parts) == 3:
            tracked_wallets[parts[1]] = parts[2]
            winloss_stats[parts[1]] = {"win": 0, "loss": 0}
            await send_message(chat_id, f"✅ Wallet <code>{parts[1]}</code> hinzugefügt.")
    elif text.startswith("/rm"):
        parts = text.split()
        if len(parts) == 2:
            wallet = parts[1]
            tracked_wallets.pop(wallet, None)
            manual_profits.pop(wallet, None)
            winloss_stats.pop(wallet, None)
            await send_message(chat_id, f"🗑️ Wallet <code>{wallet}</code> entfernt.")
    elif text.startswith("/profit"):
        parts = text.split()
        if len(parts) == 3 and parts[1] in tracked_wallets:
            try:
                manual_profits[parts[1]] = float(parts[2])
                await send_message(chat_id, f"💰 Profit für <code>{parts[1]}</code>: <b>{parts[2]} sol</b>")
            except:
                await send_message(chat_id, "❌ Ungültiger Betrag.")
    elif text.startswith("/list"):
        await handle_list(chat_id)

    return {"ok": True}

async def handle_list(chat_id: str):
    if not tracked_wallets:
        await send_message(chat_id, "ℹ️ Keine Wallets getrackt.")
        return
    msg = "📋 <b>Getrackte Wallets:</b>\n"
    for idx, (wallet, tag) in enumerate(tracked_wallets.items(), 1):
        bird_link = f"https://birdeye.so/address/{wallet}?chain=solana"
        profit = manual_profits.get(wallet, 0)
        stats = winloss_stats.get(wallet, {"win": 0, "loss": 0})
        wr = f"<b>WR(</b><span style='color:green'>{stats['win']}</span>/<span style='color:red'>{stats['loss']}</span><b>)</b>"
        pnl = f"<b> | PnL(</b><span style='color:{'green' if profit >= 0 else 'red'}'>{profit:.2f} sol</span><b>)</b>"
        msg += f"\n<b>{idx}.</b> <a href='{bird_link}'>{wallet}</a> – <i>{tag}</i>\n{wr}{pnl}\n"
    await send_message(chat_id, msg)