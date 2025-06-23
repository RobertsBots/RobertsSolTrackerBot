from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode

def send_message_with_buttons(text, buttons=None):
    reply_markup = None
    if buttons:
        reply_markup = InlineKeyboardMarkup(buttons)
    return {"text": text, "reply_markup": reply_markup, "parse_mode": ParseMode.MARKDOWN}

def format_wallet_info(wallet, tag, balance, pnl, winrate):
    pnl_str = f"*PnL:* `{pnl}`"
    wr_str = f"*WR:* `{winrate}`"
    return f"📟 *{wallet}* (`{tag}`)\n💰 *Balance:* `{balance} SOL`\n{wr_str} | {pnl_str}"

def dex_link(token_address):
    return f"[🔗 DexScreener](https://dexscreener.com/solana/{token_address})"

def format_profit(pnl_value: float) -> str:
    color = "🟢" if pnl_value > 0 else "🔴" if pnl_value < 0 else "⚪️"
    return f"{color} {abs(pnl_value)} sol"
