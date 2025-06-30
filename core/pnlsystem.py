import logging
from core.database import get_wallets

logger = logging.getLogger(__name__)

# Berechnet WR(x/y) + PnL(+/-) für eine Wallet anhand Supabase-Einträgen
async def calculate_wallet_wr(user_id: int, wallet: str) -> str:
    try:
        wallets = await get_wallets(user_id)
        if not wallets:
            logger.warning(f"⚠️ Keine Wallets gefunden für User {user_id}")
            return "⚪️ Keine Daten"

        target = next((w for w in wallets if w.get("wallet") == wallet), None)
        if not target:
            logger.warning(f"⚠️ Wallet {wallet} nicht gefunden für User {user_id}")
            return "⚪️ Nicht gefunden"

        try:
            wins = int(target.get("wins") or 0)
            losses = int(target.get("losses") or 0)
            pnl = float(target.get("pnl") or 0.0)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Ungültige Werte bei Wallet {wallet} – Wins, Losses oder PnL.")
            return "⚠️ Ungültige Daten"

        total = wins + losses
        wr_str = f"WR({wins}/{total})" if total > 0 else "WR(0/0)"
        pnl_str = f"PnL({pnl:+.2f} SOL)"

        if pnl > 0:
            pnl_str = f"🟢 {pnl_str}"
        elif pnl < 0:
            pnl_str = f"🔴 {pnl_str}"
        else:
            pnl_str = f"⚪️ {pnl_str}"

        return f"{wr_str} · {pnl_str}"

    except Exception as e:
        logger.exception(f"❌ Fehler bei calculate_wallet_wr für {wallet}: {e}")
        return "⚠️ Fehler bei Auswertung"
