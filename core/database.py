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

# ✅ WALLET FUNKTIONEN
async def add_wallet(user_id: int, wallet: str, tag: str = "") -> bool:
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("*").eq("wallet", wallet).eq("user_id", user_id).execute()
    )
    if result.data:
        return False
    await asyncio.to_thread(
        lambda: supabase.table("wallets").insert({
            "user_id": user_id,
            "wallet": wallet,
            "tag": tag,
            "created_at": datetime.utcnow().isoformat(),
            "last_tx_time": None,
            "initial_sol_balance": None
        }).execute()
    )
    return True

async def remove_wallet(user_id: int, wallet: str):
    await asyncio.to_thread(
        lambda: supabase.table("wallets").delete().eq("user_id", user_id).eq("wallet", wallet).execute()
    )

async def get_wallets(user_id: int):
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("*").eq("user_id", user_id).execute()
    )
    return result.data or []

async def get_all_wallets():
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("*").execute()
    )
    return result.data or []

async def update_pnl(wallet: str, amount: float):
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("pnl", "wins", "losses").eq("wallet", wallet).execute()
    )
    if not result.data:
        return
    current = result.data[0]
    pnl = (current.get("pnl") or 0.0) + amount
    wins = (current.get("wins") or 0)
    losses = (current.get("losses") or 0)
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

# ✅ FINDER-MODUS FUNKTIONEN
async def set_finder_mode(user_id: int, mode: str):
    result = await asyncio.to_thread(
        lambda: supabase.table("finder_modes").select("*").eq("user_id", user_id).execute()
    )
    if result.data:
        await asyncio.to_thread(
            lambda: supabase.table("finder_modes").update({
                "mode": mode
            }).eq("user_id", user_id).execute()
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

# ✅ NEU: Letzte Aktivität speichern
async def update_last_tx_time(wallet: str):
    now = datetime.utcnow().isoformat()
    await asyncio.to_thread(
        lambda: supabase.table("wallets").update({"last_tx_time": now}).eq("wallet", wallet).execute()
    )

# ✅ NEU: Letzte Aktivität holen
async def get_last_tx_time(wallet: str):
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("last_tx_time").eq("wallet", wallet).execute()
    )
    if result.data and result.data[0].get("last_tx_time"):
        return datetime.fromisoformat(result.data[0]["last_tx_time"])
    return None

# ✅ NEU: Aktuelle & initiale SOL-Balance abrufen
async def get_wallet_sol_balance(wallet: str) -> tuple:
    result = await asyncio.to_thread(
        lambda: supabase.table("wallets").select("initial_sol_balance", "last_sol_balance").eq("wallet", wallet).execute()
    )
    if result.data:
        initial = result.data[0].get("initial_sol_balance") or 0.0
        current = result.data[0].get("last_sol_balance") or 0.0
        return float(initial), float(current)
    return 0.0, 0.0

# ✅ NEU: Initiale oder aktuelle Balance setzen
async def set_wallet_sol_balance(wallet: str, balance: float, set_initial=False):
    column = "initial_sol_balance" if set_initial else "last_sol_balance"
    await asyncio.to_thread(
        lambda: supabase.table("wallets").update({column: balance}).eq("wallet", wallet).execute()
    )
