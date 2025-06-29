import logging
from aiogram import types, Dispatcher, Bot
from core.buttons import get_main_menu, get_smart_finder_menu
from core.database import set_finder_mode
from core.alerts import notify_user

logger = logging.getLogger(__name__)

# 📈 Button: Add Wallet
async def handle_add_wallet(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.answer("📥 Bitte benutze den Befehl:\n`/add <WALLET> <TAG>`", parse_mode="Markdown")

# 🗑 Button: Remove Wallet
async def handle_remove_wallet(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.answer("🗑 Bitte benutze den Befehl:\n`/rm`", parse_mode="Markdown")

# 💼 Button: List Wallets
async def handle_list_wallets(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.answer("📊 Bitte benutze den Befehl:\n`/list`", parse_mode="Markdown")

# 💰 Button: Add Profit
async def handle_add_profit(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.answer("💰 Bitte benutze den Befehl:\n`/profit <WALLET> <+/-BETRAG>`", parse_mode="Markdown")

# 🛰️ Button: SmartFinder
async def handle_open_smart_finder(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.edit_text(
        "📡 <b>Smart Wallet Finder</b>\nWähle deinen Modus:",
        reply_markup=get_smart_finder_menu(),
        parse_mode="HTML"
    )

# 🔙 Button: Zurück zum Hauptmenü
async def handle_back_to_main_menu(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.edit_text(
        "🏠 Hauptmenü – wähle eine Aktion:",
        reply_markup=get_main_menu()
    )

# 🌕/⚡️/🛑 Finder-Auswahl
async def handle_finder_selection(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    selection = callback_query.data.replace("finder_", "")
    user_id = callback_query.from_user.id

    if selection == "moonbags":
        await set_finder_mode(user_id, "moonbags")
        await callback_query.message.edit_text("✅ Finder aktiviert: 🌕 Moonbags", reply_markup=get_main_menu())
    elif selection == "scalping":
        await set_finder_mode(user_id, "scalping")
        await callback_query.message.edit_text("✅ Finder aktiviert: ⚡️ Scalping Bags", reply_markup=get_main_menu())
    elif selection == "off":
        await set_finder_mode(user_id, "off")
        await callback_query.message.edit_text("🛑 Finder deaktiviert.", reply_markup=get_main_menu())

    await notify_user(user_id, f"🎯 Finder-Modus gesetzt: <b>{selection}</b>")

# 🔁 Registrierung aller Button-Handler
def register_callback_buttons(dp: Dispatcher):
    dp.register_callback_query_handler(handle_add_wallet, lambda c: c.data == "add_wallet")
    dp.register_callback_query_handler(handle_remove_wallet, lambda c: c.data == "remove_wallet")
    dp.register_callback_query_handler(handle_list_wallets, lambda c: c.data == "list_wallets")
    dp.register_callback_query_handler(handle_add_profit, lambda c: c.data == "add_profit")
    dp.register_callback_query_handler(handle_open_smart_finder, lambda c: c.data == "smartfinder_menu" or c.data == "smart_finder")
    dp.register_callback_query_handler(handle_back_to_main_menu, lambda c: c.data == "main_menu")
    dp.register_callback_query_handler(handle_finder_selection, lambda c: c.data.startswith("finder_"))
