import logging
from core.database import get_wallets

logger = logging.getLogger(__name__)

# Berechnet WR(x/y) + PnL(+/-) für eine Wallet anhand Supabase-Einträgen
async def calculate_wallet_wr(user_id: int, wallet: str):
    try:
        wallets = await get_wallets(user_id)
        target = next((w for w in wallets if w.get("wallet") == wallet), None)

        if not target:
            return None

        wins = target.get("wins", 0) or 0
        losses = target.get("losses", 0) or 0
        pnl = target.get("pnl", 0.0) or 0.0

        wr_str = f"WR({wins}/{wins + losses})"
        pnl_str = f"PnL({pnl:+.2f} SOL)"

        if pnl > 0:
            pnl_str = f"🟢 {pnl_str}"
        elif pnl < 0:
            pnl_str = f"🔴 {pnl_str}"
        else:
            pnl_str = f"⚪️ {pnl_str}"

        return f"{wr_str} · {pnl_str}"

    except Exception as e:
        logger.error(f"❌ Fehler bei calculate_wallet_wr für {wallet}: {e}")
        return "⚠️ Fehler bei Auswertung"
