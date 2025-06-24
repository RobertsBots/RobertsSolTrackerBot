# core/smartfinder/finder.py

import os
import logging
import aiohttp
import asyncio
from telegram import ParseMode
from core.database import supabase_client

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
DUNE_API_KEY = os.getenv("DUNE_API_KEY")

job_reference = {"task": None}
mode_reference = {"mode": "moonbags"}  # oder 'scalping'

async def fetch_smart_wallets():
    headers = {
        "X-Dune-API-Key": DUNE_API_KEY,
        "Content-Type": "application/json"
    }
    url = "https://api.dune.com/api/v1/query/4632804/results"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data["result"]["rows"]
            else:
                logging.error(f"Dune API Fehler: {response.status}")
                return []

def meets_criteria(wallet, mode):
    try:
        wr = float(wallet.get("winrate", 0))
        roi = float(wallet.get("roi", 0))
        return wr >= 70 and roi >= 5
    except Exception as e:
        logging.error(f"Kriterienprüfung fehlgeschlagen: {e}")
        return False

async def post_wallet(bot, wallet):
    address = wallet.get("wallet")
    tag = "🚀 AutoDetected"
    wr = wallet.get("winrate")
    roi = wallet.get("roi")
    pnl = wallet.get("pnl")
    age = wallet.get("wallet_age_days")
    sol = wallet.get("sol_balance")

    birdeye = f"https://birdeye.so/address/{address}?chain=solana"
    message = f"""
<b>📡 Neue Smart Wallet erkannt</b>
<b>Wallet:</b> <code>{address}</code>
<b>Tag:</b> {tag}
<b>WR:</b> {wr:.1f}% | <b>ROI:</b> {roi:.1f}% | <b>PnL:</b> {pnl:+.2f} SOL
<b>Alter:</b> {age} Tage | <b>Balance:</b> {sol:.2f} SOL
🔗 <a href="{birdeye}">Birdeye Link</a>
"""
    # Prüfe ob bereits vorhanden
    exists = supabase_client.table("wallets").select("*").eq("address", address).execute()
    if not exists.data:
        supabase_client.table("wallets").insert({
            "address": address,
            "tag": tag,
            "pnl": 0,
            "wins": 0,
            "losses": 0
        }).execute()
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def smartfinder_loop(bot):
    while True:
        try:
            wallets = await fetch_smart_wallets()
            if wallets:
                for wallet in wallets:
                    if meets_criteria(wallet, mode_reference["mode"]):
                        await post_wallet(bot, wallet)
        except Exception as e:
            logging.error(f"Smartfinder Fehler: {e}")
        await asyncio.sleep(1800)  # alle 30 Minuten
        

def start_smartfinder_job(app):
    if job_reference["task"] is None:
        job_reference["task"] = asyncio.create_task(smartfinder_loop(app.bot))

def stop_smartfinder_job():
    if job_reference["task"]:
        job_reference["task"].cancel()
        job_reference["task"] = None

def set_finder_mode(mode: str):
    if mode in ["moonbags", "scalping"]:
        mode_reference["mode"] = mode
