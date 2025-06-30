import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.database import add_wallet

logger = logging.getLogger(__name__)

async def post_wallet_detection_message(bot: Bot, channel_id: str, wallet: dict):
    try:
        address = wallet.get("address", "N/A")
        if not address or len(address) < 8:
            logger.warning("⚠️ Ungültige oder leere Wallet-Adresse erhalten.")
            return

        winrate = float(wallet.get("winrate") or 0)
        roi = float(wallet.get("roi") or 0)
        pnl = float(wallet.get("pnl") or 0)
        age = int(wallet.get("account_age") or 0)
        sol = float(wallet.get("sol_balance") or 0)
        tag = "🚀 AutoDetected"

        # Prüfen, ob Wallet neu ist
        was_added = await add_wallet(user_id=0, wallet=address, tag=tag)
        if not was_added:
            logger.info(f"🔁 Wallet {address} wurde bereits hinzugefügt.")
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
