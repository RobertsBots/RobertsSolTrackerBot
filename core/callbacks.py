import logging
from aiogram import types, Dispatcher, Bot
from core.buttons import get_main_menu, get_smart_finder_menu

logger = logging.getLogger(__name__)


# 📈 Add Wallet
async def handle_add_wallet_button(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()  # ⬅️ wichtig zur Vermeidung von "loading..." Bug
    await callback_query.message.answer(
        "📥 Bitte benutze den Befehl:\n`/add <WALLET> <TAG>`",
        parse_mode="Markdown"
    )


# 🗑 Remove Wallet
async def handle_remove_wallet_button(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.answer(
        "🗑 Bitte nutze den Befehl `/rm`, um eine Wallet zu entfernen.",
        parse_mode="Markdown"
    )


# 💼 List Wallets
async def handle_list_wallets_button(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.answer(
        "📋 Bitte sende den Befehl `/list`, um alle Wallets zu sehen.",
        parse_mode="Markdown"
    )


# 💰 Add Profit
async def handle_add_profit_button(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.answer(
        "💰 Bitte nutze den Befehl:\n`/profit <WALLET> <+/-BETRAG>`",
        parse_mode="Markdown"
    )


# 🧠 Smart Finder → Menü
async def handle_smart_finder_button(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.edit_text(
        "📡 <b>Smart Wallet Finder</b>\nWähle deinen Modus:",
        reply_markup=get_smart_finder_menu(),
        parse_mode="HTML"
    )


# 🌕 Moonbags
async def handle_finder_moonbags(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.edit_text(
        "✅ Finder aktiviert: 🌕 Moonbags"
    )
    from core.database import set_finder_mode
    await set_finder_mode(callback_query.from_user.id, "moonbags")


# ⚡️ Scalping Bags
async def handle_finder_scalping(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.edit_text(
        "✅ Finder aktiviert: ⚡️ Scalping Bags"
    )
    from core.database import set_finder_mode
    await set_finder_mode(callback_query.from_user.id, "scalpbags")


# 🔙 Back to Main Menu
async def handle_main_menu_back(callback_query: types.CallbackQuery):
    Bot.set_current(callback_query.bot)
    await callback_query.answer()
    await callback_query.message.edit_text(
        "🔙 Hauptmenü:",
        reply_markup=get_main_menu()
    )


# Registrierung
def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(handle_add_wallet_button, lambda c: c.data == "add_wallet")
    dp.register_callback_query_handler(handle_remove_wallet_button, lambda c: c.data == "remove_wallet")
    dp.register_callback_query_handler(handle_list_wallets_button, lambda c: c.data == "list_wallets")
    dp.register_callback_query_handler(handle_add_profit_button, lambda c: c.data == "add_profit")
    dp.register_callback_query_handler(handle_smart_finder_button, lambda c: c.data == "smart_finder")

    dp.register_callback_query_handler(handle_finder_moonbags, lambda c: c.data == "finder_moonbags")
    dp.register_callback_query_handler(handle_finder_scalping, lambda c: c.data == "finder_scalping")
    dp.register_callback_query_handler(handle_main_menu_back, lambda c: c.data == "main_menu")
