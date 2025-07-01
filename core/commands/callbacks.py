# core/commands/callbacks.py

import logging
from aiogram import types, Bot
from core.smartcoach import smartcoach_reply
from core.database import get_wallets

logger = logging.getLogger(__name__)

async def handle_start_buttons_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()  # Lade-Spinner stoppen

    data = callback_query.data

    if data == "start:add_wallet":
        await callback_query.message.answer(
            "Bitte sende mir die Wallet-Adresse im Format:\n\n"
            "<code>/add WALLET TAG</code>\n\n"
            "Beispiel:\n"
            "/add 7g3n...ABcd MeineWallet",
            parse_mode="HTML"
        )
    elif data == "start:remove_wallet":
        await callback_query.message.answer(
            "Nutze <code>/rm</code>, um eine Wallet zu entfernen.",
            parse_mode="HTML"
        )
    elif data == "start:list_wallets":
        await callback_query.message.answer(
            "Nutze <code>/list</code>, um deine getrackten Wallets anzuzeigen.",
            parse_mode="HTML"
        )
    elif data == "start:add_profit":
        await callback_query.message.answer(
            "Nutze <code>/profit WALLET +10</code>, um Profit oder Verlust einzutragen.",
            parse_mode="HTML"
        )
    elif data == "start:finder_on":
        await callback_query.message.answer(
            "SmartFinder wird gestartet! Nutze /finder für Einstellungen.",
            parse_mode="HTML"
        )
    elif data == "start:finder_off":
        await callback_query.message.answer(
            "SmartFinder wird gestoppt! Nutze /finder für Einstellungen.",
            parse_mode="HTML"
        )
    elif data == "start:coach":
        await callback_query.message.answer(
            "Nutze <code>/coach WALLET</code>, um eine SmartCoach-Analyse zu erhalten.",
            parse_mode="HTML"
        )
    elif data == "start:backup":
        await callback_query.message.answer(
            "Backup-Funktion ist noch in Arbeit.",
            parse_mode="HTML"
        )
    else:
        await callback_query.answer("Unbekannte Aktion.", show_alert=True)


async def handle_smartcoach_reply(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()

        parts = callback_query.data.split(":", 1)
        if len(parts) < 2:
            await callback_query.message.answer("⚠️ Ungültige Callback-Daten.")
            return
        address = parts[1]
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

def register_callback_buttons(dp):
    dp.register_callback_query_handler(handle_start_buttons_callback, lambda c: c.data and c.data.startswith("start:"))
    dp.register_callback_query_handler(handle_smartcoach_reply, lambda c: c.data and c.data.startswith("smartcoach_reply:"))
