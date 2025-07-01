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

# Helfer für sync-to-async Supabase-Aufrufe
async def run_sync_query(fn):
    return await asyncio.to_thread(fn)

# WALLET-Funktionen
async def add_wallet(user_id: int, wallet: str, tag: str = "") -> bool:
    existing = await run_sync_query(lambda: supabase.table("wallets")
                                    .select("*")
                                    .eq("wallet", wallet)
                                    .eq("user_id", user_id)
                                    .execute())
    if existing.data:
        return False

    await run_sync_query(lambda: supabase.table("wallets")
                        .insert({
                            "user_id": user_id,
                            "wallet": wallet,
                            "tag": tag,
                            "created_at": datetime.utcnow().isoformat(),
                            "last_tx_time": None,
                            "initial_sol_balance": None,
                            "last_sol_balance": None
                        }).execute())
    return True

async def remove_wallet(user_id: int, wallet: str):
    await run_sync_query(lambda: supabase.table("wallets")
                        .delete()
                        .eq("user_id", user_id)
                        .eq("wallet", wallet)
                        .execute())

async def get_wallets(user_id: int):
    result = await run_sync_query(lambda: supabase.table("wallets")
                                .select("*")
                                .eq("user_id", user_id)
                                .execute())
    return result.data or []

async def get_all_wallets():
    result = await run_sync_query(lambda: supabase.table("wallets").select("*").execute())
    return result.data or []

async def update_pnl(wallet: str, amount: float):
    result = await run_sync_query(lambda: supabase.table("wallets")
                                .select("pnl", "wins", "losses")
                                .eq("wallet", wallet)
                                .execute())
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

    await run_sync_query(lambda: supabase.table("wallets")
                        .update({
                            "pnl": pnl,
                            "wins": wins,
                            "losses": losses
                        })
                        .eq("wallet", wallet)
                        .execute())

async def reset_wallets():
    await run_sync_query(lambda: supabase.table("wallets")
                        .delete()
                        .neq("wallet", "")
                        .execute())

async def set_wallets(wallets):
    for entry in wallets:
        await run_sync_query(lambda: supabase.table("wallets").insert(entry).execute())

async def update_tag(wallet: str, new_tag: str):
    await run_sync_query(lambda: supabase.table("wallets")
                        .update({"tag": new_tag})
                        .eq("wallet", wallet)
                        .execute())

# FINDER-MODUS-Funktionen
async def set_finder_mode(user_id: int, mode: str):
    existing = await run_sync_query(lambda: supabase.table("finder_modes")
                                    .select("*")
                                    .eq("user_id", user_id)
                                    .execute())
    if existing.data:
        await run_sync_query(lambda: supabase.table("finder_modes")
                            .update({"mode": mode})
                            .eq("user_id", user_id)
                            .execute())
    else:
        await run_sync_query(lambda: supabase.table("finder_modes")
                            .insert({
                                "user_id": user_id,
                                "mode": mode,
                                "created_at": datetime.utcnow().isoformat()
                            })
                            .execute())

async def get_finder_mode(user_id: int) -> str:
    result = await run_sync_query(lambda: supabase.table("finder_modes")
                                .select("mode")
                                .eq("user_id", user_id)
                                .execute())
    if result.data and result.data[0].get("mode"):
        return result.data[0]["mode"]
    return "off"

# Letzte Aktivität
async def update_last_tx_time(wallet: str):
    now = datetime.utcnow().isoformat()
    await run_sync_query(lambda: supabase.table("wallets")
                        .update({"last_tx_time": now})
                        .eq("wallet", wallet)
                        .execute())

async def get_last_tx_time(wallet: str):
    result = await run_sync_query(lambda: supabase.table("wallets")
                                .select("last_tx_time")
                                .eq("wallet", wallet)
                                .execute())
    if result.data and result.data[0].get("last_tx_time"):
        return datetime.fromisoformat(result.data[0]["last_tx_time"])
    return None

# SOL-Balance
async def get_wallet_sol_balance(wallet: str) -> tuple:
    result = await run_sync_query(lambda: supabase.table("wallets")
                                .select("initial_sol_balance", "last_sol_balance")
                                .eq("wallet", wallet)
                                .execute())
    if result.data:
        initial = result.data[0].get("initial_sol_balance") or 0.0
        current = result.data[0].get("last_sol_balance") or 0.0
        return float(initial), float(current)
    return 0.0, 0.0

async def set_wallet_sol_balance(wallet: str, balance: float, set_initial=False):
    column = "initial_sol_balance" if set_initial else "last_sol_balance"
    await run_sync_query(lambda: supabase.table("wallets")
                        .update({column: balance})
                        .eq("wallet", wallet)
                        .execute())

# Start-Message-ID speichern/abrufen
async def save_user_start_message_id(user_id: int, message_id: int):
    existing = await run_sync_query(lambda: supabase.table("start_messages")
                                    .select("*")
                                    .eq("user_id", user_id)
                                    .execute())
    if existing.data:
        await run_sync_query(lambda: supabase.table("start_messages")
                            .update({"message_id": message_id})
                            .eq("user_id", user_id)
                            .execute())
    else:
        await run_sync_query(lambda: supabase.table("start_messages")
                            .insert({
                                "user_id": user_id,
                                "message_id": message_id
                            })
                            .execute())

async def get_user_start_message_id(user_id: int) -> int:
    result = await run_sync_query(lambda: supabase.table("start_messages")
                                .select("message_id")
                                .eq("user_id", user_id)
                                .execute())
    if result.data and result.data[0].get("message_id"):
        return int(result.data[0]["message_id"])
    return 0
