import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_wallet(address: str, tag: str):
    existing = supabase.table("wallets").select("address").eq("address", address).execute()
    if existing.data:
        return False
    supabase.table("wallets").insert({"address": address, "tag": tag, "pnl": 0.0, "wins": 0, "losses": 0}).execute()
    return True

def remove_wallet(address: str):
    supabase.table("wallets").delete().eq("address", address).execute()

def list_wallets():
    result = supabase.table("wallets").select("*").execute()
    return result.data if result.data else []

def update_pnl(address: str, amount: float):
    wallet = supabase.table("wallets").select("*").eq("address", address).execute()
    if not wallet.data:
        return False
    current_pnl = wallet.data[0]["pnl"]
    supabase.table("wallets").update({"pnl": current_pnl + amount}).eq("address", address).execute()
    return True

def add_win(address: str):
    wallet = supabase.table("wallets").select("wins").eq("address", address).execute()
    if wallet.data:
        wins = wallet.data[0]["wins"] + 1
        supabase.table("wallets").update({"wins": wins}).eq("address", address).execute()

def add_loss(address: str):
    wallet = supabase.table("wallets").select("losses").eq("address", address).execute()
    if wallet.data:
        losses = wallet.data[0]["losses"] + 1
        supabase.table("wallets").update({"losses": losses}).eq("address", address).execute()

# 🧩 Wichtig: für main.py kompatibel machen
supabase_client = supabase
