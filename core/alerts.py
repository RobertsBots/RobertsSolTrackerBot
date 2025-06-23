from telegram import Bot
import os
from core.database import supabase_client

CHANNEL_ID = os.getenv("CHANNEL_ID")

def format_trade_alert(wallet_address: str, token_symbol: str, tx_type: str, amount: float):
    emoji = "🟢" if tx_type == "BUY" else "🔴"
    action = "Kauf" if tx_type == "BUY" else "Verkauf"
    link = f"https://dexscreener.com/solana/{token_symbol.lower()}"
    return (
        f"{emoji} <b>{action} erkannt</b>\n"
        f"<b>Wallet:</b> <code>{wallet_address}</code>\n"
        f"<b>Token:</b> <code>{token_symbol}</code>\n"
        f"<b>Betrag:</b> {amount:.2f} SOL\n"
        f"<a href='{link}'>🔍 Zum Chart</a>"
    )

async def send_trade_alert(bot: Bot, wallet_address: str, token_symbol: str, tx_type: str, amount: float):
    text = format_trade_alert(wallet_address, token_symbol, tx_type, amount)
    await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
