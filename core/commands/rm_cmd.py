import logging
from aiogram import types, Bot
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_wallets, remove_wallet

logger = logging.getLogger(__name__)

# /rm Befehl – zeigt Wallets zur Auswahl an
async def remove_wallet_cmd(message: types.Message):
    try:
        Bot.set_current(message.bot)
        user_id = message.from_user.id if message.from_user else None

        if not user_id:
            await message.answer("❗️Benutzer-ID fehlt.")
            return

        wallets = await get_wallets(user_id)

        if not wallets:
            await message.answer("💤 Du hast aktuell keine Wallets zum Entfernen.")
            return

        keyboard = InlineKeyboardMarkup()
        for entry in wallets:
            tag = entry.get("tag", "❓")
            wallet_addr = entry.get("wallet") or entry.get("address") or None
            if not wallet_addr:
                continue
            display = f"{tag} - {wallet_addr[:5]}...{wallet_addr[-4:]}"
            callback_data = f"rm_{wallet_addr}"
            keyboard.add(InlineKeyboardButton(text=display, callback_data=callback_data))

        await message.answer("🗑 Wähle eine Wallet zum Entfernen:", reply_markup=keyboard)

    except Exception as e:
        logger.exception("❌ Fehler bei /rm Befehl:")
        await message.answer("⚠️ Ein Fehler ist aufgetreten beim Anzeigen deiner Wallets.")

# Callback für Entfernen einer Wallet
async def handle_rm_callback(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        user_id = callback_query.from_user.id if callback_query.from_user else None

        if not user_id:
            await callback_query.answer("❗️Benutzer-ID fehlt.", show_alert=True)
            return

        data = callback_query.data
        if not data or not data.startswith("rm_"):
            await callback_query.answer("❗️Ungültige Auswahl.", show_alert=True)
            return

        wallet = data.replace("rm_", "")
        await remove_wallet(user_id, wallet)

        await callback_query.message.edit_text(
            f"❌ Wallet `{wallet}` wurde erfolgreich entfernt.",
            parse_mode="Markdown"
        )
        logger.info(f"🗑 Wallet entfernt: {wallet} – User {user_id}")

    except Exception as e:
        logger.exception("❌ Fehler beim Entfernen der Wallet:")
        await callback_query.answer("⚠️ Fehler beim Entfernen der Wallet.", show_alert=True)

def register_rm_cmd(dp: Dispatcher):
    dp.register_message_handler(remove_wallet_cmd, commands=["rm"])
    dp.register_callback_query_handler(handle_rm_callback, lambda c: c.data and c.data.startswith("rm_"))
