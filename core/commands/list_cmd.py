import logging
from aiogram import types, Dispatcher, Bot
from core.database import get_wallets
from core.utils import format_pnl
from core.pnlsystem import calculate_wallet_wr

logger = logging.getLogger(__name__)

# Handler-Funktion für /list
async def list_wallets_cmd(message: types.Message):
    try:
        Bot.set_current(message.bot)
        user_id = message.from_user.id
        wallets = await get_wallets(user_id=user_id)

        if not wallets:
            await message.answer("📭 Du hast noch keine Wallets hinzugefügt.")
            return

        response = "📄 <b>Deine getrackten Wallets:</b>\n\n"

        for wallet in wallets:
            try:
                address = wallet.get("address", "Unbekannt")
                tag = wallet.get("tag", "-")
                profit = wallet.get("profit", 0)
                wr = calculate_wallet_wr(wallet)
                pnl_text = format_pnl(profit)

                response += (
                    f"<code>{address}</code>\n"
                    f"🏷 Tag: <b>{tag}</b>\n"
                    f"📈 {wr} | {pnl_text}\n\n"
                )
            except Exception as e:
                logger.warning(f"❗️ Fehler beim Rendern einer Wallet-Zeile: {e}")
                continue

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.exception("❌ Fehler bei /list")
        await message.answer("⚠️ Ein Fehler ist aufgetreten beim Anzeigen deiner Wallets.")

# ✅ Dispatcher-Registrierung
def register_list_cmd(dp: Dispatcher):
    dp.register_message_handler(list_wallets_cmd, commands=["list"])
