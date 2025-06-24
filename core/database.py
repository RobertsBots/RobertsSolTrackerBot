from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Kein proxy-Parameter, weil du supabase==2.1.1 nutzt
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_wallet(wallet: str, tag: str):
    return supabase.table("wallets").insert({"wallet": wallet, "tag": tag}).execute()


def remove_wallet(wallet: str):
    return supabase.table("wallets").delete().eq("wallet", wallet).execute()


def list_wallets():
    response = supabase.table("wallets").select("*").execute()
    return response.data if response.data else []


def set_profit(wallet: str, profit: float):
    return supabase.table("wallets").update({"profit": profit}).eq("wallet", wallet).execute()


def get_profit(wallet: str):
    result = supabase.table("wallets").select("profit").eq("wallet", wallet).execute()
    return result.data[0]['profit'] if result.data else 0.0


def get_wallet_tags():
    result = supabase.table("wallets").select("wallet", "tag").execute()
    return {item["wallet"]: item["tag"] for item in result.data} if result.data else {}


def upsert_wallet(wallet: str, tag: str):
    existing = supabase.table("wallets").select("wallet").eq("wallet", wallet).execute()
    if existing.data:
        return supabase.table("wallets").update({"tag": tag}).eq("wallet", wallet).execute()
    else:
        return insert_wallet(wallet, tag)
