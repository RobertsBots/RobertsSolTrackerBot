
import os
import time
import json
import requests
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TRACKED_WALLETS_FILE = "tracked_wallets.json"

if not os.path.exists(TRACKED_WALLETS_FILE):
    with open(TRACKED_WALLETS_FILE, "w") as f:
        json.dump({}, f)

def load_wallets():
    with open(TRACKED_WALLETS_FILE, "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open(TRACKED_WALLETS_FILE, "w") as f:
        json.dump(wallets, f)

async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Nutzung: /add <WALLET> <TAG>")
        return
    wallet, tag = context.args
    wallets = load_wallets()
    wallets[wallet] = tag
    save_wallets(wallets)
    await update.message.reply_text(f"Wallet {wallet} mit Tag '{tag}' wurde hinzugefügt.")

async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Nutzung: /rm <WALLET>")
        return
    wallet = context.args[0]
    wallets = load_wallets()
    if wallet in wallets:
        del wallets[wallet]
        save_wallets(wallets)
        await update.message.reply_text(f"Wallet {wallet} wurde entfernt.")
    else:
        await update.message.reply_text(f"Wallet {wallet} wurde nicht gefunden.")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallets = load_wallets()
    if not wallets:
        await update.message.reply_text("Es werden derzeit keine Wallets getrackt.")
        return
    msg = "Getrackte Wallets:
"
    for w, tag in wallets.items():
        msg += f"{w} - {tag}
"
    await update.message.reply_text(msg)

def fetch_wallet_activity(wallet):
    url = f"https://api.solscan.io/account/tokens?account={wallet}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("Fehler bei Wallet-Request:", e)
    return None

def wallet_scanner():
    old_balances = {}
    while True:
        wallets = load_wallets()
        for wallet, tag in wallets.items():
            data = fetch_wallet_activity(wallet)
            if not data:
                continue
            sol_url = f"https://solscan.io/account/{wallet}"
            message = f"📡 Update für *{tag}*
[Wallet]({sol_url})"

            current_balance = 0
            for token in data:
                if token.get("tokenSymbol") == "SOL":
                    current_balance = float(token.get("tokenAmount", {}).get("uiAmount", 0))

            prev_balance = old_balances.get(wallet)
            if prev_balance is not None and current_balance != prev_balance:
                msg = f"{message}
💰 Neue SOL-Balance: *{current_balance} SOL*"
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "Markdown"}
                )
            old_balances[wallet] = current_balance
        time.sleep(60)

def run_scanner():
    t = threading.Thread(target=wallet_scanner, daemon=True)
    t.start()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("add", add_wallet))
app.add_handler(CommandHandler("rm", remove_wallet))
app.add_handler(CommandHandler("list", list_wallets))

run_scanner()
app.run_polling()
