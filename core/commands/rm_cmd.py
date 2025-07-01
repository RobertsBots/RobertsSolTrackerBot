import logging
from aiogram import types, Bot
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_wallets, remove_wallet
import hashlib

logger = logging.getLogger(__name__)

# Temporäres Mapping Hash → Wallet-Adresse im Speicher (kann auch DB sein)
hash_wallet_map = {}

def wallet_to_callback(wallet_addr: str) -> str:
    """Erstellt einen MD5-Hash der Wallet-Adresse als Callback-Daten."""
    return hashlib.md5(wallet_addr.encode()).hexdigest()

async def remove_wallet_cmd(message: types.Message):
    try:
        Bot.set_current(message.bot)
        user_id = message.from_user.id if message.from_user else None

        if not user_id:
            await message.answer("❗️ Benutzer-ID fehlt.")
            return

        wallets = await get_wallets(user_id)

        if not wallets:
            await message.answer("💤 Du hast aktuell keine Wallets zum Entfernen.", parse_mode="HTML")
            return

        keyboard = InlineKeyboardMarkup(row_width=1)
        hash_wallet_map.clear()  # Alte Mappings löschen

        for entry in wallets:
            tag = entry.get("tag", "❓")
            wallet_addr = entry.get("wallet") or entry.get("address") or None
            if not wallet_addr:
                continue

            hash_key = wallet_to_callback(wallet_addr)
            hash_wallet_map[hash_key] = wallet_addr

            display = f"{tag} - {wallet_addr[:5]}...{wallet_addr[-4:]}"
            callback_data = f"rm_{hash_key}"
            keyboard.add(InlineKeyboardButton(text=display, callback_data=callback_data))

        # Abbrechen-Button hinzufügen
        keyboard.add(InlineKeyboardButton("↩️ Abbrechen", callback_data="rm_cancel"))

        await message.answer(
            "🗑 <b>Wähle eine Wallet zum Entfernen:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.exception("❌ Fehler bei /rm Befehl:")
        await message.answer("⚠️ Ein Fehler ist aufgetreten beim Anzeigen deiner Wallets.", parse_mode="HTML")

async def handle_rm_callback(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        user_id = callback_query.from_user.id if callback_query.from_user else None

        if not user_id:
            await callback_query.answer("❗️ Benutzer-ID fehlt.", show_alert=True)
            return

        data = callback_query.data
        if not data:
            await callback_query.answer("❗️ Ungültige Auswahl.", show_alert=True)
            return

        if data == "rm_cancel":
            await callback_query.message.edit_text("❎ Entfernen abgebrochen.")
            await callback_query.answer()
            return

        if not data.startswith("rm_"):
            await callback_query.answer("❗️ Ungültige Auswahl.", show_alert=True)
            return

        hash_key = data.replace("rm_", "")

        wallet = hash_wallet_map.get(hash_key)
        if not wallet:
            await callback_query.answer("❗️ Wallet konnte nicht gefunden werden.", show_alert=True)
            return

        await remove_wallet(user_id, wallet)

        await callback_query.message.edit_text(
            f"❌ Wallet <code>{wallet}</code> wurde erfolgreich entfernt.",
            parse_mode="HTML"
        )
        logger.info(f"🗑 Wallet entfernt: {wallet} – User {user_id}")
        await callback_query.answer("✅ Wallet erfolgreich entfernt.")

    except Exception as e:
        logger.exception("❌ Fehler beim Entfernen der Wallet:")
        await callback_query.answer("⚠️ Fehler beim Entfernen der Wallet.", show_alert=True)

def register_rm_cmd(dp: Dispatcher):
    dp.register_message_handler(remove_wallet_cmd, commands=["rm"])
    dp.register_callback_query_handler(handle_rm_callback, lambda c: c.data and (c.data.startswith("rm_") or c.data == "rm_cancel"))
