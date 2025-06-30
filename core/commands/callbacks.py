# 🧠 SmartCoach Button
from core.smartcoach import smartcoach_reply
from core.database import get_wallets

async def handle_smartcoach_reply(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()

        address = callback_query.data.split(":", 1)[1]
        user_id = callback_query.from_user.id

        wallets = await get_wallets(user_id)
        wallet = next((w for w in wallets if w.get("address") == address), None)

        if not wallet:
            await callback_query.message.answer("❌ Wallet nicht gefunden.")
            return

        wins = int(wallet.get("wins", 0) or 0)
        losses = int(wallet.get("losses", 0) or 0)
        roi = float(wallet.get("roi", 0) or 0)
        total = wins + losses
        wr = (wins / total) if total > 0 else 0.0

        response = smartcoach_reply(wr, roi=roi)
        await callback_query.message.answer(f"🧠 <b>SmartCoach:</b>\n{response}", parse_mode="HTML")

    except Exception as e:
        logger.exception("❌ Fehler bei SmartCoach Analyse:")
        await callback_query.message.answer("⚠️ Fehler bei SmartCoach-Analyse.")
