import logging
from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.database import add_wallet
from core.smartcoach import smartcoach_reply

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

        was_added = await add_wallet(user_id=0, wallet=address, tag=tag)
        if not was_added:
            logger.info(f"🔁 Wallet {address} wurde bereits hinzugefügt.")
            return

        tp = round(roi * 1.2, 1)
        sl = round(roi * 0.5, 1)

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
            )],
            [InlineKeyboardButton(
                text="🧠 SmartCoach Analyse",
                callback_data=f"smartcoach_reply:{address}:{winrate}:{roi}:{tp}:{sl}"
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


async def send_smartcoach_reply(callback_query: types.CallbackQuery):
    try:
        data = callback_query.data.split(":")
        if len(data) != 6:
            await callback_query.answer("❗️ Ungültige Anfrage.")
            return

        _, address, wr, roi, tp, sl = data
        wr = float(wr)
        roi = float(roi)
        tp = float(tp)
        sl = float(sl)

        message = smartcoach_reply(wr=wr / 100, roi=roi, tp=tp, sl=sl)

        await callback_query.answer()
        await callback_query.message.reply(f"🧠 <b>SmartCoach Analyse:</b>\n\n{message}", parse_mode="HTML")

    except Exception as e:
        logger.exception("❌ Fehler bei SmartCoach Callback:")
        await callback_query.answer("❌ Analysefehler. Bitte später erneut versuchen.")
