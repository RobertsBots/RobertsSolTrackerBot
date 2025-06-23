from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Funktionen zum Zugriff auf die Wallet-Tabelle ===

async def add_wallet_entry(wallet: str, tag: str):
    supabase_client.table("wallets").insert({"wallet": wallet, "tag": tag}).execute()

async def remove_wallet_entry(wallet: str):
    supabase_client.table("wallets").delete().eq("wallet", wallet).execute()

async def list_wallet_entries():
    result = supabase_client.table("wallets").select("*").execute()
    return result.data or []

# === Funktionen für PnL und Winrate ===

async def update_wallet_profit(wallet: str, profit: float):
    supabase_client.table("wallets").update({"manual_profit": profit}).eq("wallet", wallet).execute()

async def get_wallet_by_address(wallet: str):
    result = supabase_client.table("wallets").select("*").eq("wallet", wallet).execute()
    if result.data:
        return result.data[0]
    return None
