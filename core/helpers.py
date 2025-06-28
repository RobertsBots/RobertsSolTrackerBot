# core/helpers.py

import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode

async def post_wallet_detection_message(bot: Bot, channel_id: str, wallet: dict):
    try:
        winrate = wallet.get("winrate", "N/A")
        roi = wallet.get("roi", "N/A")
        pnl = wallet.get("pnl", "N/A")
        age = wallet.get("account_age", "N/A")
        sol = wallet.get("sol_balance", "N/A")
        address = wallet.get("address", "N/A")

        message = f"""
🚨 <b>Neue smarte Wallet erkannt!</b>

<b>🏷️ Wallet:</b> <code>{address}</code>
<b>📈 Winrate:</b> {winrate}%
<b>💹 ROI:</b> {roi}%
<b>💰 PnL:</b> {pnl} SOL
<b>📅 Account Age:</b> {age} Tage
<b>🧾 Balance:</b> {sol} SOL
<b>🏷️ Tag:</b> 🚀 AutoDetected
        """

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Auf Birdeye", url=f"https://birdeye.so/address/{address}?chain=solana")]
            ]
        )

        await bot.send_message(
            chat_id=channel_id,
            text=message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"❌ Fehler beim Posten der Wallet Detection Nachricht: {e}")
