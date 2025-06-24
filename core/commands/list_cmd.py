from aiogram.types import Message
from core.database import list_wallets

def format_wallet_data(wallet):
    address = wallet["address"]
    tag = wallet.get("tag", "📄")
    pnl = wallet.get("pnl", 0.0)
    wins = wallet.get("wins", 0)
    losses = wallet.get("losses", 0)
    total = wins + losses
    wr = f"{int(wins / total * 100)}%" if total > 0 else "N/A"
    dex_link = f"https://dexscreener.com/solana/{address}"

    pnl_str = f"<b>PnL:</b> {'🟢' if pnl >= 0 else '🔴'} {pnl:.2f} SOL"
    wr_str = f"<b>WR:</b> {wins}/{total} ({wr})"

    return f"""
<b>{tag}</b> – <code>{address}</code>
{pnl_str}
{wr_str}
<a href="{dex_link}">📊 Dexscreener</a>
"""

async def list_cmd(message: Message):
    wallets = list_wallets()
    if not wallets:
        await message.reply("📭 Noch keine Wallets getrackt.")
        return

    chunks = [wallets[i:i+5] for i in range(0, len(wallets), 5)]
    for chunk in chunks:
        msg = "\n".join(format_wallet_data(w) for w in chunk)
        await message.reply(msg)
