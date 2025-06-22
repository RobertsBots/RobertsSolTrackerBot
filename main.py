import logging
import requests
import time
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7953666029:AAEKunPOhUdeoS-57OlTDuZbRoOTgGY5P5o"
CHANNEL_ID = "-4690026526"
WALLETS_FILE = "wallets.json"

if not os.path.exists(WALLETS_FILE):
    with open(WALLETS_FILE, "w") as f:
        json.dump({}, f)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_wallets():
    with open(WALLETS_FILE, "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open(WALLETS_FILE, "w") as f:
        json.dump(wallets, f)

def get_sol_balance(wallet):
    url = f"https://api.solscan.io/account/tokens?account={wallet}"
    try:
        response = requests.get(url)
        data = response.json()
        sol = next((x for x in data if x.get("tokenSymbol") == "SOL"), None)
        return float(sol.get("tokenAmount", {}).get("uiAmount", 0)) if sol else 0
    except:
        return 0

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /add <wallet_address> <tag>")
        return
    wallet, tag = context.args
    wallets = load_wallets()
    wallets[wallet] = tag
    save_wallets(wallets)
    await update.message.reply_text(f"✅ Wallet {wallet} mit Tag '{tag}' wurde hinzugefügt.")

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /rm <wallet_address>")
        return
    wallet = context.args[0]
    wallets = load_wallets()
    if wallet in wallets:
        del wallets[wallet]
        save_wallets(wallets)
        await update.message.reply_text(f"✅ Wallet {wallet} wurde entfernt.")
    else:
        await update.message.reply_text("⚠️ Wallet nicht gefunden.")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallets = load_wallets()
    if not wallets:
        await update.message.reply_text("📭 Keine Wallets vorhanden.")
        return
    text = "📄 Getrackte Wallets:
"
    for w, t in wallets.items():
        text += f"• {t} → `{w}`
"
    await update.message.reply_text(text, parse_mode="Markdown")

async def check_wallets(app):
    last_tx = {}
    while True:
        wallets = load_wallets()
        for wallet, tag in wallets.items():
            url = f"https://api.solscan.io/account/transactions?account={wallet}&limit=1"
            try:
                response = requests.get(url)
                txs = response.json()
                if not txs:
                    continue
                tx = txs[0]
                sig = tx.get("signature")
                if wallet not in last_tx or last_tx[wallet] != sig:
                    last_tx[wallet] = sig
                    token_info = tx.get("changeTokenInfo", [{}])[0]
                    token_symbol = token_info.get("tokenSymbol", "UNKNOWN")
                    token_address = token_info.get("tokenAddress", "")
                    action = tx.get("changeType", "UNKNOWN").upper()
                    link = f"https://dexscreener.com/solana/{token_address}"
                    balance = get_sol_balance(wallet)
                    message = f"📣 {action} | {tag}
💰 Token: {token_symbol}
🔗 {link}
💼 Balance: {balance:.4f} SOL"
                    await app.bot.send_message(chat_id=CHANNEL_ID, text=message)
            except Exception as e:
                logger.error(f"Fehler bei Wallet {wallet}: {e}")
        time.sleep(60)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("rm", rm))
    app.add_handler(CommandHandler("list", list_wallets))

    app.create_task(check_wallets(app))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
