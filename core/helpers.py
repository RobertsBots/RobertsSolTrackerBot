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

        try:
            winrate = float(wallet.get("winrate", 0))
        except (ValueError, TypeError):
            winrate = 0.0

        try:
            roi = float(wallet.get("roi", 0))
        except (ValueError, TypeError):
            roi = 0.0

        try:
            pnl = float(wallet.get("pnl", 0))
        except (ValueError, TypeError):
            pnl = 0.0

        try:
            age = int(wallet.get("account_age", 0))
        except (ValueError, TypeError):
            age = 0

        try:
            sol = float(wallet.get("sol_balance", 0))
        except (ValueError, TypeError):
            sol = 0.0

        tag = "🚀 AutoDetected"
        tp = round(roi * 1.2, 1)
        sl = round(roi * 0.5, 1)

        was_added = await add_wallet(user_id=0, wallet=address, tag=tag)
        if not was_added:
            logger.info(f"🔁 Wallet {address} wurde bereits hinzugefügt.")
            return

        message = f"""
🚨 <b>Neue smarte Wallet erkannt!</b>

<b>🏷️ Wallet:</b> <code>{address}</code>
<b>📈 Winrate:</b> {winrate:.1f}%
<b>💹 ROI:</b> {roi:.2f}%
<b>💰 PnL:</b> {pnl:.2f} SOL
<b>📅 Account Age:</b> {age} Tage
<b>🧾 Balance:</b> {sol:.2f} SOL
<b>🏷️ Tag:</b> {tag}
        """.strip()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Auf Birdeye",
                    url=f"https://birdeye.so/address/{address}?chain=solana"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧠 SmartCoach Analyse",
                    callback_data=f"smartcoach_reply:{address}:{winrate}:{roi}:{tp}:{sl}"
                )
            ]
        ])

        await bot.send_message(
            chat_id=channel_id,
            text=message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"📬 Wallet-Detection gesendet für {address}")

    except Exception as e:
        logger.exception(f"❌ Fehler beim Posten der Wallet Detection Nachricht: {e}")


async def send_smartcoach_reply(callback_query: types.CallbackQuery):
    try:
        data = callback_query.data.split(":")
        if len(data) != 6:
            await callback_query.answer("❗️ Ungültige Anfrage.", show_alert=True)
            return

        _, address, wr_str, roi_str, tp_str, sl_str = data

        try:
            wr = float(wr_str)
            roi = float(roi_str)
            tp = float(tp_str)
            sl = float(sl_str)
        except ValueError:
            await callback_query.answer("❗️ Ungültige Analysewerte.", show_alert=True)
            return

        message = smartcoach_reply(wr=wr / 100, roi=roi, tp=tp, sl=sl)

        await callback_query.answer()
        await callback_query.message.reply(
            f"🧠 <b>SmartCoach Analyse:</b>\n\n{message}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.exception("❌ Fehler bei SmartCoach Callback:")
        await callback_query.answer("❌ Analysefehler. Bitte später erneut versuchen.", show_alert=True)
