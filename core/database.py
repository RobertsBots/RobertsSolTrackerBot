import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_wallet(user_id: int, wallet: str, tag: str = ""):
    existing = supabase.table("wallets").select("*").eq("wallet", wallet).eq("user_id", user_id).execute()
    if existing.data:
        return False
    supabase.table("wallets").insert({"user_id": user_id, "wallet": wallet, "tag": tag}).execute()
    return True

def upsert_wallet(wallet: str, tag: str):
    result = supabase.table("wallets").select("*").eq("wallet", wallet).execute()
    if result.data:
        supabase.table("wallets").update({"tag": tag}).eq("wallet", wallet).execute()
    else:
        supabase.table("wallets").insert({"wallet": wallet, "tag": tag}).execute()

def remove_wallet(user_id: int, wallet: str):
    supabase.table("wallets").delete().eq("user_id", user_id).eq("wallet", wallet).execute()

def get_wallets(user_id: int):
    result = supabase.table("wallets").select("*").eq("user_id", user_id).execute()
    return result.data

def get_all_wallets():
    result = supabase.table("wallets").select("*").execute()
    return result.data

def update_pnl(wallet: str, amount: float):
    result = supabase.table("wallets").select("pnl", "wins", "losses").eq("wallet", wallet).execute()
    if not result.data:
        return
    current = result.data[0]
    pnl = current.get("pnl", 0) + amount
    wins = current.get("wins", 0)
    losses = current.get("losses", 0)
    if amount > 0:
        wins += 1
    else:
        losses += 1
    supabase.table("wallets").update({"pnl": pnl, "wins": wins, "losses": losses}).eq("wallet", wallet).execute()

def reset_wallets():
    supabase.table("wallets").delete().neq("wallet", "").execute()

def set_wallets(wallets):
    for entry in wallets:
        supabase.table("wallets").insert(entry).execute()

def update_tag(wallet: str, new_tag: str):
    supabase.table("wallets").update({"tag": new_tag}).eq("wallet", wallet).execute()

# 🔥 Fehlende Funktionen für Finder-Modus
def set_finder_mode(user_id: int, mode: str):
    result = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if result.data:
        supabase.table("users").update({"finder_mode": mode}).eq("user_id", user_id).execute()
    else:
        supabase.table("users").insert({"user_id": user_id, "finder_mode": mode}).execute()

def get_finder_mode(user_id: int) -> str:
    result = supabase.table("users").select("finder_mode").eq("user_id", user_id).execute()
    if result.data and result.data[0].get("finder_mode"):
        return result.data[0]["finder_mode"]
    return "off"
