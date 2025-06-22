import json
import os

WALLETS_FILE = "wallets.json"

def load_wallets():
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_wallets(wallets):
    with open(WALLETS_FILE, "w") as f:
        json.dump(wallets, f)

def format_wallet_list(wallets):
    if not wallets:
        return "Keine Wallets eingetragen."
    return "\n".join([f"{w} – {t}" for w, t in wallets.items()])