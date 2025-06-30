import os
import httpx
import logging
from aiogram import Bot
from core.database import get_wallets
from core.utils import get_token_name

DEX_BASE_URL = "https://birdeye.so/token"
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")
SOLANA_API_URL = "https://api.solscan.io/account/transactions?address={}&limit=1"

logger = logging.getLogger(__name__)

# Cache zuletzt gesehener Transaktionen je Wallet
latest_tx_by_wallet = {}

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

                # Bereits gesehen?
                if latest_tx_by_wallet.get(address) == tx_sig:
                    continue

                latest_tx_by_wallet[address] = tx_sig  # speichern
                token_info = extract_token_info(latest_tx)
                if not token_info:
                    continue

                # Formatierte Nachricht
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
