import logging
from aiogram import types, Dispatcher, Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.database import get_wallets
from core.utils import format_pnl
from core.pnlsystem import calculate_wallet_wr

logger = logging.getLogger(__name__)

async def list_wallets_cmd(message: types.Message):
    Bot.set_current(message.bot)
    user_id = message.from_user.id if message.from_user else None

    if not user_id:
        await message.answer("❗️ Benutzer-ID konnte nicht ermittelt werden.")
        return

    wallets = await get_wallets(user_id=user_id)

    if not wallets:
        await message.answer(
            "💤 Du hast aktuell keine Wallets zum Anzeigen.\n\n"
            "Nutze <code>/add &lt;wallet&gt; &lt;tag&gt;</code>, um eine neue Wallet zu tracken.",
            parse_mode="HTML"
        )
        return

    await message.answer("📄 <b>Deine getrackten Wallets:</b>", parse_mode="HTML")

    for wallet in wallets:
        try:
            address = wallet.get("address") or wallet.get("wallet") or "Unbekannt"
            tag = wallet.get("tag", "-")
            profit = wallet.get("profit", 0)
            wr_string = await calculate_wallet_wr(user_id, address)
            pnl_text = format_pnl(profit)

            text = (
                f"<code>{address}</code>\n"
                f"🏷️ <b>Tag:</b> <code>{tag}</code>\n"
                f"📊 <b>{wr_string}</b> | {pnl_text}"
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🧠 SmartCoach Analyse",
                    callback_data=f"smartcoach_reply:{address}"
                )]
            ])

            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

        except Exception as e:
            logger.warning(f"❗️ Fehler beim Rendern einer Wallet-Zeile: {e}")
            continue

def register_list_cmd(dp: Dispatcher):
    dp.register_message_handler(list_wallets_cmd, commands=["list"])
