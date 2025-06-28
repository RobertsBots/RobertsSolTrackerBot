# core/helpers.py

import logging
import os
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from core.database import add_wallet

async def post_wallet_detection_message(bot: Bot, channel_id: str, wallet: dict):
    try:
        address = wallet.get("address", "N/A")
        winrate = float(wallet.get("winrate", 0))
        roi = float(wallet.get("roi", 0))
        pnl = float(wallet.get("pnl", 0))
        age = int(wallet.get("account_age", 0))
        sol = float(wallet.get("sol_balance", 0))
        tag = "🚀 AutoDetected"

        # Prüfen, ob Wallet neu ist und speichern
        was_added = add_wallet(user_id=0, wallet=address, tag=tag)
        if not was_added:
            return  # bereits getrackt → keine doppelte Meldung

        # Nachricht aufbauen
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
