import logging
from aiogram import types, Dispatcher, Bot
from core.pnlsystem import calculate_wallet_wr
from core.database import get_wallets
from core.smartcoach import smartcoach_reply

logger = logging.getLogger(__name__)

async def coach_cmd(message: types.Message):
    Bot.set_current(message.bot)
    user_id = message.from_user.id
    args = message.get_args()

    if not args:
        await message.reply("❓ Nutze den Befehl so: /coach WALLET\n\nBeispiel: <code>/coach 7g3n...ABcd</code>", parse_mode="HTML")
        return

    wallet_id = args.strip()

    try:
        wallets = await get_wallets(user_id)
        target = next((w for w in wallets if w.get("address") == wallet_id), None)

        if not target:
            await message.reply("⚠️ Diese Wallet ist nicht in deiner Trackliste.")
            return

        # Werte holen
        wr_raw = int(target.get("wins", 0)) / max(1, (int(target.get("wins", 0)) + int(target.get("losses", 0))))
        roi = float(target.get("roi", 0.0)) if "roi" in target else None
        tp = None
        sl = None

        # SmartCoach-Antwort erzeugen
        coach_response = smartcoach_reply(wr_raw, roi=roi, tp=tp, sl=sl)

        await message.answer(f"🧠 <b>SmartCoach Analyse</b> für <code>{wallet_id}</code>:\n\n{coach_response}", parse_mode="HTML")

    except Exception as e:
        logger.exception(f"❌ Fehler bei /coach: {e}")
        await message.reply("⚠️ Fehler bei der Coach-Analyse.")
    

def register_coach_cmd(dp: Dispatcher):
    dp.register_message_handler(coach_cmd, commands=["coach"])
