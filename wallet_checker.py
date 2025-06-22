import os
import json
import requests
from telegram import Bot

WALLETS_FILE = "wallets.json"
BOT = Bot(token=os.getenv("BOT_TOKEN"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

def load_wallets():
    if not os.path.exists(WALLETS_FILE):
        return {}
    with open(WALLETS_FILE, "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open(WALLETS_FILE, "w") as f:
        json.dump(wallets, f)

async def add_wallet(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Nutzung: /add <WALLET> <TAG>")
        return
    wallet, tag = context.args[0], " ".join(context.args[1:])
    wallets = load_wallets()
    wallets[wallet] = tag
    save_wallets(wallets)
    await update.message.reply_text(f"✅ Wallet {wallet} mit Tag '{tag}' hinzugefügt.")

async def remove_wallet(update, context):
    if not context.args:
        await update.message.reply_text("⚠️ Nutzung: /rm <WALLET>")
        return
    wallet = context.args[0]
    wallets = load_wallets()
    if wallet in wallets:
        del wallets[wallet]
        save_wallets(wallets)
        await update.message.reply_text(f"🗑️ Wallet {wallet} entfernt.")
    else:
        await update.message.reply_text("❌ Wallet nicht gefunden.")

async def list_wallets(update, context):
    wallets = load_wallets()
    if not wallets:
        await update.message.reply_text("📭 Keine Wallets werden überwacht.")
        return
    msg = "\n".join([f"{tag}: {wallet}" for wallet, tag in wallets.items()])
    await update.message.reply_text(f"📋 Überwachte Wallets:\n{msg}")

def check_wallets():
    wallets = load_wallets()
    for wallet, tag in wallets.items():
        url = f"https://public-api.solscan.io/account/tokens?account={wallet}"
        headers = {"accept": "application/json"}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    for token in data:
                        amount = token.get("tokenAmount", {}).get("uiAmount", 0)
                        if amount > 0:
                            token_name = token.get("tokenSymbol", "Unknown")
                            link = f"https://dexscreener.com/solana/{token.get('tokenAddress')}"
                            msg = f"💸 Neue Aktivität in {tag} ({wallet})\nToken: {token_name}\nMenge: {amount}\n📈 {link}"
                            BOT.send_message(chat_id=CHANNEL_ID, text=msg)
        except Exception as e:
            print(f"Fehler beim Check der Wallet {wallet}: {e}")