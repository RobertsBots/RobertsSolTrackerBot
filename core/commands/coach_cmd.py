import logging
from aiogram import types, Dispatcher, Bot
from core.pnlsystem import calculate_wallet_wr
from core.database import get_wallets
from core.smartcoach import smartcoach_reply

logger = logging.getLogger(__name__)

async def coach_cmd(message: types.Message):
    Bot.set_current(message.bot)
    user_id = message.from_user.id if message.from_user else None
    args = message.get_args()

    if not user_id:
        await message.reply("❗️ Benutzer-ID konnte nicht ermittelt werden.")
        return

    if not args:
        await message.reply(
            "❓ Nutze den Befehl so: <code>/coach WALLET</code>\n\n"
            "Beispiel: <code>/coach 7g3n...ABcd</code>",
            parse_mode="HTML"
        )
        return

    wallet_id = args.strip()

    try:
        wallets = await get_wallets(user_id)
        target = next((w for w in wallets if w.get("address") == wallet_id), None)

        if not target:
            await message.reply(
                "⚠️ Diese Wallet ist nicht in deiner Trackliste.",
                parse_mode="HTML"
            )
            return

        wins = int(target.get("wins", 0) or 0)
        losses = int(target.get("losses", 0) or 0)
        total = wins + losses
        wr_raw = (wins / total) if total > 0 else 0.0
        roi = float(target.get("roi") or 0.0)
        tp = None
        sl = None

        coach_response = smartcoach_reply(wr_raw, roi=roi, tp=tp, sl=sl)

        await message.answer(
            f"🧠 <b>SmartCoach Analyse</b> für <code>{wallet_id}</code>:\n\n{coach_response}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.exception(f"❌ Fehler bei /coach: {e}")
        await message.reply("⚠️ Fehler bei der Coach-Analyse.", parse_mode="HTML")


def register_coach_cmd(dp: Dispatcher):
    dp.register_message_handler(coach_cmd, commands=["coach"])
