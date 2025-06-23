import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_wallet(wallet: str, tag: str):
    return supabase.table("wallets").insert({"wallet": wallet, "tag": tag}).execute()

def remove_wallet(wallet: str):
    return supabase.table("wallets").delete().eq("wallet", wallet).execute()

def list_wallets():
    return supabase.table("wallets").select("*").execute()

def update_wallet_profit(wallet: str, profit: float):
    return supabase.table("wallets").update({"profit": profit}).eq("wallet", wallet).execute()
