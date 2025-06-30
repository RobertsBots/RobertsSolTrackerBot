import os
import httpx
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from core.database import get_wallets, update_last_tx_time, get_last_tx_time, get_wallet_sol_balance
from core.utils import get_token_name

DEX_BASE_URL = "https://birdeye.so/token"
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")
SOLANA_API_URL = "https://api.solscan.io/account/transactions?address={}&limit=1"
SOL_BALANCE_API = "https://api.solscan.io/account/tokens?address={}"

logger = logging.getLogger(__name__)

# Cache zuletzt gesehener Transaktionen je Wallet
latest_tx_by_wallet = {}
last_notified_inactive = {}
last_notified_dump = {}

async def check_wallet_activity(bot: Bot):
    try:
        wallets = await get_wallets(user_id=0)
        if not wallets:
            logger.info("📭 Keine Wallets zu tracken.")
            return

        for wallet in wallets:
            address = wallet.get("address")
            tag = wallet.get("tag", "Ungetaggt")
            if not address:
                continue

            # -- Abrufen letzter Transaktion
            async with httpx.AsyncClient(timeout=20) as client:
                res = await client.get(SOLANA_API_URL.format(address))
                if res.status_code != 200:
                    continue

                data = res.json()
                txs = data.get("data", [])
                if not txs:
                    continue

                latest_tx = txs[0]
                tx_sig = latest_tx.get("signature")
                if not tx_sig:
                    continue

                # Zeit für Inaktivitäts-Tracking speichern
                await update_last_tx_time(address)

                # Neue Aktivität oder nicht?
                if latest_tx_by_wallet.get(address) == tx_sig:
                    continue
                latest_tx_by_wallet[address] = tx_sig

                token_info = extract_token_info(latest_tx)
                if not token_info:
                    continue

                # Nachricht bei neuer Aktivität
                token_name, amount, price, mint = token_info
                dex_url = f"{DEX_BASE_URL}/{mint}?chain=solana"

                message = f"""
📢 <b>Neue Wallet-Aktivität entdeckt</b>

🏷️ <b>Wallet:</b> <code>{address}</code>
🔁 <b>Tag:</b> {tag}
🪙 <b>Token:</b> {token_name}
📦 <b>Menge:</b> {amount}
💰 <b>Preis:</b> {price} SOL

🔗 <a href="{dex_url}">Auf DexScreener</a>
                """

                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message.strip(), parse_mode="HTML")
                logger.info(f"📬 Neue Aktivität bei {address} gepostet.")

            # --- 🔔 Inaktivitäts-Warnung
            await handle_inactivity_reminder(bot, address, tag)

            # --- 🚨 SOL-Dump-Warnung
            await handle_sol_dump_check(bot, address, tag)

    except Exception as e:
        logger.exception(f"❌ Fehler beim Check der Wallet-Aktivität: {e}")


def extract_token_info(tx: dict):
    try:
        inner = tx.get("parsedInstruction", []) or []
        post_token = tx.get("postTokenBalances", [])
        if not inner or not post_token:
            return None

        token = post_token[0]
        mint = token.get("mint")
        amount = int(token.get("uiTokenAmount", {}).get("amount", 0)) / 10**9
        token_name = get_token_name(mint)
        price = round(float(tx.get("fee", 0)) / 1e9, 5)

        return token_name, round(amount, 3), price, mint
    except Exception as e:
        logger.warning(f"⚠️ Token Info konnte nicht extrahiert werden: {e}")
        return None

# 🔔 Erinnerung bei Inaktivität
async def handle_inactivity_reminder(bot: Bot, address: str, tag: str, days_threshold=2):
    try:
        last_tx = await get_last_tx_time(address)
        if not last_tx:
            return

        inactive_days = (datetime.utcnow() - last_tx).days
        if inactive_days < days_threshold:
            return

        if address in last_notified_inactive and (datetime.utcnow() - last_notified_inactive[address]).days < 1:
            return  # Nur alle 24h benachrichtigen

        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=f"💤 Wallet <code>{address}</code> ({tag}) ist seit {inactive_days} Tagen inaktiv.",
            parse_mode="HTML"
        )
        last_notified_inactive[address] = datetime.utcnow()
    except Exception as e:
        logger.warning(f"❗️ Inaktivitäts-Warnung fehlgeschlagen: {e}")

# 🚨 Warnung bei >80% SOL-Dump
async def handle_sol_dump_check(bot: Bot, address: str, tag: str, threshold=0.8):
    try:
        sol_before, sol_after = await get_wallet_sol_balance(address)
        if sol_before == 0:
            return

        dumped_ratio = (sol_before - sol_after) / sol_before
        if dumped_ratio < threshold:
            return

        if address in last_notified_dump and (datetime.utcnow() - last_notified_dump[address]).seconds < 86400:
            return  # Max 1x/24h warnen

        percent = round(dumped_ratio * 100, 2)
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=(
                f"🚨 <b>SOL-Dump erkannt</b>\n\n"
                f"Wallet <code>{address}</code> ({tag}) hat {percent}% seines SOL-Bestands verkauft! 💣"
            ),
            parse_mode="HTML"
        )
        last_notified_dump[address] = datetime.utcnow()
    except Exception as e:
        logger.warning(f"❗️ Fehler bei SOL-Dump-Check: {e}")
