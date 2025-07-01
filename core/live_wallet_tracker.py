import os
import httpx
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from core.database import (
    get_wallets,
    update_last_tx_time,
    get_last_tx_time,
    get_wallet_sol_balance
)
from core.utils import get_token_name

logger = logging.getLogger(__name__)

DEX_BASE_URL = "https://birdeye.so/token"
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")
SOLANA_API_URL = "https://api.solscan.io/account/transactions?address={}&limit=1"

# Caches für Benachrichtigungen & letzte Transaktionen
latest_tx_by_wallet = {}
last_notified_inactive = {}
last_notified_dump = {}

async def check_wallet_activity(bot: Bot):
    try:
        wallets = await get_wallets(user_id=0)
        if not wallets:
            logger.info("📭 Keine Wallets zu tracken.")
            return

        async with httpx.AsyncClient(timeout=20) as client:
            for wallet in wallets:
                address = wallet.get("address")
                tag = wallet.get("tag", "Ungetaggt")
                if not address:
                    continue

                # Letzte Transaktion abrufen
                res = await client.get(SOLANA_API_URL.format(address))
                if res.status_code != 200:
                    logger.warning(f"⚠️ Solscan Fehler für {address} (Status: {res.status_code})")
                    continue

                data = res.json()
                txs = data.get("data", [])
                if not txs:
                    logger.debug(f"ℹ️ Keine Transaktionen gefunden für {address}")
                    continue

                latest_tx = txs[0]
                tx_sig = latest_tx.get("signature")
                if not tx_sig:
                    logger.debug(f"ℹ️ Keine Signatur für neueste Transaktion bei {address}")
                    continue

                # Nur neue Transaktionen verarbeiten
                if latest_tx_by_wallet.get(address) == tx_sig:
                    continue
                latest_tx_by_wallet[address] = tx_sig

                await update_last_tx_time(address)

                token_info = await extract_token_info(latest_tx)
                if not token_info:
                    logger.debug(f"ℹ️ Keine Tokeninfo für Transaktion {tx_sig} bei {address}")
                    continue

                token_name, amount, price, mint = token_info
                dex_url = f"{DEX_BASE_URL}/{mint}?chain=solana"

                message = (
                    f"📢 <b>Neue Wallet-Aktivität entdeckt</b>\n\n"
                    f"🏷️ <b>Wallet:</b> <code>{address}</code>\n"
                    f"🔁 <b>Tag:</b> {tag}\n"
                    f"🪙 <b>Token:</b> {token_name}\n"
                    f"📦 <b>Menge:</b> {amount}\n"
                    f"💰 <b>Preis:</b> {price} SOL\n\n"
                    f"🔗 <a href=\"{dex_url}\">Auf DexScreener</a>"
                )

                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode="HTML")
                logger.info(f"📬 Neue Aktivität bei {address} gepostet.")

                # Reminder-Checks
                await handle_inactivity_reminder(bot, address, tag)
                await handle_sol_dump_check(bot, address, tag)

    except Exception as e:
        logger.exception(f"❌ Fehler bei check_wallet_activity: {e}")

async def extract_token_info(tx: dict):
    try:
        post_token = tx.get("postTokenBalances", [])
        if not post_token:
            return None

        token = post_token[0]
        mint = token.get("mint")
        if not mint:
            return None

        amount_raw = token.get("uiTokenAmount", {}).get("amount", 0)
        amount = int(amount_raw) / 1e9 if amount_raw else 0

        token_name = await get_token_name(mint)
        price = round(float(tx.get("fee", 0)) / 1e9, 5)

        return token_name, round(amount, 3), price, mint
    except Exception as e:
        logger.warning(f"⚠️ Fehler bei extract_token_info: {e}")
        return None

async def handle_inactivity_reminder(bot: Bot, address: str, tag: str, days_threshold=2):
    try:
        last_tx = await get_last_tx_time(address)
        if not last_tx:
            return

        inactive_duration = datetime.utcnow() - last_tx
        if inactive_duration.days < days_threshold:
            return

        last_notify = last_notified_inactive.get(address)
        if last_notify and (datetime.utcnow() - last_notify).total_seconds() < 86400:
            return  # max 1x pro 24h

        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=f"💤 Wallet <code>{address}</code> ({tag}) ist seit {inactive_duration.days} Tagen inaktiv.",
            parse_mode="HTML"
        )
        last_notified_inactive[address] = datetime.utcnow()
    except Exception as e:
        logger.warning(f"❗️ Fehler bei Inaktivitäts-Warnung: {e}")

async def handle_sol_dump_check(bot: Bot, address: str, tag: str, threshold=0.8):
    try:
        sol_before, sol_after = await get_wallet_sol_balance(address)
        if sol_before == 0:
            return

        dumped_ratio = (sol_before - sol_after) / sol_before
        if dumped_ratio < threshold:
            return

        last_notify = last_notified_dump.get(address)
        if last_notify and (datetime.utcnow() - last_notify).total_seconds() < 86400:
            return  # max 1x pro 24h

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
