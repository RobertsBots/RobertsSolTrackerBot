import os
import logging
from datetime import datetime
import httpx
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.database import add_wallet

logger = logging.getLogger(__name__)

def shorten_address(address: str) -> str:
    if address and len(address) > 8:
        return f"{address[:4]}...{address[-4:]}"
    return "N/A"

def format_sol(value: float) -> str:
    try:
        return f"{value:.2f} ◎"
    except Exception:
        return "0.00 ◎"

def format_pnl(value: float) -> str:
    try:
        if value is None:
            return "⚪️ PnL(n/a)"
        emoji = "🟢" if value >= 0 else "🔴"
        return f"{emoji} PnL({value:+.2f} $)"
    except Exception:
        return "⚪️ PnL(n/a)"

def generate_dexscreener_link(token_address: str) -> str:
    # Fallback für leere Eingaben
    if not token_address:
        return "https://dexscreener.com/"
    return f"https://dexscreener.com/solana/{token_address}"

def get_timestamp() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

def colorize_winrate(wins: int, losses: int) -> str:
    try:
        total = wins + losses
        if total == 0:
            return "WR(0/0)"
        winrate = int((wins / total) * 100)
        emoji = "🟢" if winrate >= 60 else "🔴"
        return f"{emoji} WR({wins}/{total})"
    except Exception as e:
        logger.error(f"❌ Fehler bei colorize_winrate: {e}")
        return "WR(0/0)"

def calculate_winrate(wins: int, losses: int) -> float:
    try:
        total = wins + losses
        return round((wins / total) * 100, 2) if total > 0 else 0.0
    except Exception as e:
        logger.error(f"❌ Fehler bei calculate_winrate: {e}")
        return 0.0

def get_webhook_url() -> str:
    base_url = (
        os.getenv("WEBHOOK_URL") or
        os.getenv("RENDER_EXTERNAL_URL") or
        os.getenv("RAILWAY_STATIC_URL")
    )
    if not base_url:
        raise ValueError("❌ WEBHOOK_URL, RENDER_EXTERNAL_URL oder RAILWAY_STATIC_URL ist nicht gesetzt.")
    return base_url.rstrip("/") + "/webhook"

async def get_token_name(mint: str) -> str:
    try:
        url = f"https://public-api.birdeye.so/public/token/{mint}"
        headers = {"x-chain": "solana"}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Absicherung falls Antwort nicht wie erwartet
            return data.get("data", {}).get("name") or (mint[:4] + "...")
    except Exception as e:
        logger.warning(f"⚠️ Fehler beim Auflösen des Token-Namens für {mint}: {e}")
        return mint[:4] + "..."

def parse_wallet_trade(data: dict) -> str:
    try:
        token = data.get("tokenSymbol", "UNKNOWN")
        amount = float(data.get("tokenAmount", {}).get("uiAmount", 0))
        return f"{token} ({amount:.2f})"
    except Exception as e:
        logger.error(f"❌ Fehler bei parse_wallet_trade: {e}")
        return "ParseError"

async def post_wallet_detection_message(bot: Bot, channel_id: str, wallet: dict):
    try:
        address = wallet.get("address", "N/A")
        if not address or len(address) < 8:
            logger.warning("⚠️ Ungültige Wallet-Adresse erhalten.")
            return

        winrate = float(wallet.get("winrate", 0) or 0)
        roi = float(wallet.get("roi", 0) or 0)
        pnl = float(wallet.get("pnl", 0) or 0)
        age = int(wallet.get("account_age", 0) or 0)
        sol = float(wallet.get("sol_balance", 0) or 0)
        tag = "🚀 AutoDetected"

        was_added = await add_wallet(user_id=0, wallet=address, tag=tag)
        if not was_added:
            logger.info(f"ℹ️ Wallet bereits vorhanden: {address}")
            return

        message = (
            f"🚨 <b>Neue smarte Wallet erkannt!</b>\n\n"
            f"<b>🏷️ Wallet:</b> <code>{address}</code>\n"
            f"<b>📈 Winrate:</b> {winrate:.1f}%\n"
            f"<b>💹 ROI:</b> {roi:.2f}%\n"
            f"<b>💰 PnL:</b> {pnl:.2f} SOL\n"
            f"<b>📅 Account Age:</b> {age} Tage\n"
            f"<b>🧾 Balance:</b> {sol:.2f} SOL\n"
            f"<b>🏷️ Tag:</b> {tag}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📊 Auf Birdeye",
                url=f"https://birdeye.so/address/{address}?chain=solana"
            )]
        ])

        await bot.send_message(
            chat_id=channel_id,
            text=message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"📬 Wallet-Detection gesendet für {address}")

    except Exception as e:
        logger.error(f"❌ Fehler beim Posten der Wallet Detection Nachricht: {e}")
