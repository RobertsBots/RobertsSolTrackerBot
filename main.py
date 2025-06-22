
import json
import os
import time
import asyncio
import httpx
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import ApplicationBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

wallets_file = "wallets.json"
app = FastAPI()
bot = Bot(token=BOT_TOKEN)

telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

def load_wallets():
    if not os.path.exists(wallets_file):
        return {}
    with open(wallets_file, "r") as f:
        return json.load(f)

def save_wallets(data):
    with open(wallets_file, "w") as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Willkommen beim RobertsSolTrackerBot!")

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ Benutze: /add WALLET TAG")
        return
    wallet, tag = args
    data = load_wallets()
    data[wallet] = {"tag": tag, "last_tx": ""}
    save_wallets(data)
    await update.message.reply_text(f"✅ Wallet {wallet} unter '{tag}' gespeichert.")

async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("❌ Benutze: /rm WALLET")
        return
    wallet = args[0]
    data = load_wallets()
    if wallet in data:
        del data[wallet]
        save_wallets(data)
        await update.message.reply_text(f"🗑️ Wallet {wallet} gelöscht.")
    else:
        await update.message.reply_text("⚠️ Wallet nicht gefunden.")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_wallets()
    if not data:
        await update.message.reply_text("📭 Keine Wallets gespeichert.")
        return
    reply = "📋 Getrackte Wallets:\n"
    for wallet, info in data.items():
        reply += f"- {wallet} ({info['tag']})\n"
    await update.message.reply_text(reply)

def get_dexscreener_link(token_address):
    return f"https://dexscreener.com/solana/{token_address}"

async def check_wallet_activity():
    while True:
        data = load_wallets()
        for wallet, info in data.items():
            async with httpx.AsyncClient() as client:
                url = f"https://api.solscan.io/account/transactions?address={wallet}&limit=1"
                try:
                    res = await client.get(url)
                    txs = res.json().get("data", [])
                except Exception:
                    continue

                if not txs:
                    continue

                latest = txs[0]
                tx_hash = latest.get("txHash")
                if tx_hash and tx_hash != info["last_tx"]:
                    info["last_tx"] = tx_hash
                    save_wallets(data)

                    token_address = latest.get("token", {}).get("tokenAddress", "unknown")
                    link = get_dexscreener_link(token_address)
                    action = latest.get("type", "Trade")
                    msg = (
                        f"📈 Neue Aktivität von *{info['tag']}*\n\n"
                        f"🧾 Tx: `{tx_hash}`\n"
                        f"⚡️ Typ: {action}\n"
                        f"🔗 [Dexscreener]({link})"
                    )
                    await bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown", disable_web_page_preview=True)
        await asyncio.sleep(60)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("add", add_wallet))
telegram_app.add_handler(CommandHandler("rm", remove_wallet))
telegram_app.add_handler(CommandHandler("list", list_wallets))

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    await telegram_app.update_queue.put(Update.de_json(data, bot))
    return {"ok": True}

@app.on_event("startup")
async def startup():
    asyncio.create_task(check_wallet_activity())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8080, host="0.0.0.0", reload=True)
