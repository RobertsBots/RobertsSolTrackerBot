import logging
from aiogram import types, Dispatcher, Bot
from core.buttons import get_main_menu, get_smart_finder_menu
from core.database import set_finder_mode
from core.alerts import notify_user
from core.helpers import send_smartcoach_reply

logger = logging.getLogger(__name__)

# 📈 Button: Add Wallet
async def handle_add_wallet(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()
        await callback_query.message.answer(
            "📥 Bitte benutze den Befehl:\n`/add <WALLET> <TAG>`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception("❌ Fehler bei Add Wallet Button:")

# 🗑 Button: Remove Wallet
async def handle_remove_wallet(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()
        await callback_query.message.answer(
            "🗑 Bitte benutze den Befehl:\n`/rm`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception("❌ Fehler bei Remove Wallet Button:")

# 💼 Button: List Wallets
async def handle_list_wallets(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()
        await callback_query.message.answer(
            "📊 Bitte benutze den Befehl:\n`/list`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception("❌ Fehler bei List Wallets Button:")

# 💰 Button: Add Profit
async def handle_add_profit(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()
        await callback_query.message.answer(
            "💰 Bitte benutze den Befehl:\n`/profit <WALLET> <+/-BETRAG>`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception("❌ Fehler bei Add Profit Button:")

# 🛰️ Button: SmartFinder öffnen
async def handle_open_smart_finder(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()
        await callback_query.message.edit_text(
            "📡 <b>Smart Wallet Finder</b>\nWähle deinen Modus:",
            reply_markup=get_smart_finder_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.exception("❌ Fehler beim Öffnen des SmartFinder Menüs:")

# 🔙 Zurück zum Hauptmenü
async def handle_back_to_main_menu(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()
        await callback_query.message.edit_text(
            "🏠 Hauptmenü – wähle eine Aktion:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.exception("❌ Fehler beim Zurückspringen zum Hauptmenü:")

# 🌕/⚡️/🛑 Finder-Modus wählen
async def handle_finder_selection(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await callback_query.answer()

        selection = callback_query.data.replace("finder_", "")
        user_id = callback_query.from_user.id if callback_query.from_user else None

        if not user_id:
            await callback_query.answer("❗️ Benutzer-ID fehlt.", show_alert=True)
            return

        if selection == "moonbags":
            await set_finder_mode(user_id, "moonbags")
            await callback_query.message.edit_text("✅ Finder aktiviert: 🌕 Moonbags", reply_markup=get_main_menu())
        elif selection == "scalping":
            await set_finder_mode(user_id, "scalping")
            await callback_query.message.edit_text("✅ Finder aktiviert: ⚡️ Scalping Bags", reply_markup=get_main_menu())
        elif selection == "off":
            await set_finder_mode(user_id, "off")
            await callback_query.message.edit_text("🛑 Finder deaktiviert.", reply_markup=get_main_menu())
        else:
            await callback_query.answer("❗️ Ungültige Auswahl.", show_alert=True)
            return

        await notify_user(user_id, f"🎯 Finder-Modus gesetzt: <b>{selection}</b>")
        logger.info(f"📡 Finder-Modus gesetzt: {selection} – User {user_id}")

    except Exception as e:
        logger.exception("❌ Fehler bei Finder-Auswahl:")

# 🧠 SmartCoach Button
async def handle_smartcoach_reply(callback_query: types.CallbackQuery):
    try:
        Bot.set_current(callback_query.bot)
        await send_smartcoach_reply(callback_query)
    except Exception as e:
        logger.exception("❌ Fehler bei SmartCoach Analyse:")

# 🔁 Registrierung aller Buttons
def register_callback_buttons(dp: Dispatcher):
    dp.register_callback_query_handler(handle_add_wallet, lambda c: c.data == "add_wallet")
    dp.register_callback_query_handler(handle_remove_wallet, lambda c: c.data == "remove_wallet")
    dp.register_callback_query_handler(handle_list_wallets, lambda c: c.data == "list_wallets")
    dp.register_callback_query_handler(handle_add_profit, lambda c: c.data == "add_profit")
    dp.register_callback_query_handler(handle_open_smart_finder, lambda c: c.data in ["smartfinder_menu", "smart_finder"])
    dp.register_callback_query_handler(handle_back_to_main_menu, lambda c: c.data == "main_menu")
    dp.register_callback_query_handler(handle_finder_selection, lambda c: c.data.startswith("finder_"))
    dp.register_callback_query_handler(handle_smartcoach_reply, lambda c: c.data.startswith("smartcoach_reply:"))
