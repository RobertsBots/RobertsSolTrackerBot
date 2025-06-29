import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL oder SUPABASE_KEY fehlen in den Umgebungsvariablen.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Wallets
async def add_wallet(user_id: int, wallet: str, tag: str = "") -> bool:
    existing = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("*").eq("wallet", wallet).eq("user_id", user_id).execute()
    )
    if existing.data:
        return False
    await asyncio.to_thread(
        lambda: supabase.table("wallets").insert({"user_id": user_id, "wallet": wallet, "tag": tag}).execute()
    )
    return True

async def upsert_wallet(wallet: str, tag: str):
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("*").eq("wallet", wallet).execute()
    )
    if result.data:
        await asyncio.to_thread(
            lambda: supabase.table("wallets").update({"tag": tag}).eq("wallet", wallet).execute()
        )
    else:
        await asyncio.to_thread(
            lambda: supabase.table("wallets").insert({"wallet": wallet, "tag": tag}).execute()
        )

async def remove_wallet(user_id: int, wallet: str):
    await asyncio.to_thread(
        lambda: supabase.table("wallets").delete().eq("user_id", user_id).eq("wallet", wallet).execute()
    )

async def get_wallets(user_id: int):
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("*").eq("user_id", user_id).execute()
    )
    return result.data

async def get_all_wallets():
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("*").execute()
    )
    return result.data

async def update_pnl(wallet: str, amount: float):
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("pnl", "wins", "losses").eq("wallet", wallet).execute()
    )
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
    await asyncio.to_thread(
        lambda: supabase.table("wallets").update({
            "pnl": pnl,
            "wins": wins,
            "losses": losses
        }).eq("wallet", wallet).execute()
    )

async def reset_wallets():
    await asyncio.to_thread(
        lambda: supabase.table("wallets").delete().neq("wallet", "").execute()
    )

async def set_wallets(wallets):
    for entry in wallets:
        await asyncio.to_thread(
            lambda: supabase.table("wallets").insert(entry).execute()
        )

async def update_tag(wallet: str, new_tag: str):
    await asyncio.to_thread(
        lambda: supabase.table("wallets").update({"tag": new_tag}).eq("wallet", wallet).execute()
    )

# ✅ Finder-Modus
async def set_finder_mode(user_id: int, mode: str):
    existing = await asyncio.to_thread(
        lambda: supabase.table("finder_modes").select("*").eq("user_id", user_id).execute()
    )
    if existing.data:
        await asyncio.to_thread(
            lambda: supabase.table("finder_modes").update({"mode": mode}).eq("user_id", user_id).execute()
        )
    else:
        await asyncio.to_thread(
            lambda: supabase.table("finder_modes").insert({
                "user_id": user_id,
                "mode": mode,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        )

async def get_finder_mode(user_id: int) -> str:
    result = await asyncio.to_thread(
        lambda: supabase.table("finder_modes").select("mode").eq("user_id", user_id).execute()
    )
    if result.data and result.data[0].get("mode"):
        return result.data[0]["mode"]
    return "off"
