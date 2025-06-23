
from postgrest import PostgrestClient
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

client = PostgrestClient(f"{SUPABASE_URL}/rest/v1/")
client.auth(token=SUPABASE_KEY)

def insert_wallet(address: str, tag: str):
    return client.from_("wallets").insert({"address": address, "tag": tag}).execute()

def get_wallets():
    return client.from_("wallets").select("*").execute().data
