import os
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ParseMode

app = FastAPI()

bot_token = os.getenv("BOT_TOKEN")
channel_id = os.getenv("CHANNEL_ID")
bot = Bot(token=bot_token)

tracked_wallets = {}
manual_profits = {}
winloss_stats = {}

async def send_message(chat_id: str, text: str):
    await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

def get_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Wallet hinzufügen", callback_data="add_help")],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data="list")],
        [InlineKeyboardButton("🗑️ Wallet entfernen", callback_data="rm_list")],
        [InlineKeyboardButton("➕ Profit eintragen", callback_data="profit_help")]
    ])

async def fetch_smart_wallets():
    # Dummy Wallets – hier kannst du später eine echte API wie Dune einbauen
    return [
        {"wallet": "9xyzSmartWallet1", "winrate": 68, "roi": 24},
        {"wallet": "4abcNewWallet2", "winrate": 70, "roi": 30}
    ]

async def wallet_discovery_loop():
    await asyncio.sleep(5)
    while True:
        try:
            smart_wallets = await fetch_smart_wallets()
            for entry in smart_wallets:
                wallet = entry["wallet"]
                if wallet not in tracked_wallets:
                    tag = "🚀 AutoDetected"
                    tracked_wallets[wallet] = tag
                    winloss_stats[wallet] = {"win": 0, "loss": 0}
                    await send_message(
                        channel_id,
                        f"🧠 Neue Smart Wallet entdeckt:\n<code>{wallet}</code> – WR: {entry['winrate']} % | ROI: {entry['roi']} %\n<a href='https://birdeye.so/address/{wallet}?chain=solana'>📈 Birdeye öffnen</a>"
                    )
        except Exception as e:
            await send_message(channel_id, f"❌ Fehler beim Wallet-Scan: {e}")
        await asyncio.sleep(1800)

@app.on_event("startup")
async def startup_event():
    await send_message(channel_id, "✅ <b>RobertsSolTrackerBot ist bereit!</b>")
    await bot.set_my_commands([
        BotCommand("start", "Startmenü anzeigen"),
        BotCommand("add", "Wallet hinzufügen"),
        BotCommand("rm", "Wallet entfernen"),
        BotCommand("profit", "Profit eintragen"),
        BotCommand("list", "Alle Wallets anzeigen")
    ])
    asyncio.create_task(wallet_discovery_loop())

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
        elif data_id == "rm_list":
            if not tracked_wallets:
                await send_message(chat_id, "ℹ️ Keine Wallets zum Entfernen.")
                return
            buttons = [[InlineKeyboardButton(f"{tag}", callback_data=f"rm_wallet_{wallet}")]
                       for wallet, tag in tracked_wallets.items()]
            await bot.send_message(
                chat_id=chat_id,
                text="🗑️ Wähle eine Wallet aus, um sie zu entfernen:",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        elif data_id.startswith("rm_wallet_"):
            wallet = data_id.replace("rm_wallet_", "")
            if wallet in tracked_wallets:
                del tracked_wallets[wallet]
                manual_profits.pop(wallet, None)
                winloss_stats.pop(wallet, None)
                await send_message(chat_id, f"🗑️ Wallet <code>{wallet}</code> entfernt.")
            else:
                await send_message(chat_id, "❌ Wallet nicht gefunden.")
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
            if not tracked_wallets:
                await send_message(chat_id, "ℹ️ Keine Wallets zum Entfernen.")
            else:
                buttons = [[InlineKeyboardButton(f"{tag}", callback_data=f"rm_wallet_{wallet}")]
                           for wallet, tag in tracked_wallets.items()]
                await bot.send_message(
                    chat_id=chat_id,
                    text="🗑️ Wähle eine Wallet aus, um sie zu entfernen:",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML
                )

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