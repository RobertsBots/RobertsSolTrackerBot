import json
import os

WALLETS_FILE = "data/wallets.json"
FINDER_STATUS_FILE = "data/finder_status.json"

def ensure_file_exists(path, default):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(default, f)

def load_json(path, default):
    ensure_file_exists(path, default)
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def add_wallet_to_tracking(wallet, tag="💼 Manual"):
    data = load_json(WALLETS_FILE, {})
    if wallet not in data:
        data[wallet] = {"tag": tag, "pnl": 0, "wins": 0, "losses": 0}
        save_json(WALLETS_FILE, data)
        return True
    return False

def remove_wallet_from_tracking(wallet):
    data = load_json(WALLETS_FILE, {})
    if wallet in data:
        del data[wallet]
        save_json(WALLETS_FILE, data)
        return True
    return False

def get_tracked_wallets_with_stats():
    return load_json(WALLETS_FILE, {})

def set_manual_profit(wallet, profit):
    data = load_json(WALLETS_FILE, {})
    if wallet in data:
        data[wallet]["pnl"] += profit
        save_json(WALLETS_FILE, data)
        return True
    return False

def increment_win(wallet):
    data = load_json(WALLETS_FILE, {})
    if wallet in data:
        data[wallet]["wins"] += 1
        save_json(WALLETS_FILE, data)

def increment_loss(wallet):
    data = load_json(WALLETS_FILE, {})
    if wallet in data:
        data[wallet]["losses"] += 1
        save_json(WALLETS_FILE, data)

def get_finder_status():
    return load_json(FINDER_STATUS_FILE, {"enabled": False, "mode": None})

def toggle_smart_finder(enabled, mode=None):
    status = {"enabled": enabled, "mode": mode}
    save_json(FINDER_STATUS_FILE, status)
