import os
from datetime import datetime
import httpx
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.database import add_wallet

logger = logging.getLogger(__name__)

def shorten_address(address: str) -> str:
    return f"{address[:4]}...{address[-4:]}"

def format_sol(value: float) -> str:
    return f"{value:.2f} ◎"

def format_pnl(value: float) -> str:
    emoji = "🟢" if value >= 0 else "🔴"
    return f"{emoji} {value:+.2f}◎"

def generate_dexscreener_link(token_address: str) -> str:
    return f"https://dexscreener.com/solana/{token_address}"

def get_timestamp() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

async def fetch_wallet_data(wallet: str) -> dict:
    url = f"https://api.solscan.io/account/tokens?account={wallet}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception:
            return {}

def parse_wallet_trade(data: dict) -> str:
    try:
        token = data.get("tokenSymbol", "UNKNOWN")
        amount = float(data.get("tokenAmount", {}).get("uiAmount", 0))
        return f"{token} ({amount:.2f})"
    except Exception:
        return "ParseError"

def colorize_winrate(wins: int, losses: int) -> str:
    total = wins + losses
    if total == 0:
        return "WR(0/0)"
    winrate = int((wins / total) * 100)
    emoji = "🟢" if winrate >= 60 else "🔴"
    return f"{emoji} WR({wins}/{total})"

def calculate_winrate(wins: int, losses: int) -> float:
    total = wins + losses
    return round((wins / total) * 100, 2) if total > 0 else 0.0

def get_webhook_url() -> str:
    base_url = (
        os.getenv("WEBHOOK_URL") or
        os.getenv("RENDER_EXTERNAL_URL") or
        os.getenv("RAILWAY_STATIC_URL")
    )
    if not base_url:
        raise ValueError("❌ WEBHOOK_URL, RENDER_EXTERNAL_URL oder RAILWAY_STATIC_URL ist nicht gesetzt.")
    
    return base_url.rstrip("/") + "/webhook"  # ✅ Webhook-Pfad anhängen

async def post_wallet_detection_message(bot: Bot, channel_id: str, wallet: dict):
    try:
        address = wallet.get("address", "N/A")
        winrate = float(wallet.get("winrate", 0))
        roi = float(wallet.get("roi", 0))
        pnl = float(wallet.get("pnl", 0))
        age = int(wallet.get("account_age", 0))
        sol = float(wallet.get("sol_balance", 0))
        tag = "🚀 AutoDetected"

        was_added = add_wallet(user_id=0, wallet=address, tag=tag)
        if not was_added:
            return

        message = f"""
🚨 <b>Neue smarte Wallet erkannt!</b>

<b>🏷️ Wallet:</b> <code>{address}</code>
<b>📈 Winrate:</b> {winrate:.1f}%
<b>💹 ROI:</b> {roi:.2f}%
<b>💰 PnL:</b> {pnl:.2f} SOL
<b>📅 Account Age:</b> {age} Tage
<b>🧾 Balance:</b> {sol:.2f} SOL
<b>🏷️ Tag:</b> {tag}
        """

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📊 Auf Birdeye",
                url=f"https://birdeye.so/address/{address}?chain=solana"
            )]
        ])

        await bot.send_message(
            chat_id=channel_id,
            text=message.strip(),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"📬 Wallet-Detection gesendet für {address}")
    except Exception as e:
        logger.error(f"❌ Fehler beim Posten der Wallet Detection Nachricht: {e}")
