import os
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# FastAPI App definieren – wichtig für Railway!
app = FastAPI()

# Umgebungsvariablen lesen
bot_token = os.getenv("BOT_TOKEN")
channel_id = os.getenv("CHANNEL_ID")
bot = Bot(token=bot_token)

# Getrackte Wallets und PnL-Werte
tracked_wallets = {}  # wallet -> tag
manual_profits = {}   # wallet -> float
winloss_stats = {}    # wallet -> {"win": int, "loss": int}

# Nachricht senden
async def send_message(chat_id: str, text: str):
    await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

# Inline-Tastatur erzeugen für /start
def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_help")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_help")]
    ])

# Bot startet
@app.on_event("startup")
async def startup_event():
    await send_message(channel_id, "✅ <b>RobertsSolTrackerBot ist bereit!</b>")

# Telegram Webhook-Handler
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()

    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = str(query["message"]["chat"]["id"])
        data_id = query["data"]

        if data_id == "add_help":
            await send_message(chat_id, "📥 Um eine Wallet hinzuzufügen:\n<code>/add WALLET TAG</code>")
        elif data_id == "list":
            await handle_list(chat_id)
        elif data_id == "profit_help":
            await send_message(chat_id, "➕ Um Profit hinzuzufügen:\n<code>/profit WALLET +/-BETRAG</code>")
        return {"ok": True}

    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").strip()

    if not text.startswith("/"):
        return {"ok": True}

    if text.startswith("/start"):
        await bot.send_message(
            chat_id=chat_id,
            text="👋 <b>Willkommen beim Solana Wallet Tracker!</b>\nWähle unten eine Funktion aus:",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_buttons()
        )

    elif text.startswith("/add"):
        parts = text.split()
        if len(parts) == 3:
            wallet, tag = parts[1], parts[2]
            tracked_wallets[wallet] = tag
            winloss_stats[wallet] = {"win": 0, "loss": 0}
            await send_message(chat_id, f"✅ Wallet <code>{wallet}</code> mit Tag <b>{tag}</b> hinzugefügt.")
        else:
            await send_message(chat_id, "⚠️ Format: /add WALLET TAG")

    elif text.startswith("/rm"):
        parts = text.split()
        if len(parts) == 2:
            wallet = parts[1]
            if wallet in tracked_wallets:
                del tracked_wallets[wallet]
                manual_profits.pop(wallet, None)
                winloss_stats.pop(wallet, None)
                await send_message(chat_id, f"🗑️ Wallet <code>{wallet}</code> entfernt.")
            else:
                await send_message(chat_id, "❌ Wallet nicht gefunden.")
        else:
            await send_message(chat_id, "⚠️ Format: /rm WALLET")

    elif text.startswith("/profit"):
        parts = text.split()
        if len(parts) == 3:
            wallet, profit_str = parts[1], parts[2]
            if wallet not in tracked_wallets:
                await send_message(chat_id, "❌ Diese Wallet wird nicht getrackt.")
                return
            if profit_str.startswith("+") or profit_str.startswith("-"):
                try:
                    profit = float(profit_str)
                    manual_profits[wallet] = profit
                    await send_message(chat_id, f"💰 Manuell eingetragener Profit für <code>{wallet}</code>: <b>{profit} sol</b>")
                except ValueError:
                    await send_message(chat_id, "❌ Ungültiger Betrag. Beispiel: /profit WALLET +12.3")
            else:
                await send_message(chat_id, "⚠️ Format: /profit WALLET +/-BETRAG")
        else:
            await send_message(chat_id, "⚠️ Format: /profit WALLET +/-BETRAG")

    elif text.startswith("/list"):
        await handle_list(chat_id)

    else:
        await send_message(chat_id, "❌ Befehl existiert nicht. Tippe <code>/start</code> für Hilfe.")

    return {"ok": True}

# Helferfunktion für /list
async def handle_list(chat_id: str):
    if not tracked_wallets:
        await send_message(chat_id, "ℹ️ Keine Wallets getrackt.")
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

    await send_message(chat_id, msg)