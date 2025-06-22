import os
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

app = FastAPI()
bot_token = os.getenv("BOT_TOKEN")
channel_id = os.getenv("CHANNEL_ID")
bot = Bot(token=bot_token)

tracked_wallets = {}
wallet_stats = {}

DEX_API = "https://api.dexscreener.com/latest/dex/pairs/solana/"
BIRDEYE_URL = "https://birdeye.so/address/"
DEX_LINK = "https://dexscreener.com/solana/"

async def send_message(chat_id: str, text: str):
    await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@app.on_event("startup")
async def startup_event():
    await send_message(channel_id, "👋 Willkommen beim RobertsSolTrackerBot!")
    asyncio.create_task(track_wallets_loop())

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "")

    if not text.startswith("/"):
        return {"ok": True}

    if text.startswith("/start"):
        keyboard = [
            [InlineKeyboardButton("➕ /add", callback_data="help_add"),
             InlineKeyboardButton("📋 /list", callback_data="list_wallets")],
            [InlineKeyboardButton("➖ /rm", callback_data="help_rm"),
             InlineKeyboardButton("💰 /profit", callback_data="help_profit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=chat_id, text="🤖 <b>Wähle einen Befehl:</b>", parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    elif text.startswith("/add"):
        parts = text.split()
        if len(parts) == 3:
            wallet, tag = parts[1], parts[2]
            tracked_wallets[wallet] = tag
            wallet_stats[wallet] = {"wins": 0, "losses": 0, "profit": 0.0}
            await send_message(chat_id, f"✅ Wallet <b>{wallet}</b> mit Tag <b>{tag}</b> hinzugefügt.")
        else:
            await send_message(chat_id, "⚠️ Format: /add <WALLET> <TAG>")

    elif text.startswith("/rm"):
        parts = text.split()
        if len(parts) == 2:
            wallet = parts[1]
            if wallet in tracked_wallets:
                del tracked_wallets[wallet]
                wallet_stats.pop(wallet, None)
                await send_message(chat_id, f"🗑️ Wallet <b>{wallet}</b> entfernt.")
            else:
                await send_message(chat_id, f"❌ Wallet <b>{wallet}</b> nicht gefunden.")
        else:
            await send_message(chat_id, "⚠️ Format: /rm <WALLET>")

    elif text.startswith("/profit"):
        parts = text.split()
        if len(parts) == 3 and parts[2][0] in ['+', '-']:
            wallet = parts[1]
            value = parts[2]
            try:
                amount = float(value)
                if wallet in wallet_stats:
                    wallet_stats[wallet]["profit"] += amount
                    await send_message(chat_id, f"📈 PnL für Wallet <b>{wallet}</b> aktualisiert: <b>{amount:.2f} SOL</b>")
                else:
                    await send_message(chat_id, f"❌ Wallet <b>{wallet}</b> nicht gefunden.")
            except ValueError:
                await send_message(chat_id, "❌ Ungültiger Betrag.")
        else:
            await send_message(chat_id, "⚠️ Format: /profit <WALLET> <+/–BETRAG>")

    elif text.startswith("/list"):
        if tracked_wallets:
            message = "📋 <b>Getrackte Wallets:</b>\n\n"
            for i, (wallet, tag) in enumerate(tracked_wallets.items(), start=1):
                stats = wallet_stats.get(wallet, {"wins": 0, "losses": 0, "profit": 0.0})
                wr = f"WR(<b><span style='color:green'>{stats['wins']}</span>/<span style='color:red'>{stats['losses']}</span></b>)"
                pnl = f"<span style='color:green'>PnL({stats['profit']:.2f} SOL)</span>" if stats["profit"] >= 0 else f"<span style='color:red'>PnL({stats['profit']:.2f} SOL)</span>"
                message += f"{i}. <a href='{BIRDEYE_URL}{wallet}'>{wallet}</a> – <i>{tag}</i>\n {wr} | {pnl}\n\n"
        else:
            message = "ℹ️ Keine Wallets getrackt."
        await send_message(chat_id, message)

    else:
        await send_message(chat_id, "❌ Unbekannter Befehl.")

    return {"ok": True}

@app.post("/callback")
async def telegram_callback(req: Request):
    data = await req.json()
    callback = data.get("callback_query", {})
    message = callback.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    data_text = callback.get("data")

    if data_text == "help_add":
        await send_message(chat_id, "📝 Format: /add WALLET TAG")
    elif data_text == "list_wallets":
        await send_message(chat_id, "/list")
    elif data_text == "help_rm":
        await send_message(chat_id, "🗑️ Format: /rm WALLET")
    elif data_text == "help_profit":
        await send_message(chat_id, "💰 Format: /profit WALLET +/-BETRAG")

    return {"ok": True}

async def track_wallets_loop():
    last_tx = {}
    while True:
        for wallet in tracked_wallets:
            url = f"https://public-api.solscan.io/account/splTransfers?account={wallet}&limit=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"accept": "application/json"}) as resp:
                    if resp.status == 200:
                        txs = await resp.json()
                        if txs and isinstance(txs, list):
                            tx = txs[0]
                            tx_id = tx.get("signature")
                            token = tx.get("tokenSymbol")
                            amount = float(tx.get("changeAmount", 0)) / 10**6
                            tx_type = "📉 Verkauf" if "-" in tx.get("changeAmount", "") else "📈 Kauf"

                            if wallet not in last_tx or last_tx[wallet] != tx_id:
                                last_tx[wallet] = tx_id
                                token_address = tx.get("tokenAddress", "")
                                tag = tracked_wallets[wallet]
                                birdeye_link = f"{BIRDEYE_URL}{wallet}"
                                dex_link = f"{DEX_LINK}{token_address}"

                                msg = f"""{tx_type} durch <a href="{birdeye_link}">{wallet}</a> ({tag})
<b>{abs(amount):.4f}</b> {token} → <a href="{dex_link}">Dexscreener</a>"""
                                await send_message(channel_id, msg)

                                # Winrate Auswertung (nur SELL)
                                if tx_type == "📉 Verkauf":
                                    # dummy evaluation
                                    is_win = amount > 0
                                    wallet_stats[wallet]["wins" if is_win else "losses"] += 1
                                    wallet_stats[wallet]["profit"] += amount

        await asyncio.sleep(60)